from django.db import models
from decimal import Decimal
from usuarios.models import Usuario
from escola.models import Curso, Turma, Disciplina


class Inscricao(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE',    'Pendente'),
        ('CONFIRMADO',  'Dados Confirmados'),  
        ('PAGO',        'Pagamento Validado'),   
        ('APROVADO',    'Aprovado'),
        ('REJEITADO',   'Rejeitado'),
    )
    nome_completo       = models.CharField('Nome Completo', max_length=255)
    data_nascimento     = models.DateField('Data de Nascimento')
    genero              = models.CharField('Género', max_length=10, choices=(('M', 'Masculino'), ('F', 'Feminino')))
    bi_numero           = models.CharField('Número do B.I.', max_length=20, unique=True)
    telefone            = models.CharField('Telefone / WhatsApp', max_length=20)
    email               = models.EmailField('E-mail', blank=True, null=True)
    curso_pretendido    = models.ForeignKey(Curso, on_delete=models.PROTECT, verbose_name='Curso')
    classe_pretendida   = models.CharField('Classe', max_length=3, choices=Turma.CLASSES_CHOICES)
    foto_tipo_passe     = models.ImageField('Foto Tipo Passe', upload_to='tarimba/inscricoes/fotos/')
    bi_frente           = models.ImageField('B.I. Frente', upload_to='tarimba/inscricoes/documentos/')
    bi_verso            = models.ImageField('B.I. Verso', upload_to='tarimba/inscricoes/documentos/')
    certificado_anterior    = models.FileField('Certificado de Habilitações', upload_to='tarimba/inscricoes/documentos/')
    comprovativo_pagamento  = models.ImageField(
        'Comprovativo de Pagamento',
        upload_to='tarimba/inscricoes/pagamentos/',
        blank=True,
        null=True,
    )
    status              = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDENTE')
    observacoes_adm     = models.TextField('Observações', blank=True, null=True)
    data_submissao      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"

    def __str__(self):
        return f"{self.nome_completo} - {self.bi_numero}"


class Aluno(models.Model):
    usuario         = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_aluno')
    turma           = models.ForeignKey(Turma, on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos')
    numero_processo = models.CharField('Nº de Processo', max_length=20, unique=True)
    esta_congelado  = models.BooleanField('Matrícula Congelada', default=False)
    data_matricula  = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"

    def __str__(self):
        nome = self.usuario.get_full_name() or self.usuario.username
        return f"{nome} (Proc: {self.numero_processo})"


class Nota(models.Model):
    TRIMESTRES = ((1, '1º Trimestre'), (2, '2º Trimestre'), (3, '3º Trimestre'))
    aluno       = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='notas')
    disciplina  = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    trimestre   = models.IntegerField(choices=TRIMESTRES)
    mac         = models.DecimalField('MAC', max_digits=4, decimal_places=2, default=0)
    npp         = models.DecimalField('NPP', max_digits=4, decimal_places=2, default=0)
    npt         = models.DecimalField('NPT', max_digits=4, decimal_places=2, default=0)
    exame       = models.DecimalField('Exame/Recurso', max_digits=4, decimal_places=2, blank=True, null=True)

    @property
    def media_trimestral(self):
        soma = self.mac + self.npp + self.npt
        return (soma / Decimal('3')).quantize(Decimal('0.1'))


class Presenca(models.Model):
    aluno                   = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='presencas')
    disciplina              = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    data                    = models.DateField()
    esta_presente           = models.BooleanField('Presente', default=True)
    justificada             = models.BooleanField('Falta Justificada', default=False)
    documento_justificativo = models.FileField(upload_to='tarimba/justificativas/', blank=True, null=True)
    observacao_justificativa = models.TextField('Nota do Aluno', blank=True, null=True)

    def __str__(self):
        status = "P" if self.esta_presente else "F"
        return f"{self.aluno.usuario.username} - {self.data} [{status}]"


class RelatoriosDashboard(models.Model):
    class Meta:
        verbose_name_plural = "📊 Ver Relatórios e Estatísticas"
        managed = False
        app_label = "academico"
