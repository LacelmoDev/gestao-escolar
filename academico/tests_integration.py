import io
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from academico.models import Inscricao, Curso
from academico import utils as academico_utils


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
