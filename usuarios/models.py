from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    is_aluno = models.BooleanField(default=False)
    is_professor = models.BooleanField(default=False)
    is_admin_escola = models.BooleanField(default=False)
    bi_numero = models.CharField(max_length=20, unique=True, blank=True, null=True)