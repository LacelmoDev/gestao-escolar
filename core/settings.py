import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv
import environ

# Inicialização do ambiente
env = environ.Env()
environ.Env.read_env()
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-*24vx##!_h55l958a_#-$lc550@@4nw_)46#(rlqde9u4*!nnx')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Ler hosts de variáveis de ambiente com fallbacks sensatos
def _parse_hosts_list(env_var, default_list):
    """Parse comma-separated hosts from environment variable."""
    val = os.environ.get(env_var)
    if val:
        return [h.strip() for h in val.split(',') if h.strip()]
    return default_list

ALLOWED_HOSTS = _parse_hosts_list(
    'ALLOWED_HOSTS',
    ['localhost', '127.0.0.1', 'tarimba.onrender.com', '.onrender.com']
)

# CSRF_TRUSTED_ORIGINS deve incluir esquema (https://)
# Ex: "https://tarimba.onrender.com,https://outro.onrender.com"
CSRF_TRUSTED_ORIGINS = _parse_hosts_list(
    'CSRF_TRUSTED_ORIGINS',
    ['https://tarimba.onrender.com', 'https://localhost:8000']
)

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',        # Deve vir antes do staticfiles
    'django.contrib.staticfiles',    
    'cloudinary',
    'csp',
    'usuarios',
    'escola',
    'academico',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Essencial para estáticos em produção
    'academico.middleware.CSRFDebugMiddleware',  # Debug CSRF antes da validação
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware', 
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

ENV = os.getenv("ENV", "local")

if ENV == "production":
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'usuarios.Usuario'

# --- INTERNACIONALIZAÇÃO ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'Africa/Luanda'
USE_I18N = True
USE_TZ = True

# --- ARQUIVOS ESTÁTICOS E MÍDIA ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True

# Tornar uso do Cloudinary opcional: se faltar API secret, usar armazenamento
# local (FileSystemStorage) para evitar erros em tempo de execução.
CLOUDINARY_API_SECRET = os.environ.get('API_SECRET_DO_CLOUDINARY') or os.environ.get('CLOUDINARY_API_SECRET')

if ENV == 'production':
    if not CLOUDINARY_API_SECRET:
        raise RuntimeError("CLOUDINARY API secret is required in production. Set API_SECRET_DO_CLOUDINARY in environment variables.")

    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

    # Configurações do Cloudinary
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUD_NAME_DO_CLOUDINARY'),
        'API_KEY': os.environ.get('API_KEY_DO_CLOUDINARY'),
        'API_SECRET': CLOUDINARY_API_SECRET,
    }
else:
    # Em ambiente local/de desenvolvimento, usa fallback para armazenamento local
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    # Define CLOUDINARY_STORAGE mesmo em dev para evitar que o pacote falhe ao
    # recarregar configurações durante os testes. Valores podem ficar vazios.
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUD_NAME_DO_CLOUDINARY', ''),
        'API_KEY': os.environ.get('API_KEY_DO_CLOUDINARY', ''),
        'API_SECRET': os.environ.get('API_SECRET_DO_CLOUDINARY', ''),
    }

# --- EMAIL ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=f'Colégio Tarimba <{EMAIL_HOST_USER}>')

# --- SEGURANÇA DE COOKIES E SESSÃO ---
# Em produção: usar cookies seguros + HTTPS redirect
# Em desenvolvimento: desativar para permitir testes locais
if ENV == 'production':
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False
else:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# SameSite policy para melhor segurança CSRF
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# --- OUTROS ---
LOGIN_REDIRECT_URL = 'verificar_perfil'
LOGOUT_REDIRECT_URL = 'home'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
APPEND_SLASH = True

# --- LOGGING ---
# Configurar logging para capturar detalhes de CSRF em produção
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'academico.views': {
            'handlers': ['console'],
            'level': 'DEBUG' if ENV == 'production' else 'DEBUG',
            'propagate': False,
        },
        'academico.middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
