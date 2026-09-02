import logging
import os
import sys
import traceback

from datetime import datetime

import caminhos

PASTA_LOGS = os.path.join(caminhos.diretorio_dados(), "logs")


def configurar_logging():
    """Configura o logging em arquivo e retorna o logger raiz do app."""
    os.makedirs(PASTA_LOGS, exist_ok=True)
    nome = datetime.now().strftime("app_%Y%m%d.log")
    caminho = os.path.join(PASTA_LOGS, nome)

    logger = logging.getLogger("CalculadoraIMC")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(caminho, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    return logger


def _log_excecao_nao_tratada(exc_type, exc_value, exc_traceback):
    """Registra exceções não capturadas em log e as repassa ao handler padrão."""
    logger = logging.getLogger("CalculadoraIMC")
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    detalhes = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.error("Exceção não tratada:\n%s", detalhes)
    try:
        from tkinter import messagebox
        messagebox.showerror(
            "Erro inesperado",
            "Ocorreu um erro inesperado. Detalhes registrados em logs/.\n\n"
            f"{exc_value}")
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def instalar_exception_hook():
    """Instala o exception hook global que registra erros em log."""
    sys.excepthook = _log_excecao_nao_tratada


# Chamada no carregamento para já deixar o logger pronto e o hook ativo.
LOGGER = configurar_logging()
instalar_exception_hook()