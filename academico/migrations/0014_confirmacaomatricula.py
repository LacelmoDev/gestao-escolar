from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0013_notificacao'),
        ('escola', '0007_remove_disciplina_cursos_gradecurricular'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmacaoMatricula',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano_letivo', models.IntegerField(verbose_name='Ano Lectivo')),
                ('foto_rosto', models.ImageField(upload_to='tarimba/confirmacoes/fotos/', verbose_name='Foto de Rosto')),
                ('bi_numero', models.CharField(max_length=20, verbose_name='Número do B.I.')),
                ('email', models.EmailField(verbose_name='E-mail de Contacto')),
                ('classe_nova', models.CharField(
                    choices=[('INI','Iniciação'),('1','1ª Classe'),('2','2ª Classe'),
                             ('3','3ª Classe'),('4','4ª Classe'),('5','5ª Classe'),
                             ('6','6ª Classe'),('7','7ª Classe'),('8','8ª Classe'),
                             ('9','9ª Classe'),('10','10ª Classe'),('11','11ª Classe'),
                             ('12','12ª Classe'),('13','13ª Classe')],
                    max_length=3, verbose_name='Nova Classe'
                )),
                ('status', models.CharField(
                    choices=[('EM_REVISAO','Em Revisão'),
                             ('AGUARDANDO_PAGAMENTO','Aguardando Pagamento'),
                             ('ATIVO','Ativo'),('REJEITADO','Rejeitado')],
                    default='EM_REVISAO', max_length=25
                )),
                ('motivo_rejeicao', models.TextField(blank=True, null=True, verbose_name='Motivo de Rejeição')),
                ('data_submissao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('aluno', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='confirmacoes', to='academico.aluno', verbose_name='Aluno'
                )),
                ('curso_novo', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    to='escola.curso', verbose_name='Novo Curso'
                )),
            ],
            options={
                'verbose_name': 'Confirmação de Matrícula',
                'verbose_name_plural': 'Confirmações de Matrícula',
                'ordering': ['-data_submissao'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='confirmacaomatricula',
            unique_together={('aluno', 'ano_letivo')},
        ),
    ]
