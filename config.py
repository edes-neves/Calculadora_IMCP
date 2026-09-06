import base64
import functools
import hashlib
import hmac
import json
import os
import platform

import caminhos

# Nome do arquivo de configuração (fora do controle de versão via .gitignore)
CAMINHO_CONFIG = os.path.join(caminhos.diretorio_dados(), "config_smtp.json")

CHAVES = ("host", "porta", "usuario", "senha", "destinatario", "tls", "enviar_email")

# ---------------------------------------------------------------------------
# Criptografia da senha SMTP em repouso (usa apenas a biblioteca padrão).
# Apenas o campo "senha" é cifrado com um algoritmo simétrico (XOR derivado de
# uma chave PBKDF2 + HMAC de integridade). Não há dependências externas, então
# nada da aplicação existente precisa mudar: a senha é sempre devolvida em claro
# por carregar_config().
# ---------------------------------------------------------------------------
_PREFIXO = "enc$"
_SALT = b"CalculadoraIMC::config::pasta::2024"
_IV_LEN = 8
_MAC_LEN = 32


@functools.lru_cache(maxsize=1)
def _chave_cifra():
    """Deriva uma chave de 32 bytes a partir de um identificador local do usuário."""
    identidade = (platform.node() + "|" + os.path.expanduser("~") +
                  "|CalculadoraIMC").encode("utf-8", "replace")
    return hashlib.pbkdf2_hmac("sha256", identidade, _SALT, 60_000, dklen=32)


def _stream_xor(dados, chave, iv):
    """Aplica um XOR de fluxo determinístico (derivado de sha256 contra-nonced)."""
    resultado = bytearray()
    contador = 0
    while len(resultado) < len(dados):
        bloco = hashlib.sha256(chave + contador.to_bytes(4, "big") + iv).digest()
        resultado.extend(bloco)
        contador += 1
    return bytes(a ^ b for a, b in zip(dados, resultado))


def _cifrar_senha(plano):
    """Cifra a senha. Retorna '' para senha vazia e um texto com prefixo caso contrário."""
    if not plano:
        return ""
    chave = _chave_cifra()
    iv = os.urandom(_IV_LEN)
    dados = plano.encode("utf-8")
    corpo = _stream_xor(dados, chave, iv)
    mac = hmac.new(chave, iv + corpo, hashlib.sha256).digest()
    payload = iv + mac + corpo
    return _PREFIXO + base64.urlsafe_b64encode(payload).decode("ascii")


def _decifrar_senha(texto):
    """Decifra uma senha salva. Textos legados (sem prefixo) são devolvidos intactos."""
    if not texto:
        return ""
    if not texto.startswith(_PREFIXO):
        # Arquivos legados gravados em texto puro (antes da criptografia).
        return texto
    try:
        payload = base64.urlsafe_b64decode(texto[len(_PREFIXO):].encode("ascii"))
    except Exception:
        return texto
    minimo = _IV_LEN + _MAC_LEN
    if len(payload) < minimo:
        return texto
    chave = _chave_cifra()
    iv = payload[:_IV_LEN]
    mac = payload[_IV_LEN:minimo]
    corpo = payload[minimo:]
    esperado = hmac.new(chave, iv + corpo, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, esperado):
        return texto  # não foi possível autenticar -> mantém o texto como está
    try:
        dados = _stream_xor(corpo, chave, iv)
        return dados.decode("utf-8")
    except Exception:
        return texto


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
    if base.get("senha"):
        base["senha"] = _decifrar_senha(base["senha"])
    return base


def salvar_config(dados):
    """Persiste as configurações SMTP no arquivo JSON.

    A senha é cifrada antes de gravar. Arquivos legados (senha em texto puro,
    sem o prefixo de cifra) são gravados de volta já cifrados.
    """
    base = {k: (dados.get(k, "") if k in CHAVES else dados.get(k, "")) for k in CHAVES}
    senha = base.get("senha", "")
    if senha and not senha.startswith(_PREFIXO):
        base["senha"] = _cifrar_senha(senha)
    with open(CAMINHO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    return base


def configurado_para_email(cfg):
    """Retorna True se há credenciais suficientes para enviar e-mail."""
    return bool(cfg.get("enviar_email")) and bool(cfg.get("host")) and bool(
        cfg.get("usuario")) and bool(cfg.get("senha")) and bool(cfg.get("destinatario"))