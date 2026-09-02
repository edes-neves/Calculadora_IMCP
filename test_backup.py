import os
import shutil
import sqlite3
import tempfile
import unittest

import backup
import config


class TestBackup(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "teste.db")
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE teste (id INTEGER)")
        conn.commit()
        conn.close()
        # Redireciona a pasta de backups para o diretório temporário
        self._orig_pasta = backup.PASTA_BACKUPS
        backup.PASTA_BACKUPS = os.path.join(self.tmpdir, "backups")

    def tearDown(self):
        backup.PASTA_BACKUPS = self._orig_pasta
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_criar_backup_local(self):
        zipf = backup.criar_backup_local(self.db_path)
        self.assertIsNotNone(zipf)
        self.assertTrue(os.path.exists(zipf))
        self.assertTrue(zipf.endswith(".zip"))

    def test_criar_backup_arquivo_inexistente(self):
        self.assertIsNone(backup.criar_backup_local(os.path.join(self.tmpdir, "nao_existe.db")))

    def test_rotacao_mantem_limite(self):
        for i in range(15):
            backup.criar_backup_local(self.db_path, destino_nome=f"backup_{i}.zip")
        zips = [f for f in os.listdir(backup.PASTA_BACKUPS) if f.endswith(".zip")]
        self.assertLessEqual(len(zips), backup.MAX_BACKUPS)

    def test_email_sem_configuracao_falha_graciosamente(self):
        # garante arquivo inexistente
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config_smtp.json")
        if os.path.exists(caminho):
            os.rename(caminho, caminho + ".bak")
        try:
            ok, msg = backup.enviar_email("a", "b")
            self.assertFalse(ok)
            self.assertIn("não configurado", msg.lower())
        finally:
            if os.path.exists(caminho + ".bak"):
                os.rename(caminho + ".bak", caminho)


class TestExportacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        from database import Database
        self.db = Database(self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_exportar_json(self):
        import json
        pid = self.db.criar_perfil("Export", 30, "Masculino")
        self.db.salvar_registro(pid, 75, 1.75, 30, "Masculino")
        caminho = os.path.join(os.path.dirname(self.tmp.name), "dados.json")
        self.db.exportar_json(caminho)
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        self.assertIn("perfis", dados)
        self.assertIn("historico", dados)
        self.assertEqual(len(dados["perfis"]), 1)
        self.assertEqual(len(dados["historico"]), 1)
        os.unlink(caminho)

    def test_exportar_csv(self):
        pid = self.db.criar_perfil("Export CSV", 40, "Feminino")
        self.db.salvar_registro(pid, 65, 1.65, 40, "Feminino")
        caminho = os.path.join(os.path.dirname(self.tmp.name), "dados.csv")
        self.db.exportar_csv(caminho)
        with open(caminho, encoding="utf-8") as f:
            conteudo = f.read()
        self.assertIn("Export CSV", conteudo)
        os.unlink(caminho)


if __name__ == "__main__":
    unittest.main()