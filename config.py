import json
import os

# Nome do arquivo de configuração (fora do controle de versão via .gitignore)
CAMINHO_CONFIG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config_smtp.json")

CHAVES = ("host", "porta", "usuario", "senha", "destinatario", "tls", "enviar_email")


def carregar_config():
    """Carrega as configurações SMTP do arquivo JSON (ou retorna padrão vazio)."""
    if not os.path.exists(CAMINHO_CONFIG):
        return {k: "" for k in CHAVES}
    try:
        with open(CAMINHO_CONFIG, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return {k: "" for k in CHAVES}
    base = {k: "" for k in CHAVES}
    base.update(dados if isinstance(dados, dict) else {})
    return base


def salvar_config(dados):
    """Persiste as configurações SMTP no arquivo JSON."""
    base = {k: (dados.get(k, "") if k in CHAVES else dados.get(k, "")) for k in CHAVES}
    with open(CAMINHO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    return base


def configurado_para_email(cfg):
    """Retorna True se há credenciais suficientes para enviar e-mail."""
    return bool(cfg.get("enviar_email")) and bool(cfg.get("host")) and bool(
        cfg.get("usuario")) and bool(cfg.get("senha")) and bool(cfg.get("destinatario"))