"""Cálculos de nutrição clínica: TMB (Mifflin-St Jeor e Harris-Benedict) e GET.

Módulo com funções puras (sem estado/UI/SQL), de modo a permitir testes unitários
e reutilização tanto pela interface quanto pelos relatórios e pela camada de dados.
"""

# Fatores de atividade (Food and Agriculture Organization / Forças de Defesa,
# conforme diretrizes usuais). Cada entrada é (chave, rótulo, fator).
ATIVIDADES = (
    ("sedentario", "Sedentário (pouco ou nenhum exercício)", 1.2),
    ("leve", "Levemente ativo (exercício leve 1-3x/semana)", 1.375),
    ("moderado", "Moderadamente ativo (exercício moderado 3-5x/semana)", 1.55),
    ("intenso", "Muito ativo (exercício intenso 6-7x/semana)", 1.725),
    ("atleta", "Extremamente ativo (trabalho físico + treino diário)", 1.9),
)


def idade_maior_que_17(idade):
    """Os cálculos de TMB incorporados aplicam-se a adultos (>= 18 anos)."""
    return bool(idade) and idade >= 18 and idade <= 130


def fator_atividade(chave):
    """Retorna o fator multiplicador (float) dado a chave, ou 1.2 por padrão."""
    for k, _rotulo, fator in ATIVIDADES:
        if k == chave:
            return fator
    return 1.2


def _altura_cm(altura_m):
    return altura_m * 100.0


def tmb_mifflin(peso_kg, altura_m, idade, genero):
    """Gasto energético basal por Mifflin-St Jeor (1990).

    Fórmula reconhecida pela OMS/ADA como referência para adultos saudáveis.
    Retorna None fora da faixa adulta ou para gênero não suportado.
    """
    if not idade_maior_que_17(idade):
        return None
    a = _altura_cm(altura_m)
    base = 10 * peso_kg + 6.25 * a - 5 * idade
    if genero == "Masculino":
        return round(base + 5, 1)
    if genero == "Feminino":
        return round(base - 161, 1)
    # "Outro": média sem o ajuste de gênero (as fórmulas clássicas são binárias).
    return round(base, 1)


def tmb_harris_benedict(peso_kg, altura_m, idade, genero):
    """Gasto energético basal pela equação de Harris-Benedict (rev. 1984)."""
    if not idade_maior_que_17(idade):
        return None
    a = _altura_cm(altura_m)
    if genero == "Masculino":
        return round(88.362 + 13.397 * peso_kg + 4.799 * a - 5.677 * idade, 1)
    if genero == "Feminino":
        return round(447.593 + 9.247 * peso_kg + 3.098 * a - 4.330 * idade, 1)
    # "Outro": média das equações masculina e feminina.
    masc = 88.362 + 13.397 * peso_kg + 4.799 * a - 5.677 * idade
    fem = 447.593 + 9.247 * peso_kg + 3.098 * a - 4.330 * idade
    return round((masc + fem) / 2.0, 1)


def calcular_tmb(peso_kg, altura_m, idade, genero, metodo="mifflin"):
    """Calcula a TMB pelo método escolhido.

    ``metodo`` pode ser "mifflin" ou "harris". Retorna None se não aplicável.
    """
    if metodo == "harris":
        return tmb_harris_benedict(peso_kg, altura_m, idade, genero)
    return tmb_mifflin(peso_kg, altura_m, idade, genero)


def get_total(tmb, fator):
    """Gasto Energético Total (GET) = TMB x fator de atividade."""
    if tmb is None or fator is None:
        return None
    return round(tmb * fator, 1)


def calcular_get(peso_kg, altura_m, idade, genero, atividade="sedentario",
                 metodo="mifflin"):
    """Cálculo de GET num único passo: usa a TMB (método) e o fator de atividade."""
    tmb = calcular_tmb(peso_kg, altura_m, idade, genero, metodo=metodo)
    if tmb is None:
        return None, None, None
    fator = fator_atividade(atividade)
    get = get_total(tmb, fator)
    return tmb, fator, get


def resumo_nutricional(peso_kg, altura_m, idade, genero, atividade="sedentario",
                       metodo="mifflin"):
    """Retorna dict com TMB (2 métodos) e GET do método escolhido.

    Estrutura de retorno::

        {
            "aplicavel": bool,
            "idade_valida": bool,
            "atividade": chave,
            "fator": float,
            "tmb": {"mifflin": float|None, "harris": float|None},
            "get": float|None,
            "get_metodo": metodo,
        }
    """
    if not idade_maior_que_17(idade):
        return {
            "aplicavel": False,
            "idade_valida": False,
            "atividade": atividade,
            "fator": None,
            "tmb": {"mifflin": None, "harris": None},
            "get": None,
            "get_metodo": metodo,
        }

    mifflin = tmb_mifflin(peso_kg, altura_m, idade, genero)
    harris = tmb_harris_benedict(peso_kg, altura_m, idade, genero)
    fator = fator_atividade(atividade)

    get = None
    if metodo == "harris":
        get = get_total(harris, fator)
    elif metodo == "mifflin":
        get = get_total(mifflin, fator)

    return {
        "aplicavel": True,
        "idade_valida": True,
        "atividade": atividade,
        "fator": fator,
        "tmb": {"mifflin": mifflin, "harris": harris},
        "get": get,
        "get_metodo": metodo,
    }
