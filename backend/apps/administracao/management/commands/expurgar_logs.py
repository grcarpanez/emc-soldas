"""
Comando de gerenciamento do Django para rotina agendada de expurgo de logs (TTL)
com suporte a envio de backup por e-mail dos arquivos expirados antes da exclusão física.
Uso:
  python manage.py expurgar_logs
  python manage.py expurgar_logs --enviar-backup
  python manage.py expurgar_logs --sem-backup
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.administracao.services import expurgar_arquivos_log, sincronizar_manifesto_logs


class Command(BaseCommand):
    help = "Executa a rotina de expurgo de arquivos físicos de log por decurso de prazo (TTL), com envio opcional de backup por e-mail."

    def add_arguments(self, parser):
        parser.add_argument(
            '--enviar-backup',
            action='store_true',
            dest='enviar_backup',
            default=True,
            help='Envia backup por e-mail com os arquivos .log em anexo antes do expurgo (padrão: True).'
        )
        parser.add_argument(
            '--sem-backup',
            action='store_false',
            dest='enviar_backup',
            help='Executa o expurgo físico diretamente sem enviar e-mail de backup.'
        )

    def handle(self, *args, **options):
        enviar_backup = options.get('enviar_backup', True)
        self.stdout.write("Iniciando sincronizacao do manifesto de logs do servidor...")
        sinc_res = sincronizar_manifesto_logs()
        self.stdout.write(f"[OK] Sincronizacao concluida: {sinc_res.get('novos_indexados', 0)} novo(s) arquivo(s) indexado(s).")

        self.stdout.write("Verificando arquivos com data de expurgo atingida...")
        resultado = expurgar_arquivos_log(enviar_email_backup=enviar_backup)

        if resultado.get('sucesso'):
            total = resultado.get('total_expurgados', 0)
            if total > 0:
                self.stdout.write(self.style.SUCCESS(f"[OK] {total} arquivo(s) de log expurgado(s) com sucesso: {', '.join(resultado.get('arquivos', []))}"))
                if resultado.get('email_backup_enviado'):
                    self.stdout.write(self.style.SUCCESS("[OK] E-mail de backup com os arquivos expirados foi disparado com sucesso."))
            else:
                self.stdout.write("[OK] Nenhum arquivo de log atingiu a data de expurgo hoje.")
        else:
            self.stdout.write(self.style.ERROR(f"[ERRO] Falha no expurgo de logs: {resultado.get('erro', 'Erro desconhecido')}"))
