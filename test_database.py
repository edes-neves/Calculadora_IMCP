import os
import tempfile
import unittest

from database import Database, LIMITES


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = Database(self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    # ---------- Cálculo do IMC ----------
    def test_calculo_imc(self):
        pid = self.db.criar_perfil("Teste", 30, "Masculino")
        imc, classe = self.db.salvar_registro(pid, 75.5, 1.75, 30, "Masculino")
        esperado = 75.5 / (1.75 ** 2)
        self.assertAlmostEqual(imc, round(esperado, 2), places=2)
        self.assertEqual(classe, "Peso Normal")

    def test_classificacao_adulto_borda(self):
        casos = [
            (18.4, "Abaixo do Peso"),
            (18.5, "Peso Normal"),
            (24.9, "Peso Normal"),
            (25.0, "Sobrepeso"),
            (29.9, "Sobrepeso"),
            (30.0, "Obesidade Grau I"),
            (34.9, "Obesidade Grau I"),
            (35.0, "Obesidade Grau II"),
            (39.9, "Obesidade Grau II"),
            (40.0, "Obesidade Grau III"),
        ]
        for imc, esperado in casos:
            with self.subTest(imc=imc):
                self.assertEqual(self.db.classificar_imc(imc, 30), esperado)

    def test_classificacao_idoso(self):
        self.assertEqual(self.db.classificar_imc(21.9, 65), "Baixo Peso")
        self.assertEqual(self.db.classificar_imc(22.0, 65), "Peso Normal")
        self.assertEqual(self.db.classificar_imc(26.9, 65), "Peso Normal")
        self.assertEqual(self.db.classificar_imc(27.0, 65), "Sobrepeso")
        self.assertEqual(self.db.classificar_imc(29.9, 65), "Sobrepeso")
        self.assertEqual(self.db.classificar_imc(30.0, 65), "Obesidade")

    def test_calcular_peso_ideal_adulto_e_idoso(self):
        p_min_a, p_max_a = self.db.calcular_peso_ideal(1.75, 30)
        self.assertAlmostEqual(p_min_a, 18.5 * 1.75 ** 2, places=4)
        self.assertAlmostEqual(p_max_a, 24.9 * 1.75 ** 2, places=4)

        p_min_i, p_max_i = self.db.calcular_peso_ideal(1.75, 65)
        self.assertAlmostEqual(p_min_i, 22 * 1.75 ** 2, places=4)
        self.assertAlmostEqual(p_max_i, 27 * 1.75 ** 2, places=4)

    # ---------- Validação de limites ----------
    def test_validacoes_limites(self):
        self.assertTrue(Database.validar_peso(2.0))
        self.assertTrue(Database.validar_peso(400.0))
        self.assertFalse(Database.validar_peso(1.9))
        self.assertFalse(Database.validar_peso(401.0))
        self.assertFalse(Database.validar_peso(-10))

        self.assertTrue(Database.validar_altura(0.40))
        self.assertTrue(Database.validar_altura(2.50))
        self.assertFalse(Database.validar_altura(0.30))
        self.assertFalse(Database.validar_altura(3.0))

        self.assertTrue(Database.validar_idade(2))
        self.assertTrue(Database.validar_idade(120))
        self.assertFalse(Database.validar_idade(1))
        self.assertFalse(Database.validar_idade(121))
        self.assertFalse(Database.validar_idade(-5))

    # ---------- CRUD de perfis ----------
    def test_criar_e_listar_perfis(self):
        pid = self.db.criar_perfil("Ana", 40, "Feminino")
        perfis = self.db.listar_perfis()
        self.assertEqual(len(perfis), 1)
        self.assertEqual(perfis[0][1], "Ana")
        self.assertEqual(perfis[0][2], 40)
        self.assertEqual(perfis[0][3], "Feminino")
        self.assertIsNotNone(pid)

    def test_editar_perfil(self):
        pid = self.db.criar_perfil("Ana", 40, "Feminino")
        self.assertTrue(self.db.editar_perfil(pid, "Ana Paula", 41, "Outro"))
        p = self.db.buscar_perfil(pid)
        self.assertEqual(p[1], "Ana Paula")
        self.assertEqual(p[2], 41)

    def test_meta_peso(self):
        pid = self.db.criar_perfil("Carlos", 50, "Masculino")
        self.db.definir_meta(pid, 74.0)
        p = self.db.buscar_perfil(pid)
        self.assertAlmostEqual(p[4], 74.0)

    def test_excluir_perfil_cascata(self):
        pid = self.db.criar_perfil("Maria", 55, "Feminino")
        self.db.salvar_registro(pid, 70, 1.6, 55, "Feminino")
        self.assertTrue(self.db.excluir_perfil(pid))
        self.assertEqual(self.db.buscar_historico(pid), [])

    # ---------- Histórico ----------
    def test_historico_do_perfil(self):
        pid = self.db.criar_perfil("João", 30, "Masculino")
        self.db.salvar_registro(pid, 75, 1.75, 30, "Masculino")
        self.db.salvar_registro(pid, 76, 1.75, 30, "Masculino")
        hist = self.db.buscar_historico(pid)
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0][0], 76)  # mais recente primeiro

    def test_historico_cronologico(self):
        pid = self.db.criar_perfil("João", 30, "Masculino")
        self.db.salvar_registro(pid, 75, 1.75, 30, "Masculino")
        self.db.salvar_registro(pid, 76, 1.75, 30, "Masculino")
        hist = self.db.buscar_historico_cronologico(pid)
        self.assertEqual([h[0] for h in hist], [75, 76])

    def test_excluir_historico_do_perfil(self):
        pid = self.db.criar_perfil("João", 30, "Masculino")
        self.db.salvar_registro(pid, 75, 1.75, 30, "Masculino")
        self.db.excluir_historico_do_perfil(pid)
        self.assertEqual(self.db.buscar_historico(pid), [])

    # ---------- Composição corporal (gordura, RCQ, risco) ----------
    def test_gordura_corporal_deurenberg(self):
        g = self.db.calcular_gordura_corporal(22, 30, "Masculino")
        self.assertAlmostEqual(g, 1.20 * 22 + 0.23 * 30 - 5.4, places=1)
        g_f = self.db.calcular_gordura_corporal(22, 30, "Feminino")
        self.assertAlmostEqual(g_f, 1.20 * 22 + 0.23 * 30 - 5.4 - 10.8, places=1)

    def test_gordura_fora_da_faixa_retorna_none(self):
        self.assertIsNone(self.db.calcular_gordura_corporal(30, 30, "Masculino"))
        self.assertIsNone(self.db.calcular_gordura_corporal(22, 15, "Masculino"))

    def test_rcq(self):
        self.assertAlmostEqual(self.db.calcular_rcq(90, 100), 0.9, places=2)
        self.assertIsNone(self.db.calcular_rcq(None, 100))
        self.assertIsNone(self.db.calcular_rcq(90, None))

    def test_risco_cintura(self):
        self.assertEqual(self.db.classificar_risco_cintura(78, "Feminino"), "Baixo")
        self.assertEqual(self.db.classificar_risco_cintura(85, "Feminino"), "Moderado")
        self.assertEqual(self.db.classificar_risco_cintura(90, "Feminino"), "Elevado")
        self.assertEqual(self.db.classificar_risco_cintura(95, "Masculino"), "Moderado")
        self.assertEqual(self.db.classificar_risco_cintura(80, "Masculino"), "Baixo")
        self.assertIsNone(self.db.classificar_risco_cintura(None, "Masculino"))

    def test_salvar_registro_com_cintura_e_quadril(self):
        pid = self.db.criar_perfil("Saúde", 35, "Masculino")
        self.db.salvar_registro(pid, 80, 1.8, 35, "Masculino",
                                cintura_cm=95, quadril_cm=100)
        detalhe = self.db.buscar_ultima_medicao_detalhada(pid)
        self.assertIsNotNone(detalhe)
        self.assertAlmostEqual(detalhe[3], 95.0)  # cintura
        self.assertAlmostEqual(detalhe[4], 100.0)  # quadril
        self.assertIsNotNone(detalhe[5])  # gordura
        self.assertAlmostEqual(detalhe[6], 0.95)  # rcq
        self.assertEqual(detalhe[7], "Moderado")  # risco

    def test_migracao_adiciona_colunas_em_banco_antigo(self):
        import sqlite3 as _sqlite3
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        os.unlink(tmp.name)
        conn = _sqlite3.connect(tmp.name)
        conn.execute("CREATE TABLE perfil (id INTEGER PRIMARY KEY, nome TEXT, idade INTEGER, genero TEXT, meta_peso REAL, data_criacao TEXT)")
        conn.execute("CREATE TABLE historico (id INTEGER PRIMARY KEY, perfil_id INTEGER, peso REAL, altura REAL, idade INTEGER, genero TEXT, imc REAL, classificacao TEXT, data_registro TEXT)")
        conn.execute("INSERT INTO perfil (nome, idade, genero, data_criacao) VALUES ('Antigo', 30, 'M', '01/01')")
        conn.execute("INSERT INTO historico (perfil_id, peso, altura, idade, genero, imc, classificacao, data_registro) VALUES (1, 75, 1.75, 30, 'M', 24.5, 'Peso Normal', '01/01')")
        conn.commit()
        conn.close()
        try:
            db = Database(tmp.name)
            colunas = [c[1] for c in db.conectar().execute("PRAGMA table_info(historico)").fetchall()]
            for col in ("cintura_cm", "quadril_cm", "gordura_pct", "rcq", "risco_cintura"):
                self.assertIn(col, colunas)
            hist = db.buscar_historico(1)
            self.assertEqual(len(hist), 1)
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
