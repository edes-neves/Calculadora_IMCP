"""Atualização automática via GitHub Releases.

O app consulta a API pública do GitHub procurando a release mais recente do
repositório. Quando ela é mais nova que a versão instalada, o usuário é avisado
e pode baixar e aplicar a atualização com um clique, substituindo o executável
em execução (AppImage ou binário PyInstaller) pelo arquivo novo.

Falhas de rede ou ausência de release são silenciosas (apenas log).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

import caminhos
import logger

REPOSITORIO = "edes-neves/Calculadora_IMCP"
VERSAO_ATUAL = "1.1.0"
ASSET_PREFERENCIAL = ".appimage"
API_RELEASES = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
URL_RELEASES = f"https://github.com/{REPOSITORIO}/releases/latest"
_CAMPO_PULAR = "pular_versao"


def versao_numerica(tag):
    """Extrai (major, minor, patch) de uma tag como 'v1.2.3' ou '1.2.3'.

    Retorna None quando a tag não tem uma versão numérica reconhecível.
    """
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(tag))
    if not m:
        return None
    return tuple(int(g) for g in m.groups())


def ha_versao_nova(tag):
    """True se a tag de release é mais nova que a versão atual do app."""
    nova = versao_numerica(tag)
    atual = versao_numerica(VERSAO_ATUAL)
    return bool(nova and atual and nova > atual)


def _requisitar_json(url, timeout=10):
    """GET na URL e retorna o JSON decodificado (levanta em erros HTTP)."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"CalculadoraIMC/{VERSAO_ATUAL}",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _escolher_asset(assets):
    """Escolhe o asset da release para baixar (prefere o AppImage)."""
    for a in assets:
        if str(a.get("name", "")).lower().endswith(ASSET_PREFERENCIAL):
            return a
    for a in assets:
        if "calculadoraimc" in str(a.get("name", "")).lower():
            return a
    return None


def checar_atualizacao(timeout=10):
    """Consulta a release mais recente no GitHub.

    Retorna um dict com 'versao', 'url', 'nome', 'tamanho', 'notas' e
    'publicada' quando há atualização; caso contrário, retorna None.
    """
    try:
        dados = _requisitar_json(API_RELEASES, timeout)
    except urllib.error.HTTPError as exc:
        # 404 = ainda não existe release "latest" (normal no primeiro ciclo).
        logger.LOGGER.info("Verificação de atualização: HTTP %s", exc.code)
        return None
    except Exception as exc:
        logger.LOGGER.warning("Falha ao verificar atualização: %s", exc)
        return None

    tag = dados.get("tag_name") or ""
    if not ha_versao_nova(tag):
        return None

    asset = _escolher_asset(dados.get("assets") or [])
    if not asset or not asset.get("browser_download_url"):
        logger.LOGGER.info(
            "Release %s sem asset de download compatível.", tag)
        return None

    return {
        "versao": tag,
        "url": asset["browser_download_url"],
        "nome": asset.get("name") or "atualizacao",
        "tamanho": int(asset.get("size") or 0),
        "notas": (dados.get("body") or "").strip(),
        "publicada": dados.get("published_at") or "",
    }


def pasta_downloads():
    """Pasta (persistente e gravável) onde ficam os arquivos baixados."""
    pasta = os.path.join(caminhos.diretorio_dados(), "atualizacoes")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def baixar_arquivo(url, destino, callback=None, timeout=30):
    """Baixa 'url' para 'destino' em blocos.

    'callback(baixado, total)' é chamado a cada bloco com o progresso em bytes.
    Retorna 'destino'. Levanta exceção de rede/E/S em caso de falha.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "CalculadoraIMC"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, \
            open(destino, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        baixado = 0
        while True:
            bloco = resp.read(65536)
            if not bloco:
                break
            f.write(bloco)
            baixado += len(bloco)
            if callback:
                callback(baixado, total)
    return destino


def _arquivo_estado():
    return caminhos.caminho("atualizacao.json")


def versao_pulada():
    """Versão que o usuário pediu para não ser oferecida novamente."""
    try:
        with open(_arquivo_estado(), "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get(_CAMPO_PULAR, "")
    except Exception:
        return ""


def marcar_versao_pulada(versao):
    """Grava a versão a ser ignorada nas próximas verificações."""
    try:
        with open(_arquivo_estado(), "w", encoding="utf-8") as f:
            json.dump({_CAMPO_PULAR: versao}, f, ensure_ascii=False)
    except Exception:
        pass


def caminho_executavel():
    """Caminho real do executável em execução (AppImage ou binário).

    Retorna None quando o app roda em modo de desenvolvimento (python main.py),
    caso em que a atualização automática não se aplica.
    """
    if not getattr(sys, "frozen", False):
        return None
    if sys.platform.startswith("linux"):
        try:
            return os.path.realpath("/proc/self/exe")
        except OSError:
            pass
    return os.path.abspath(sys.argv[0])


def aplicar_atualizacao(arquivo_novo):
    """Substitui o executável em execução pelo arquivo baixado.

    Retorna o caminho do executável atualizado. Levanta exceção em caso de
    falha (ex.: pasta do AppImage sem permissão de escrita).
    """
    alvo = caminho_executavel()
    if not alvo:
        raise RuntimeError(
            "A atualização está disponível apenas na versão executável "
            "(AppImage ou binário final).")
    if os.path.abspath(arquivo_novo) == os.path.abspath(alvo):
        return alvo

    pasta = os.path.dirname(alvo) or "."
    if not os.path.isdir(pasta) or not os.access(pasta, os.W_OK):
        raise PermissionError(
            f"Sem permissão de escrita em: {pasta}")

    try:
        os.replace(arquivo_novo, alvo)
    except OSError:
        shutil.copy2(arquivo_novo, alvo)
    os.chmod(alvo, 0o755)
    logger.LOGGER.info("Atualização aplicada em %s", alvo)
    return alvo


def reiniciar(caminho):
    """Reabre o executável atualizado em um novo processo."""
    kwargs = {"start_new_session": True} if sys.platform.startswith("linux") else {}
    subprocess.Popen([caminho], **kwargs)
    return True