"""
Configuração ASGI para o sistema EMC Soldas.
"""
import os
from django.core.asgi import get_asgi_application

# Suporte ao PyMySQL
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
