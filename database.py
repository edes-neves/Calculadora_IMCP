import sqlite3
from datetime import datetime

# Limites lógicos de validação (kg / m / anos)
LIMITES = {
    "peso_min": 2.0,
    "peso_max": 400.0,
    "altura_min": 0.40,
    "altura_max": 2.50,
    "idade_min": 2,
    "idade_max": 120,
}


class Database:
    def __init__(self, db_name="calculadora_imc.db"):
        self.db_name = db_name
        self.criar_tabelas()

    def conectar(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def criar_tabelas(self):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS perfil (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    idade INTEGER NOT NULL,
                    genero TEXT NOT NULL,
                    meta_peso REAL,
                    data_criacao TEXT NOT NULL
                )
            """)

            # Migração: a tabela historico antiga não possuía perfil_id.
            colunas = [r[1] for r in cursor.execute("PRAGMA table_info(historico)").fetchall()]
            if colunas and "perfil_id" not in colunas:
                cursor.execute("ALTER TABLE historico RENAME TO historico_antigo")
                self._criar_tabela_historico(cursor)
                # Cria um perfil padrão e migra os registros antigos para ele
                cursor.execute(
                    "INSERT INTO perfil (nome, idade, genero, data_criacao) VALUES (?, ?, ?, ?)",
                    ("Perfil padrão", 30, "Masculino", datetime.now().strftime("%d/%m/%Y")),
                )
                id_padrao = cursor.lastrowid
                cursor.execute(
                    "SELECT id, peso, altura, idade, genero, imc, classificacao, data_registro FROM historico_antigo"
                )
                for reg in cursor.fetchall():
                    cursor.execute(
                        "INSERT INTO historico (id, perfil_id, peso, altura, idade, genero, imc, classificacao, data_registro) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (reg[0], id_padrao, reg[1], reg[2], reg[3], reg[4], reg[5], reg[6], reg[7]),
                    )
                cursor.execute("DROP TABLE historico_antigo")
            else:
                self._criar_tabela_historico(cursor)
            self._migrar_colunas(cursor)
            conn.commit()

    @staticmethod
    def _criar_tabela_historico(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                perfil_id INTEGER NOT NULL,
                peso REAL NOT NULL,
                altura REAL NOT NULL,
                idade INTEGER NOT NULL,
                genero TEXT NOT NULL,
                imc REAL NOT NULL,
                classificacao TEXT NOT NULL,
                data_registro TEXT NOT NULL,
                cintura_cm REAL,
                quadril_cm REAL,
                gordura_pct REAL,
                rcq REAL,
                risco_cintura TEXT,
                FOREIGN KEY (perfil_id) REFERENCES perfil (id) ON DELETE CASCADE
            )
        """)

    @staticmethod
    def _migrar_colunas(cursor):
        """Adiciona colunas novas ao schema do histórico em bancos já existentes."""
        colunas = [r[1] for r in cursor.execute("PRAGMA table_info(historico)").fetchall()]
        novas = {
            "cintura_cm": "REAL",
            "quadril_cm": "REAL",
            "gordura_pct": "REAL",
            "rcq": "REAL",
            "risco_cintura": "TEXT",
        }
        for nome, tipo in novas.items():
            if nome not in colunas:
                cursor.execute(f"ALTER TABLE historico ADD COLUMN {nome} {tipo}")

    # ---------- Perfis ----------
    def criar_perfil(self, nome, idade, genero):
        data_atual = datetime.now().strftime("%d/%m/%Y")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO perfil (nome, idade, genero, data_criacao) VALUES (?, ?, ?, ?)",
                (nome, idade, genero, data_atual),
            )
            conn.commit()
            return cursor.lastrowid

    def editar_perfil(self, perfil_id, nome, idade, genero):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE perfil SET nome = ?, idade = ?, genero = ? WHERE id = ?",
                (nome, idade, genero, perfil_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def excluir_perfil(self, perfil_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM perfil WHERE id = ?", (perfil_id,))
            conn.commit()
            return cursor.rowcount > 0

    def listar_perfis(self):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, idade, genero FROM perfil ORDER BY id ASC"
            )
            return cursor.fetchall()

    def buscar_perfil(self, perfil_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, idade, genero, meta_peso FROM perfil WHERE id = ?", (perfil_id,)
            )
            return cursor.fetchone()

    def definir_meta(self, perfil_id, meta_peso):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE perfil SET meta_peso = ? WHERE id = ?", (meta_peso, perfil_id))
            conn.commit()
            return cursor.rowcount > 0

    def excluir_historico_do_perfil(self, perfil_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historico WHERE perfil_id = ?", (perfil_id,))
            conn.commit()

    # ---------- Cálculos ----------
    def calcular_peso_ideal(self, altura, idade):
        """Calcula a faixa de peso ideal baseada na idade (adulto vs idoso)."""
        if idade >= 60:
            peso_min = 22 * (altura ** 2)
            peso_max = 27 * (altura ** 2)
        else:
            peso_min = 18.5 * (altura ** 2)
            peso_max = 24.9 * (altura ** 2)
        return peso_min, peso_max

    def classificar_imc(self, imc, idade):
        """Retorna a classificação oficial da OMS / SBGG."""
        if idade >= 60:
            if imc < 22.0:
                return "Baixo Peso"
            elif imc < 27.0:
                return "Peso Normal"
            elif imc < 30.0:
                return "Sobrepeso"
            else:
                return "Obesidade"
        else:
            if imc < 18.5:
                return "Abaixo do Peso"
            elif imc < 25.0:
                return "Peso Normal"
            elif imc < 30.0:
                return "Sobrepeso"
            elif imc < 35.0:
                return "Obesidade Grau I"
            elif imc < 40.0:
                return "Obesidade Grau II"
            else:
                return "Obesidade Grau III"

    @staticmethod
    def validar_peso(peso):
        return LIMITES["peso_min"] <= peso <= LIMITES["peso_max"]

    @staticmethod
    def validar_altura(altura):
        return LIMITES["altura_min"] <= altura <= LIMITES["altura_max"]

    @staticmethod
    def validar_idade(idade):
        return LIMITES["idade_min"] <= idade <= LIMITES["idade_max"]

    def salvar_registro(self, perfil_id, peso, altura, idade, genero,
                        cintura_cm=None, quadril_cm=None):
        imc = peso / (altura ** 2)
        classificacao = self.classificar_imc(imc, idade)
        gordura = self.calcular_gordura_corporal(imc, idade, genero) if idade > 0 else None
        rcq = self.calcular_rcq(cintura_cm, quadril_cm)
        risco = self.classificar_risco_cintura(cintura_cm, genero)
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO historico (
                    perfil_id, peso, altura, idade, genero, imc, classificacao, data_registro,
                    cintura_cm, quadril_cm, gordura_pct, rcq, risco_cintura
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (perfil_id, peso, altura, idade, genero, round(imc, 2), classificacao, data_atual,
                 cintura_cm, quadril_cm, gordura, rcq, risco),
            )
            conn.commit()

        return round(imc, 2), classificacao

    @staticmethod
    def calcular_gordura_corporal(imc, idade, genero):
        """% de gordura estimado pela fórmula de Deurenberg (adultos) e ajuste em idosos.

        Retorna None quando o IMC informado está fora da faixa recomendada para a fórmula.
        """
        if not (20 <= imc <= 25):
            return None
        if idade < 16 or idade > 100:
            return None
        if genero == "Feminino":
            gordura = 1.20 * imc + 0.23 * idade - 5.4 - 10.8
        elif genero == "Masculino":
            gordura = 1.20 * imc + 0.23 * idade - 5.4 - 0.0
        else:
            gordura = 1.20 * imc + 0.23 * idade - 5.4
        return round(gordura, 1)

    @staticmethod
    def calcular_rcq(cintura_cm, quadril_cm):
        if cintura_cm is None or quadril_cm is None or quadril_cm <= 0:
            return None
        return round(cintura_cm / quadril_cm, 2)

    @staticmethod
    def classificar_risco_cintura(cintura_cm, genero):
        """Risco cardiovascular pela cintura (OMS)."""
        if cintura_cm is None:
            return None
        if genero == "Feminino":
            if cintura_cm < 80:
                return "Baixo"
            if cintura_cm < 88:
                return "Moderado"
            return "Elevado"
        if cintura_cm < 94:
            return "Baixo"
        if cintura_cm < 102:
            return "Moderado"
        return "Elevado"

    def buscar_historico(self, perfil_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT peso, altura, imc, classificacao, data_registro FROM historico "
                "WHERE perfil_id = ? ORDER BY id DESC",
                (perfil_id,),
            )
            return cursor.fetchall()

    def buscar_historico_cronologico(self, perfil_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT peso, altura, imc, classificacao, data_registro FROM historico "
                "WHERE perfil_id = ? ORDER BY id ASC",
                (perfil_id,),
            )
            return cursor.fetchall()

    def ultima_medicao(self, perfil_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT imc, classificacao FROM historico WHERE perfil_id = ? ORDER BY id DESC LIMIT 1",
                (perfil_id,),
            )
            return cursor.fetchone()

    def buscar_ultima_medicao_detalhada(self, perfil_id):
        """Retorna peso, altura, imc, cintura, quadril, gordura, rcq e risco da última medição."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT peso, altura, imc, cintura_cm, quadril_cm, gordura_pct, rcq, risco_cintura "
                "FROM historico WHERE perfil_id = ? ORDER BY id DESC LIMIT 1",
                (perfil_id,),
            )
            return cursor.fetchone()

    # ---------- Exportação (CSV / JSON) ----------
    def coletar_dados_exportacao(self):
        """Coleta todos os perfis e seus registros para exportação."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            perfil_cols = ["id", "nome", "idade", "genero", "meta_peso", "data_criacao"]
            cursor.execute("SELECT id, nome, idade, genero, meta_peso, data_criacao FROM perfil ORDER BY id")
            perfis = [dict(zip(perfil_cols, linha)) for linha in cursor.fetchall()]

            hist_cols = ["id", "perfil_id", "peso", "altura", "idade", "genero",
                         "imc", "classificacao", "data_registro", "cintura_cm",
                         "quadril_cm", "gordura_pct", "rcq", "risco_cintura"]
            cursor.execute(
                "SELECT id, perfil_id, peso, altura, idade, genero, imc, classificacao, "
                "data_registro, cintura_cm, quadril_cm, gordura_pct, rcq, risco_cintura "
                "FROM historico ORDER BY perfil_id, id")
            historico = [dict(zip(hist_cols, linha)) for linha in cursor.fetchall()]
            return {"perfis": perfis, "historico": historico}

    def exportar_json(self, caminho):
        import json as _json
        dados = self.coletar_dados_exportacao()
        with open(caminho, "w", encoding="utf-8") as f:
            _json.dump(dados, f, ensure_ascii=False, indent=2)
        return caminho

    def exportar_csv(self, caminho):
        import csv as _csv
        dados = self.coletar_dados_exportacao()
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            if dados["perfis"]:
                perfil_cols = list(dados["perfis"][0].keys())
                writer = _csv.DictWriter(f, fieldnames=perfil_cols)
                writer.writeheader()
                writer.writerows(dados["perfis"])
            else:
                f.write("perfis_vazio\n")
            f.write("\n")
            if dados["historico"]:
                hist_cols = list(dados["historico"][0].keys())
                writer = _csv.DictWriter(f, fieldnames=hist_cols)
                writer.writeheader()
                writer.writerows(dados["historico"])
            else:
                f.write("historico_vazio\n")
        return caminho
