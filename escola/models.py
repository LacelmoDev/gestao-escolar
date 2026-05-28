from django.db import models
from usuarios.models import Usuario 

class Curso(models.Model):
    TIPOS_ENSINO = (
        ('PRIMARIO', 'Ensino Primário'),
        ('I_CICLO', 'I Ciclo'),
        ('GERAL', 'Ensino Geral (II Ciclo)'),
        ('TECNICO', 'Ensino Técnico-Profissional'),
    )

    nome = models.CharField('Nome do Curso', max_length=100)
    tipo = models.CharField('Tipo de Ensino', max_length=10, choices=TIPOS_ENSINO)
    tem_prova_semestral = models.BooleanField('Tem Prova Semestral?', default=False)

    def save(self, *args, **kwargs):
        if self.tipo == 'TECNICO':
            self.tem_prova_semestral = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    obrigatoria = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class GradeCurricular(models.Model):
    CLASSES_CHOICES = (
        ('INI', 'Iniciação'), ('1', '1ª Classe'), ('2', '2ª Classe'), 
        ('3', '3ª Classe'), ('4', '4ª Classe'), ('5', '5ª Classe'), 
        ('6', '6ª Classe'), ('7', '7ª Classe'), ('8', '8ª Classe'), 
        ('9', '9ª Classe'), ('10', '10ª Classe'), ('11', '11ª Classe'), 
        ('12', '12ª Classe'), ('13', '13ª Classe'),
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='grades')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    classe = models.CharField(max_length=3, choices=CLASSES_CHOICES)

    class Meta:
        verbose_name = "Grade Curricular"
        verbose_name_plural = "Grades Curriculares"
        unique_together = ('curso', 'disciplina', 'classe')

    def __str__(self):
        return f"{self.curso.nome} - {self.get_classe_display()} - {self.disciplina.nome}"

class Turma(models.Model):
    CLASSES_CHOICES = (
        ('INI', 'Iniciação'), ('1', '1ª Classe'), ('2', '2ª Classe'),
        ('3', '3ª Classe'), ('4', '4ª Classe'), ('5', '5ª Classe'),
        ('6', '6ª Classe'), ('7', '7ª Classe'), ('8', '8ª Classe'),
        ('9', '9ª Classe'), ('10', '10ª Classe'), ('11', '11ª Classe'),
        ('12', '12ª Classe'), ('13', '13ª Classe'),
    )
    TURNOS = (('MANHA', 'Manhã'), ('TARDE', 'Tarde'), ('NOITE', 'Noite'))

    nome = models.CharField(max_length=50)
    classe = models.CharField(max_length=3, choices=CLASSES_CHOICES, default='10')
    turno = models.CharField(max_length=10, choices=TURNOS)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    ano_letivo = models.IntegerField(default=2026)
    vagas = models.PositiveIntegerField(default=45)

    def __str__(self):
        return f"{self.get_classe_display()} {self.nome} - {self.curso.nome}"

    @property
    def listar_disciplinas(self):
        return Disciplina.objects.filter(gradecurricular__curso=self.curso, gradecurricular__classe=self.classe)

class Professor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_professor')
    especialidade = models.CharField(max_length=100, blank=True)
    disciplinas_habilitadas = models.ManyToManyField(Disciplina, related_name='professores_habilitados')

    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professores"

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

class Atribuicao(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='minhas_atribuicoes')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='grade_curricular')

    class Meta:
        verbose_name = "Atribuição de Aula"
        verbose_name_plural = "Atribuições de Aulas"
        unique_together = ('disciplina', 'turma')

    def __str__(self):
        return f"{self.professor} -> {self.disciplina} ({self.turma})"