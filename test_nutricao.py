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


class TestPregasCutaneas(unittest.TestCase):
    """Valida o protocolo de 3 dobras (Jackson & Pollock) + equação de Siri."""

    def _esperado(self, soma, idade, genero):
        soma2 = soma ** 2
        if genero == "Masculino":
            dc = 1.10938 - 0.0008267 * soma + 0.0000016 * soma2 - 0.0002574 * idade
        elif genero == "Feminino":
            dc = 1.0994921 - 0.0009929 * soma + 0.0000023 * soma2 - 0.0001392 * idade
        else:
            masc = 1.10938 - 0.0008267 * soma + 0.0000016 * soma2 - 0.0002574 * idade
            fem = 1.0994921 - 0.0009929 * soma + 0.0000023 * soma2 - 0.0001392 * idade
            dc = (masc + fem) / 2.0
        return round((4.95 / dc - 4.50) * 100.0, 1)

    def test_pregas_3_obrigatorias_por_genero(self):
        self.assertEqual(nutricao.pregas_3_obrigatorias("Masculino"),
                         ("peitoral", "abdominal", "coxa"))
        self.assertEqual(nutricao.pregas_3_obrigatorias("Feminino"),
                         ("tricipital", "suprailiaca", "coxa"))

    def test_gordura_homem(self):
        pregas = {"peitoral": 15, "abdominal": 20, "coxa": 25}
        self.assertEqual(nutricao.gordura_pct_pregas(pregas, 30, "Masculino"),
                         self._esperado(60, 30, "Masculino"))

    def test_gordura_mulher(self):
        pregas = {"tricipital": 18, "suprailiaca": 16, "coxa": 22}
        self.assertEqual(nutricao.gordura_pct_pregas(pregas, 35, "Feminino"),
                         self._esperado(56, 35, "Feminino"))

    def test_gordura_outro_usa_media(self):
        pregas = {"tricipital": 18, "suprailiaca": 16, "coxa": 22}
        self.assertEqual(nutricao.gordura_pct_pregas(pregas, 35, "Outro"),
                         self._esperado(56, 35, "Outro"))

    def test_falta_prega_retorna_none(self):
        self.assertIsNone(nutricao.gordura_pct_pregas({"peitoral": 15, "abdominal": 20},
                                                      30, "Masculino"))
        self.assertIsNone(nutricao.gordura_pct_pregas({}, 30, "Masculino"))
        self.assertIsNone(nutricao.gordura_pct_pregas(None, 30, "Masculino"))

    def test_valor_fora_da_faixa_retorna_none(self):
        pregas = {"peitoral": 1.5, "abdominal": 20, "coxa": 25}  # abaixo do mínimo
        self.assertIsNone(nutricao.gordura_pct_pregas(pregas, 30, "Masculino"))
        pregas2 = {"peitoral": 15, "abdominal": 20, "coxa": 120}  # acima do máximo
        self.assertIsNone(nutricao.gordura_pct_pregas(pregas2, 30, "Masculino"))

    def test_menor_de_18_retorna_none(self):
        pregas = {"peitoral": 15, "abdominal": 20, "coxa": 25}
        self.assertIsNone(nutricao.gordura_pct_pregas(pregas, 10, "Masculino"))


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

    def test_salva_registro_com_pregas(self):
        pid = self.db.criar_perfil("Carlos", 30, "Masculino")
        self.db.salvar_registro(pid, 80, 1.8, 30, "Masculino",
                                pregas={"peitoral": 15, "abdominal": 20, "coxa": 25})
        pregas = self.db.buscar_ultima_pregas(pid)
        self.assertIsNotNone(pregas)
        gordura, peit, abd, coxa, tri, supra = pregas
        self.assertIsNotNone(gordura)
        self.assertAlmostEqual(peit, 15.0, places=1)
        self.assertAlmostEqual(abd, 20.0, places=1)
        self.assertAlmostEqual(coxa, 25.0, places=1)
        self.assertIsNone(tri)
        self.assertIsNone(supra)

    def test_menor_de_18_nao_salva_gordura_pregas(self):
        pid = self.db.criar_perfil("Jovem", 15, "Masculino")
        self.db.salvar_registro(pid, 55, 1.65, 15, "Masculino",
                                pregas={"peitoral": 15, "abdominal": 20, "coxa": 25})
        pregas = self.db.buscar_ultima_pregas(pid)
        self.assertIsNotNone(pregas)
        self.assertIsNone(pregas[0])  # gordura_pct_pregas


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

    def test_relatorio_inclui_pregas(self):
        import relatorio
        caminho = os.path.join(self.tmpdir, "relatorio_pregas.pdf")
        # pregas = (gordura_pct_pregas, peitoral, abdominal, coxa, tricipital, suprailiaca)
        pregas = (17.9, 15.0, 20.0, 25.0, None, None)
        relatorio.gerar_pdf_relatorio(
            caminho, "Carlos", 30, "Masculino", 80, 1.80, 24.69, "Peso Normal",
            61.5, 82.7, "#2ECC71", pregas=pregas)
        self.assertTrue(os.path.exists(caminho))
        with open(caminho, "rb") as f:
            self.assertEqual(f.read(4), b"%PDF")


if __name__ == "__main__":
    unittest.main()
