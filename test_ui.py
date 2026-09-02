import os
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

import database
import relatorio
from main import AppIMC, EMAIL_SUPORTE


def _criar_banco_temporario():
    """Cria um banco SQLite temporário e retorna o caminho (não remove ao fechar)."""
    origem = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calculadora_imc.db")
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy(origem, tmp) if os.path.exists(origem) else None
    return tmp


class TestParsingEntrada(unittest.TestCase):
    """Testa a normalização de entrada (vírgula/ponto) e a interpretação da altura."""

    def test_peso_aceita_virgula_e_ponto(self):
        self.assertEqual(AppIMC._limpar_numero("87,8"), "87.8")
        self.assertEqual(AppIMC._limpar_numero("87.8"), "87.8")
        self.assertEqual(AppIMC._limpar_numero(" 87,8 "), "87.8")

    def test_altura_metros_com_virgula(self):
        self.assertAlmostEqual(AppIMC._interpretar_altura("1,75"), 1.75, places=3)
        self.assertAlmostEqual(AppIMC._interpretar_altura("1.75"), 1.75, places=3)

    def test_altura_centimetros_convertida(self):
        self.assertAlmostEqual(AppIMC._interpretar_altura("175"), 1.75, places=3)
        self.assertAlmostEqual(AppIMC._interpretar_altura("175,5"), 1.755, places=3)
        self.assertAlmostEqual(AppIMC._interpretar_altura("190"), 1.90, places=3)

    def test_altura_valor_acima_do_teto_entendido_como_cm(self):
        # 3.0 m é inválido como metros, então vira 3 cm -> 0.03 m (fora dos limites)
        self.assertAlmostEqual(AppIMC._interpretar_altura("300"), 3.0, places=3)

    def test_entrada_invalida_lanca_erro(self):
        with self.assertRaises(ValueError):
            AppIMC._interpretar_altura("abc")
        with self.assertRaises(ValueError):
            float(AppIMC._limpar_numero(""))


class TestCalculoViaApp(unittest.TestCase):
    """Testa o fluxo de cálculo pela UI usando um banco temporário."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mktemp(suffix=".db")
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calculadora_imc.db"),
                    cls.tmp)
        cls._orig_conectar = database.Database.conectar
        database.Database.conectar = lambda self: sqlite3.connect(cls.tmp)

    def setUp(self):
        self.app = AppIMC()
        self.app.update()

    def tearDown(self):
        if hasattr(self, "app") and self.app.winfo_exists():
            self.app.destroy()

    @classmethod
    def tearDownClass(cls):
        database.Database.conectar = cls._orig_conectar
        if os.path.exists(cls.tmp):
            os.unlink(cls.tmp)

    def _calcular(self, peso, altura):
        if self.app.perfil_atual_id is None:
            self.skipTest("banco sem perfis")
        self.app.entry_peso.delete(0, "end")
        self.app.entry_peso.insert(0, peso)
        self.app.entry_altura.delete(0, "end")
        self.app.entry_altura.insert(0, altura)
        self.app.processar_calculo()
        return self.app.lbl_resultado_imc.cget("text"), self.app.lbl_classificacao.cget("text")

    def test_calcula_com_peso_virgula_e_altura_cm(self):
        texto, classe = self._calcular("87,8", "175")
        self.assertIn("IMC:", texto)
        self.assertNotEqual(classe, "Erro")

    def test_calcula_com_peso_ponto_e_altura_metros(self):
        texto, classe = self._calcular("75.5", "1.75")
        self.assertIn("IMC:", texto)
        self.assertNotEqual(classe, "Erro")

    def test_entrada_invalida_mostra_erro_amigavel(self):
        self._calcular("abc", "1.75")
        self.assertEqual(self.app.lbl_resultado_imc.cget("text"), "Erro")

    def test_resultado_corresponde_ao_calculo_manual(self):
        texto, _ = self._calcular("80", "1.80")
        imc_esperado = 80 / (1.80 ** 2)
        imc_exibido = float(texto.split(":")[1].strip())
        self.assertAlmostEqual(imc_exibido, round(imc_esperado, 2), places=2)


class TestGraficosERelatorio(unittest.TestCase):
    """Testa a geração de imagens e do relatório/gráfico em PDF."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmp = os.path.join(self.tmpdir, "teste.db")
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calculadora_imc.db"),
                    self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_gera_barra_imc(self):
        import grafico
        png = grafico.gerar_barra_imc(22.5, 30)
        self.assertIsNotNone(png)
        self.assertTrue(len(png) > 0)
        # PNG assinatura
        self.assertEqual(png[:4], b"\x89PNG")

    def test_gera_grafico_evolucao(self):
        import grafico
        png = grafico.gerar_grafico_evolucao(["01/01", "01/02"], [22.0, 23.0])
        self.assertEqual(png[:4], b"\x89PNG")

    def test_gera_relatorio_pdf(self):
        caminho = os.path.join(self.tmpdir, "relatorio.pdf")
        db = database.Database(self.tmp)
        pid = db.criar_perfil("Paciente Teste", 30, "Masculino")
        imc, classe = db.salvar_registro(pid, 75, 1.75, 30, "Masculino")
        relatorio.gerar_pdf_relatorio(caminho, "Paciente Teste", 30, "Masculino",
                                      75, 1.75, imc, classe, 56.0, 76.0, "#2ECC71", 72.0)
        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(os.path.getsize(caminho) > 0)

    def test_gera_pdf_do_grafico(self):
        import grafico
        caminho = os.path.join(self.tmpdir, "grafico.pdf")
        png = grafico.gerar_grafico_evolucao(["01/01", "01/02"], [22.0, 23.0])
        relatorio.gerar_pdf_grafico(caminho, "Paciente Teste", png)
        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(os.path.getsize(caminho) > 0)


if __name__ == "__main__":
    unittest.main()