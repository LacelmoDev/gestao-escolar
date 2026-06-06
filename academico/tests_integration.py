import io
from unittest.mock import patch

from django.test import TestCase, Client, override_settings, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import admin, messages
from django.contrib.messages.storage.fallback import FallbackStorage

from academico.models import Inscricao, Curso, ConfirmacaoMatricula, Aluno
from academico import utils as academico_utils
from academico.admin import ConfirmacaoMatriculaAdmin, AlunoAdmin
from django.utils import timezone
from usuarios.models import Usuario
from escola.models import Turma, Disciplina, Professor, Atribuicao


@override_settings(
    CLOUDINARY_STORAGE={'CLOUD_NAME': 'doc900v91', 'API_KEY': 'test', 'API_SECRET': 'test'},
    STORAGES={
        'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class IntegrationCloudinaryTest(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')
        # Ensure there is at least one Curso
        if not Curso.objects.exists():
            Curso.objects.create(nome='Curso Teste')
        self.curso = Curso.objects.first()

    @patch('cloudinary.uploader.upload')
    @patch('academico.utils._enviar_email_async')
    @patch('django.core.mail.send_mail')
    def test_inscricao_uploads_and_email(self, mock_send_mail, mock_async, mock_upload):
        # Simula resposta do Cloudinary e faz o envio de email síncrono para o teste
        mock_upload.return_value = {'secure_url': 'https://res.cloudinary.com/demo/image/upload/v1/test.jpg', 'public_id': 'demo/test'}

        mock_async.side_effect = lambda subject, message, from_email, recipient_list, html_message=None: mock_send_mail(subject, message, from_email, recipient_list, html_message=html_message)

        img = SimpleUploadedFile('foto.jpg', b'\x89PNG\r\n\x1a\n' + b'0' * 512, content_type='image/png')
        pdf = SimpleUploadedFile('cert.pdf', b'%PDF-1.4\n%test', content_type='application/pdf')

        inscr = Inscricao(
            nome_completo='Teste Integracao',
            data_nascimento='2005-01-01',
            genero='M',
            bi_numero='INT123456',
            telefone='999999999',
            email='integ@example.com',
            curso_pretendido=self.curso,
            classe_pretendida='10',
        )
        inscr.foto_tipo_passe = img
        inscr.bi_frente = img
        inscr.bi_verso = img
        inscr.certificado_anterior = pdf
        inscr.save()

        # Verifica que a inscrição foi criada
        inscricao = Inscricao.objects.filter(bi_numero='INT123456').first()
        self.assertIsNotNone(inscricao)

        self.assertGreaterEqual(mock_upload.call_count, 3)

        # Envio de email deve ter sido acionado (via fake_async -> send_mail)
        # Disparar manualmente o envio que ocorreria na view
        academico_utils.enviar_email_inscricao_recebida(inscr)
        self.assertTrue(mock_send_mail.called)

    @patch('academico.utils._enviar_email_async')
    @patch('django.core.mail.send_mail')
    def test_enviar_email_utils(self, mock_send_mail, mock_async):
        # Substitui _enviar_email_async para chamar send_mail diretamente (sincrono)
        mock_async.side_effect = lambda subject, message, from_email, recipient_list, html_message=None: mock_send_mail(subject, message, from_email, recipient_list, html_message=html_message)

        # Cria inscrição e chama utilitário para garantir que send_mail é usado
        inscr = Inscricao.objects.create(
            nome_completo='Email Test',
            data_nascimento='2005-01-01',
            genero='F',
            bi_numero='EMAIL000',
            telefone='999999999',
            email='emailtest@example.com',
            curso_pretendido=self.curso,
            classe_pretendida='10',
        )

        academico_utils.enviar_email_inscricao_recebida(inscr)
        self.assertTrue(mock_send_mail.called)

    @patch('cloudinary.uploader.upload')
    @patch('academico.views_confirmacao._enviar_email_async')
    def test_fluxo_completo_congelamento_confirmacao_e_descongelamento(self, mock_send, mock_upload):
        mock_upload.return_value = {'secure_url': 'https://res.cloudinary.com/demo/image/upload/v1/test.jpg', 'public_id': 'demo/test'}
        hoje = timezone.now().year
        curso = self.curso

        turma_2026 = Turma.objects.create(
            nome='10A',
            classe='10',
            turno='MANHA',
            curso=curso,
            ano_letivo=hoje,
            vagas=40,
        )
        turma_2027 = Turma.objects.create(
            nome='11A',
            classe='11',
            turno='MANHA',
            curso=curso,
            ano_letivo=hoje + 1,
            vagas=40,
        )

        usuario = Usuario.objects.create_user(
            username='fictuser',
            password='testpass',
            first_name='Fict',
            last_name='Aluno',
            email='fict@example.com',
            bi_numero='FICT001',
        )
        usuario.is_aluno = True
        usuario.save()

        aluno = Aluno.objects.create(
            usuario=usuario,
            numero_processo=f'{hoje}/001',
            turma=turma_2026,
            esta_congelado=True,
        )

        login_ok = self.client.login(username='fictuser', password='testpass')
        self.assertTrue(login_ok)

        dashboard_resp = self.client.get('/dashboard/')
        self.assertEqual(dashboard_resp.status_code, 302)
        self.assertIn('/acesso-congelado/', dashboard_resp.url)

        self.client.logout()

        img = SimpleUploadedFile('foto.jpg', b'\x89PNG\r\n\x1a\n' + b'0' * 512, content_type='image/png')
        response = self.client.post('/confirmacao-matricula/', {
            'nome_completo': 'Fict Aluno',
            'bi_numero': 'FICT001',
            'email': 'fict@example.com',
            'classe_atual': '10',
            'foto_rosto': img,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmação Recebida!')

        confirmacao = ConfirmacaoMatricula.objects.filter(bi_numero='FICT001', ano_letivo=hoje + 1).first()
        self.assertIsNotNone(confirmacao)
        self.assertEqual(confirmacao.aluno, aluno)
        self.assertEqual(confirmacao.classe_nova, '11')
        self.assertEqual(confirmacao.status, 'EM_REVISAO')

        request = RequestFactory().get('/')
        request.user = usuario
        request.session = self.client.session
        messages_storage = FallbackStorage(request)
        setattr(request, '_messages', messages_storage)

        admin_action = ConfirmacaoMatriculaAdmin(ConfirmacaoMatricula, admin.site)
        admin_action.aprovar_confirmacao(request, ConfirmacaoMatricula.objects.filter(pk=confirmacao.pk))

        confirmacao.refresh_from_db()
        aluno.refresh_from_db()

        self.assertEqual(confirmacao.status, 'ATIVO')
        self.assertFalse(aluno.esta_congelado)
        self.assertEqual(aluno.turma, turma_2027)

        login_ok = self.client.login(username='fictuser', password='testpass')
        self.assertTrue(login_ok)

        dashboard_resp = self.client.get('/dashboard/')
        self.assertEqual(dashboard_resp.status_code, 200)

    def test_exportar_relatorios_admin_e_professor(self):
        admin_user = Usuario.objects.create_user(
            username='adminuser',
            password='adminpass',
            email='admin@example.com',
        )
        admin_user.is_staff = True
        admin_user.save()

        login_ok = self.client.login(username='adminuser', password='adminpass')
        self.assertTrue(login_ok)

        resp_xlsx = self.client.get('/relatorios/exportar/excel/?ano=2026')
        self.assertEqual(resp_xlsx.status_code, 200)
        self.assertEqual(resp_xlsx['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        resp_pdf = self.client.get('/relatorios/exportar/pdf/?ano=2026')
        self.assertEqual(resp_pdf.status_code, 200)
        self.assertEqual(resp_pdf['Content-Type'], 'application/pdf')

        self.client.logout()

        professor_user = Usuario.objects.create_user(
            username='profuser',
            password='profpass',
            email='prof@example.com',
        )
        professor_user.is_professor = True
        professor_user.save()

        professor = Professor.objects.create(usuario=professor_user)
        disciplina = Disciplina.objects.create(nome='Matemática')
        turma_long = Turma.objects.create(
            nome='Turma Longa ' + 'A' * 30,
            classe='10',
            turno='MANHA',
            curso=self.curso,
            ano_letivo=2026,
            vagas=30,
        )
        Atribuicao.objects.create(professor=professor, disciplina=disciplina, turma=turma_long)

        aluno_usuario = Usuario.objects.create_user(
            username='aluno123',
            password='testpass',
            email='aluno123@example.com',
        )
        aluno_usuario.is_aluno = True
        aluno_usuario.save()
        Aluno.objects.create(
            usuario=aluno_usuario,
            numero_processo='2026/123',
            turma=turma_long,
        )

        login_ok = self.client.login(username='profuser', password='profpass')
        self.assertTrue(login_ok)

        resp_turma_xlsx = self.client.get(f'/professor/turma/{turma_long.id}/relatorio/excel/')
        self.assertEqual(resp_turma_xlsx.status_code, 200)
        self.assertEqual(resp_turma_xlsx['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        resp_turma_pdf = self.client.get(f'/professor/turma/{turma_long.id}/relatorio/pdf/')
        self.assertEqual(resp_turma_pdf.status_code, 200)
        self.assertEqual(resp_turma_pdf['Content-Type'], 'application/pdf')

    def test_admin_actions_congelar_e_descongelar_alunos(self):
        admin_user = Usuario.objects.create_user(
            username='staffuser',
            password='staffpass',
            email='staff@example.com',
            is_staff=True,
        )
        admin_user.save()

        aluno1_user = Usuario.objects.create_user(
            username='aluno001',
            password='testpass',
            email='aluno001@example.com',
        )
        aluno1_user.is_aluno = True
        aluno1_user.save()
        aluno1 = Aluno.objects.create(
            usuario=aluno1_user,
            numero_processo='2026/001',
            esta_congelado=False,
        )

        aluno2_user = Usuario.objects.create_user(
            username='aluno002',
            password='testpass',
            email='aluno002@example.com',
        )
        aluno2_user.is_aluno = True
        aluno2_user.save()
        aluno2 = Aluno.objects.create(
            usuario=aluno2_user,
            numero_processo='2026/002',
            esta_congelado=False,
        )

        request = RequestFactory().get('/')
        request.user = admin_user
        request.session = self.client.session
        messages_storage = FallbackStorage(request)
        setattr(request, '_messages', messages_storage)

        aluno_admin = AlunoAdmin(Aluno, admin.site)

        aluno_admin.congelar_alunos(request, Aluno.objects.filter(pk__in=[aluno1.pk, aluno2.pk]))
        aluno1.refresh_from_db()
        aluno2.refresh_from_db()
        self.assertTrue(aluno1.esta_congelado)
        self.assertTrue(aluno2.esta_congelado)

        aluno_admin.descongelar_alunos(request, Aluno.objects.filter(pk__in=[aluno1.pk, aluno2.pk]))
        aluno1.refresh_from_db()
        aluno2.refresh_from_db()
        self.assertFalse(aluno1.esta_congelado)
        self.assertFalse(aluno2.esta_congelado)
