import json
import os

import caminhos

CAMINHO_PREFERENCIAS = os.path.join(caminhos.diretorio_dados(), "preferencias.json")

CHAVES = ("ui_tema",)


def carregar():
    try:
        with open(CAMINHO_PREFERENCIAS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        dados = {}
    base = dict.fromkeys(CHAVES, "")
    if isinstance(dados, dict):
        for chave in CHAVES:
            base[chave] = dados.get(chave, "")
    return base


def salvar(dados):
    try:
        with open(CAMINHO_PREFERENCIAS, "r", encoding="utf-8") as f:
            atual = json.load(f)
    except (OSError, ValueError):
        atual = {}
    if not isinstance(atual, dict):
        atual = {}
    for chave in CHAVES:
        if chave in dados:
            atual[chave] = dados[chave]
    with open(CAMINHO_PREFERENCIAS, "w", encoding="utf-8") as f:
        json.dump(atual, f, ensure_ascii=False, indent=2)
    return atual