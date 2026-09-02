import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def _png_mem(data):
    return io.BytesIO(data)

# Faixas de IMC para adultos (OMS)
FAIXAS_ADULTO = [
    (0, 18.5, "#00B4D8", "Abaixo do Peso"),
    (18.5, 25.0, "#2ECC71", "Normal"),
    (25.0, 30.0, "#FF8C00", "Sobrepeso"),
    (30.0, 35.0, "#800080", "Grau I"),
    (35.0, 40.0, "#B22222", "Grau II"),
    (40.0, 50.0, "#FF5A5F", "Grau III"),
]

FAIXAS_IDOSO = [
    (0, 22.0, "#2ECC71", "Normal"),
    (22.0, 27.0, "#FF8C00", "Sobrepeso"),
    (27.0, 30.0, "#800080", "Grau I"),
    (30.0, 50.0, "#FF5A5F", "Obesidade"),
]


def _faixas(idade):
    return FAIXAS_IDOSO if idade >= 60 else FAIXAS_ADULTO


def gerar_barra_imc(imc, idade):
    """Gera uma imagem PNG (bytes) com a barra das faixas de IMC e marca o valor atual."""
    faixas = _faixas(idade)
    max_lim = max(f[1] for f in faixas)

    fig, ax = plt.subplots(figsize=(6, 1.0), dpi=110)
    for inicio, fim, cor, _ in faixas:
        ax.add_patch(Rectangle((inicio, 0), fim - inicio, 1.0, facecolor=cor, edgecolor="none"))

    ax.add_patch(Rectangle((imc - 0.15, -0.25), 0.3, 1.5, facecolor="none", edgecolor="black", linewidth=2))

    ax.text(imc, 1.45, f"{imc:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xlim(0, max_lim)
    ax.set_ylim(-0.3, 1.9)
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def gerar_grafico_evolucao(pontos_data, pontos_imc):
    """Gera um PNG (bytes) com a evolução do IMC ao longo do tempo."""
    fig, ax = plt.subplots(figsize=(6.5, 3.0), dpi=110)

    ax.plot(range(len(pontos_imc)), pontos_imc, marker="o", color="#00B4D8", linewidth=2)
    ax.fill_between(range(len(pontos_imc)), pontos_imc, min(pontos_imc) - 2, color="#00B4D8", alpha=0.15)

    ax.axhline(25.0, color="#999999", linestyle="--", linewidth=1)
    ax.text(len(pontos_imc) - 0.3, 25.3, "Limite superior (25)", fontsize=8, color="#8A8F98", ha="right")

    ax.set_xticks(range(len(pontos_data)))
    ax.set_xticklabels([d[5:] for d in pontos_data], fontsize=7, rotation=30)
    ax.set_ylabel("IMC", fontsize=9)
    ax.set_ylim(min(min(pontos_imc), 20) - 3, max(max(pontos_imc), 30) + 3)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
