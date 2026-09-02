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
                FOREIGN KEY (perfil_id) REFERENCES perfil (id) ON DELETE CASCADE
            )
        """)

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

    def salvar_registro(self, perfil_id, peso, altura, idade, genero):
        imc = peso / (altura ** 2)
        classificacao = self.classificar_imc(imc, idade)
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO historico (perfil_id, peso, altura, idade, genero, imc, classificacao, data_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (perfil_id, peso, altura, idade, genero, round(imc, 2), classificacao, data_atual),
            )
            conn.commit()

        return round(imc, 2), classificacao

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
