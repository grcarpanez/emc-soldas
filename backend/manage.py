#!/usr/bin/env python
"""Utilitário de linha de comando do Django para o sistema EMC Soldas."""
import os
import sys

# Suporte ao PyMySQL como driver nativo do MySQL
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass


def main():
    """Executa tarefas administrativas."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Verifique se ele está instalado "
            "e disponível no seu ambiente virtual Python."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
