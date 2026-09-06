import json
import os
import shutil
import tempfile
import unittest

import config


class TestConfigSenhaCriptografada(unittest.TestCase):
    """Garante que a senha SMTP é gravada cifrada e lida de volta em claro."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.arquivo = os.path.join(self.tmpdir, "config_smtp.json")
        self._orig_caminho = config.CAMINHO_CONFIG
        config.CAMINHO_CONFIG = self.arquivo

    def tearDown(self):
        config.CAMINHO_CONFIG = self._orig_caminho
        config._chave_cifra.cache_clear()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _gravar_json(self, dados):
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def test_salvar_grava_cifrado_e_carrega_em_claro(self):
        config.salvar_config({
            "host": "smtp.gmail.com",
            "porta": "587",
            "usuario": "usuario@gmail.com",
            "senha": "@@@SenhaDeApp123!",
            "destinatario": "destino@exemplo.com",
            "tls": "1",
            "enviar_email": "1",
        })
        # Passa pelos outros campos intactos e não expõe a senha em texto puro.
        with open(self.arquivo, encoding="utf-8") as f:
            salvo = json.load(f)
        self.assertEqual(salvo["host"], "smtp.gmail.com")
        self.assertEqual(salvo["destinatario"], "destino@exemplo.com")
        self.assertTrue(str(salvo["senha"]).startswith("enc$"))
        self.assertNotIn("@@@SenhaDeApp123!", salvo["senha"])
        # A aplicação continua recebendo a senha em claro para o login SMTP.
        cfg = config.carregar_config()
        self.assertEqual(cfg["senha"], "@@@SenhaDeApp123!")
        self.assertEqual(cfg["host"], "smtp.gmail.com")

    def test_campo_senha_vazio_continua_vazio(self):
        config.salvar_config({"host": "smtp.x.com", "senha": "", "usuario": "a"})
        with open(self.arquivo, encoding="utf-8") as f:
            salvo = json.load(f)
        self.assertEqual(salvo["senha"], "")
        self.assertEqual(config.carregar_config()["senha"], "")

    def test_legado_por_escrito_em_claro_e_lido_sem_quebrar(self):
        # Simula um arquivo criado antes da criptografia.
        self._gravar_json({
            "host": "smtp.gmail.com",
            "porta": "587",
            "usuario": "u@gmail.com",
            "senha": "senha-antiga-em-claro",
            "destinatario": "d@x.com",
            "tls": "1",
            "enviar_email": "",
        })
        cfg = config.carregar_config()
        self.assertEqual(cfg["senha"], "senha-antiga-em-claro")  # não quebra
        self.assertEqual(cfg["porta"], "587")

    def test_configurado_para_email_com_senha_legivel(self):
        config.salvar_config({
            "host": "smtp.gmail.com", "porta": "587",
            "usuario": "u@gmail.com", "senha": "12345",
            "destinatario": "d@x.com", "tls": "1", "enviar_email": "1",
        })
        self.assertTrue(config.configurado_para_email(config.carregar_config()))

    def test_nao_duplica_prefixo_ao_resalvar(self):
        config.salvar_config({"senha": "abc", "host": "h"})
        primeiro = config.carregar_config()["senha"]
        # Re-salvar cenário da UI (a senha chega "em claro" via carregar_config).
        config.salvar_config(dict(config.carregar_config(), host="h"))
        segundo = config.carregar_config()["senha"]
        self.assertEqual(primeiro, "abc")
        self.assertEqual(segundo, "abc")


if __name__ == "__main__":
    unittest.main()
