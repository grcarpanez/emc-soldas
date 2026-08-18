"""
Configurações do Django para o sistema EMC Soldas.
Desenvolvido com base no FSD (Documento de Especificação Funcional).
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

# Suporte ao PyMySQL como driver nativo do MySQL e compatibilidade com XAMPP (MariaDB 10.4.x)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    
    # Compatibilidade do Django 5.x com MariaDB 10.4 do XAMPP
    from django.db.backends.mysql.base import DatabaseWrapper
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseWrapper.check_database_version_supported = lambda self: None
    DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
    DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)
except ImportError:
    pass

# Caminho base do Backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Adiciona o diretório backend ao sys.path para importação direta de apps e core
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Chaves Criptográficas (Lidas de os.environ em produção, com fallback seguro para dev local)
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-emc-soldas-dev-key-industrial-integrity-2026-secure-token-998877'
)

ENCRYPTION_KEY = os.environ.get(
    'ENCRYPTION_KEY',
    'emc_soldas_aes256_master_key_local_dev_only_32_bytes_len='
)

# Modo de Depuração
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Hosts Permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Definição das Aplicações Instaladas
INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Bibliotecas Terceirizadas
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Núcleo do Sistema
    'core',

    # Módulos Funcionais do Sistema (Apps)
    'apps.authentication.apps.AuthenticationConfig',
    'apps.cadastros.apps.CadastrosConfig',
    'apps.catalogo.apps.CatalogoConfig',
    'apps.compras.apps.ComprasConfig',
    'apps.orcamentos.apps.OrcamentosConfig',
    'apps.faturamento.apps.FaturamentoConfig',
    'apps.financeiro.apps.FinanceiroConfig',
    'apps.conciliacao.apps.ConciliacaoConfig',
    'apps.administracao.apps.AdministracaoConfig',
    'apps.relatorios.apps.RelatoriosConfig',
]

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middlewares Customizados do EMC Soldas
    'core.middleware.AuditUserMiddleware',
    'core.middleware.SecurityLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'frontend'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Configuração do Banco de Dados (MySQL InnoDB conforme FSD)
DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.mysql')
DB_NAME = os.environ.get('DB_NAME', 'emc_soldas')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '3306')

IS_TESTING = 'test' in sys.argv

if IS_TESTING and os.environ.get('USE_SQLITE_TESTS', 'True').lower() in ('true', '1'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            } if 'mysql' in DB_ENGINE else {},
        }
    }

# Modelo de Usuário Customizado (se configurado futuramente na Fase 2)
# AUTH_USER_MODEL = 'authentication.Usuario'

# Validação de Senhas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos e Mídia
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR.parent / 'frontend']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Tipo Padrão de Chave Primária
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework (DRF)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.authentication.authentication.CookieJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '100/minute',
        'heavy_reports': '5/minute',
    },
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

# Configuração do SimpleJWT (Sessão Segura HttpOnly)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'emc_access_token',
    'AUTH_COOKIE_REFRESH': 'emc_refresh_token',
    'AUTH_COOKIE_DOMAIN': None,
    'AUTH_COOKIE_SECURE': not DEBUG,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Strict',
}

# Configurações de CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500'
).split(',')

# Configurações de CSRF
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = False  # Permite ao frontend ler o token CSRF para envio no cabeçalho X-CSRFToken
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:5500',
    'http://127.0.0.1:5500',
]

# Configuração de E-mail (com Fallback Seguro para Console em Desenvolvimento)
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'EMC Soldas <nao-responda@emcsoldas.com.br>'

# Diretório de Logs Físicos e Configuração de Logging com Rotação Diária
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] [{levelname}] [{name}:{lineno}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_daily': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOGS_DIR / 'app.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_daily'],
            'level': 'INFO',
            'propagate': True,
        },
        'emc_soldas': {
            'handlers': ['console', 'file_daily'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'audit': {
            'handlers': ['console', 'file_daily'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
