import os
import datetime
import logging


class DailyDateFileHandler(logging.FileHandler):
    """
    Handler de Log que grava diretamente no arquivo correspondente ao dia atual
    no formato imutável app-YYYY-MM-DD.log.
    
    Vantagens:
    - Desacopla o peso textual do banco de dados (conforme docs/FSD.md - Seção 19).
    - Elimina completamente erros de bloqueio de arquivo no Windows (PermissionError WinError 32).
    - Mantém sincronismo 1:1 perfeito com a tabela de manifesto ControleArquivoLog.
    """

    def __init__(self, dir_path: str, prefix: str = 'app-', suffix: str = '.log', encoding: str = 'utf-8'):
        self.dir_path = str(dir_path)
        self.prefix = prefix
        self.suffix = suffix
        self.encoding = encoding
        os.makedirs(self.dir_path, exist_ok=True)
        self.current_date = datetime.date.today()
        filename = self._get_filename_for_date(self.current_date)
        super().__init__(filename, mode='a', encoding=encoding)

    def _get_filename_for_date(self, dt: datetime.date) -> str:
        return os.path.join(self.dir_path, f"{self.prefix}{dt.strftime('%Y-%m-%d')}{self.suffix}")

    def emit(self, record):
        now_date = datetime.date.today()
        if now_date != self.current_date:
            self.current_date = now_date
            new_filename = self._get_filename_for_date(now_date)
            if self.stream:
                try:
                    self.stream.flush()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            self.baseFilename = os.path.abspath(new_filename)
            self.stream = self._open()
        super().emit(record)
