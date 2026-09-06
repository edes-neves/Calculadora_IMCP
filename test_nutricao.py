import os
import tempfile
import unittest

import nutricao
from database import Database


class TestEquacoeTMB(unittest.TestCase):
    """Valida as equações de TMB contra valores de referência conhecidos."""

    def test_mifflin_homem(self):
        # Exemplo padrão: homem 30 anos, 80 kg, 1,80 m.
        tmb = nutricao.tmb_mifflin(80, 1.80, 30, "Masculino")
        # 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780
        self.assertAlmostEqual(tmb, 1780.0, places=1)

    def test_mifflin_mulher(self):
        # Mulher 30 anos, 60 kg, 1,65 m.
        tmb = nutricao.tmb_mifflin(60, 1.65, 30, "Feminino")
        # 10*60 + 6.25*165 - 5*30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
        self.assertAlmostEqual(tmb, 1320.25, places=1)

    def test_harris_benedict_homem(self):
        tmb = nutricao.tmb_harris_benedict(80, 1.80, 30, "Masculino")
        esperado = 88.362 + 13.397 * 80 + 4.799 * 180 - 5.677 * 30
        self.assertAlmostEqual(tmb, esperado, places=1)

    def test_harris_benedict_mulher(self):
        tmb = nutricao.tmb_harris_benedict(60, 1.65, 30, "Feminino")
        esperado = 447.593 + 9.247 * 60 + 3.098 * 165 - 4.330 * 30
        self.assertAlmostEqual(tmb, esperado, places=1)

    def test_nao_aplicavel_menor_18(self):
        self.assertIsNone(nutricao.tmb_mifflin(30, 1.3, 10, "Masculino"))
        self.assertIsNone(nutricao.tmb_harris_benedict(30, 1.3, 10, "Feminino"))

    def test_calcular_get(self):
        tmb = nutricao.tmb_mifflin(80, 1.80, 30, "Masculino")  # 1780.0
        get = nutricao.get_total(tmb, 1.55)
        self.assertAlmostEqual(get, 1780.0 * 1.55, places=1)
        tmb2, fator2, get2 = nutricao.calcular_get(80, 1.80, 30, "Masculino",
                                                   atividade="moderado", metodo="mifflin")
        self.assertAlmostEqual(tmb2, 1780.0, places=1)
        self.assertAlmostEqual(fator2, 1.55, places=2)
        self.assertAlmostEqual(get2, 1780.0 * 1.55, places=1)


class TestFatoresAtividade(unittest.TestCase):
    def test_fatores(self):
        self.assertAlmostEqual(nutricao.fator_atividade("sedentario"), 1.2)
        self.assertAlmostEqual(nutricao.fator_atividade("leve"), 1.375)
        self.assertAlmostEqual(nutricao.fator_atividade("moderado"), 1.55)
        self.assertAlmostEqual(nutricao.fator_atividade("intenso"), 1.725)
        self.assertAlmostEqual(nutricao.fator_atividade("atleta"), 1.9)
        # chave desconhecida usa padrão 1.2
        self.assertAlmostEqual(nutricao.fator_atividade("nao_existe"), 1.2)

    def test_resumo_nutricional(self):
        d = nutricao.resumo_nutricional(80, 1.80, 30, "Feminino",
                                        atividade="leve", metodo="mifflin")
        self.assertTrue(d["aplicavel"])
        self.assertEqual(d["tmb"]["harris"] is None, False)
        self.assertEqual(d["fator"], 1.375)
        # O app arredonda a TMB a 1 casa antes de multiplicar pelo fator.
        esperado = round(round(d["tmb"]["mifflin"] * 1.375, 1), 1)
        self.assertAlmostEqual(d["get"], esperado, places=1)


class TestPersistenciaNutricional(unittest.TestCase):
    """Garante que TMB/GET são calculados e salvos no histórico."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "teste.db")
        self.db = Database(self.path)

    def tearDown(self):
        for root, _dirs, files in os.walk(self.tmpdir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
        os.rmdir(self.tmpdir)

    def test_salva_registro_com_nutricional(self):
        pid = self.db.criar_perfil("Ana", 30, "Feminino")
        self.db.salvar_registro(pid, 60, 1.65, 30, "Feminino",
                                cintura_cm=80, quadril_cm=90,
                                atividade="leve", metodo_tmb="mifflin")
        nutri = self.db.buscar_ultimo_nutricional(pid)
        self.assertIsNotNone(nutri)
        tmb_miff, tmb_har, fator, metodo, get, _data = nutri
        self.assertAlmostEqual(tmb_miff, 1320.25, places=1)
        self.assertIsNotNone(tmb_har)
        self.assertAlmostEqual(fator, 1.375, places=2)
        self.assertEqual(metodo, "mifflin")
        self.assertAlmostEqual(get, 1320.25 * 1.375, places=1)

    def test_menor_de_18_nao_salva_nutricional(self):
        pid = self.db.criar_perfil("Crianca", 10, "Masculino")
        self.db.salvar_registro(pid, 30, 1.3, 10, "Masculino",
                                atividade="moderado", metodo_tmb="mifflin")
        nutri = self.db.buscar_ultimo_nutricional(pid)
        self.assertIsNotNone(nutri)
        self.assertIsNone(nutri[0])  # tmb_mifflin
        self.assertIsNone(nutri[1])  # tmb_harris
        self.assertIsNone(nutri[4])  # get_total


class TestRelatorioNutricional(unittest.TestCase):
    """O relatório PDF deve aceitar o bloco de gasto energético sem erro."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_relatorio_inclui_energia(self):
        import relatorio
        caminho = os.path.join(self.tmpdir, "relatorio_energia.pdf")
        # nutricional = (tmb_mifflin, tmb_harris, fator, metodo, get, data)
        nutricional = (1320.2, 1320.5, 1.375, "mifflin", 1815.3, "01/01/2025")
        relatorio.gerar_pdf_relatorio(
            caminho, "Ana", 30, "Feminino", 60, 1.65, 22.04, "Peso Normal",
            50.4, 67.8, "#2ECC71", meta=58.0, nutricional=nutricional)
        self.assertTrue(os.path.exists(caminho))
        with open(caminho, "rb") as f:
            self.assertEqual(f.read(4), b"%PDF")


if __name__ == "__main__":
    unittest.main()
