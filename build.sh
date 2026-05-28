#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
# CRIAÇÃO DO SUPERUSER CORRIGIDA:
python -c "

import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Ajuste 'core' se a sua pasta de configurações tiver outro nome
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@escola.com', 'Grupo3')
    print('Superuser criado com sucesso!')
"
