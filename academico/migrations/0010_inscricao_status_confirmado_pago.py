from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0009_alter_relatoriosdashboard_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inscricao',
            name='status',
            field=models.CharField(
                max_length=12,
                choices=[
                    ('PENDENTE',   'Pendente'),
                    ('CONFIRMADO', 'Dados Confirmados'),
                    ('PAGO',       'Pagamento Validado'),
                    ('APROVADO',   'Aprovado'),
                    ('REJEITADO',  'Rejeitado'),
                ],
                default='PENDENTE',
            ),
        ),
    ]
