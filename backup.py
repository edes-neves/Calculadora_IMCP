import os
import shutil
import smtplib
import ssl
import zipfile
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import config
import caminhos

PASTA_BACKUPS = os.path.join(caminhos.diretorio_dados(), "backups")
MAX_BACKUPS = 10


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def criar_backup_local(db_caminho, destino_nome=None):
    """Compacta o banco em um .zip dentro da pasta 'backups' e faz a rotação.

    Retorna o caminho do .zip criado (ou None em caso de falha).
    """
    try:
        if not os.path.exists(db_caminho):
            return None
        os.makedirs(PASTA_BACKUPS, exist_ok=True)
        nome = destino_nome or f"backup_{_timestamp()}.zip"
        caminho_zip = os.path.join(PASTA_BACKUPS, nome)

        with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_caminho, arcname=os.path.basename(db_caminho))

        _rotacionar_backups()
        return caminho_zip
    except OSError:
        return None


def _rotacionar_backups():
    try:
        zips = sorted(
            [f for f in os.listdir(PASTA_BACKUPS) if f.lower().endswith(".zip")],
            reverse=True)
        for antigo in zips[MAX_BACKUPS:]:
            try:
                os.remove(os.path.join(PASTA_BACKUPS, antigo))
            except OSError:
                pass
    except OSError:
        pass


def enviar_email(assunto, corpo, anexo_caminho=None):
    """Envia e-mail via SMTP usando as configurações salvas.

    Retorna (sucesso: bool, mensagem: str).
    """
    cfg = config.carregar_config()
    if not config.configurado_para_email(cfg):
        return False, "E-mail não configurado. Configure o SMTP nas Configurações."

    try:
        porta = int(cfg.get("porta") or (465 if cfg.get("tls") == "" else 587))
    except ValueError:
        porta = 587

    mensagem = MIMEMultipart()
    mensagem["From"] = cfg["usuario"]
    mensagem["To"] = cfg["destinatario"]
    mensagem["Subject"] = assunto
    mensagem.attach(MIMEText(corpo, "plain", "utf-8"))

    if anexo_caminho and os.path.exists(anexo_caminho):
        with open(anexo_caminho, "rb") as f:
            parte = MIMEApplication(f.read(), _subtype="zip")
        parte.add_header("Content-Disposition", "attachment",
                         filename=os.path.basename(anexo_caminho))
        mensagem.attach(parte)

    # Se tls estiver ativo ou a porta for a clássica 587/25, usa STARTTLS.
    usar_starttls = str(cfg.get("tls")).strip().lower() in ("1", "true", "sim", "on")
    usar_ssl = porta == 465 or str(cfg.get("tls")).strip().lower() == "ssl"

    if usar_ssl:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg["host"], porta, context=contexto) as servidor:
            servidor.login(cfg["usuario"], cfg["senha"])
            servidor.send_message(mensagem)
    else:
        with smtplib.SMTP(cfg["host"], porta, timeout=30) as servidor:
            if usar_starttls:
                servidor.starttls(context=ssl.create_default_context())
            servidor.login(cfg["usuario"], cfg["senha"])
            servidor.send_message(mensagem)
    return True, "E-mail enviado com sucesso."


def backup_completo(db_caminho):
    """Cria o backup local e, se configurado, envia por e-mail.

    Retorna (backup_zip, email_ok, email_msg).
    """
    zip_criado = criar_backup_local(db_caminho)
    email_ok = False
    msg = ""
    if config.configurado_para_email(config.carregar_config()):
        email_ok, msg = enviar_email(
            f"Backup Calculadora de IMC - {_timestamp()}",
            "Segue em anexo o backup automático do banco de dados.",
            zip_criado)
    return zip_criado, email_ok, msg


if __name__ == "__main__":
    # Teste rápido
    print(backup_completo("calculadora_imc.db"))