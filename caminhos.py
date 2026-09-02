import os
import sys


def _base_projeto():
    """Diretório do código ou do bundle PyInstaller."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _gravavel(caminho):
    try:
        os.makedirs(caminho, exist_ok=True)
        testar = os.path.join(caminho, ".write_test")
        with open(testar, "w"):
            pass
        os.remove(testar)
        return True
    except OSError:
        return False


def diretorio_dados():
    """Diretório onde ficam banco, logs, backup e config do usuário.

    Em desenvolvimento usa a pasta do projeto; em executável (PyInstaller/
    AppImage) usa a pasta de dados do usuário (~/.local/share), que é persistente
    e gravável, pois o diretório de extração do bundle é temporário.
    """
    se_empacotado = hasattr(sys, "_MEIPASS")
    base = _base_projeto()
    if not se_empacotado and _gravavel(base):
        return base

    home = os.path.expanduser("~")
    dados = os.path.join(home, ".local", "share", "CalculadoraIMC")
    os.makedirs(dados, exist_ok=True)
    return dados


def caminho(nome_arquivo):
    """Retorna o caminho de um arquivo de dados dentro do diretório dos dados."""
    return os.path.join(diretorio_dados(), nome_arquivo)


def caminho_banco():
    return caminho("calculadora_imc.db")
