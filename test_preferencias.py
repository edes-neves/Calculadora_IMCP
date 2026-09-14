import os
import shutil
import tempfile
import unittest

import preferencias


class TestPreferencias(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.arquivo = os.path.join(self.tmpdir, "preferencias.json")
        self._orig_caminho = preferencias.CAMINHO_PREFERENCIAS
        preferencias.CAMINHO_PREFERENCIAS = self.arquivo

    def tearDown(self):
        preferencias.CAMINHO_PREFERENCIAS = self._orig_caminho
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_padrao_quando_nao_existe_arquivo(self):
        self.assertEqual(preferencias.carregar(), {"ui_tema": ""})

    def test_salvar_e_carregar_tema(self):
        preferencias.salvar({"ui_tema": "Light"})
        self.assertEqual(preferencias.carregar()["ui_tema"], "Light")

    def test_salvar_preserva_outras_chaves(self):
        preferencias.salvar({"ui_tema": "Light"})
        preferencias.salvar({"outra_chave": "valor"})
        self.assertEqual(preferencias.carregar()["ui_tema"], "Light")

    def test_arquivo_invalido_retorna_padrao(self):
        with open(self.arquivo, "w", encoding="utf-8") as f:
            f.write("{invalido")
        self.assertEqual(preferencias.carregar(), {"ui_tema": ""})


if __name__ == "__main__":
    unittest.main()