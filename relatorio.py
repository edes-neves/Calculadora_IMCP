import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image


def gerar_pdf_relatorio(caminho, nome, idade, genero, peso, altura, imc, classe,
                        p_min, p_max, cor="#333333", meta=None, data=None):
    """Gera um PDF com o resultado da medição e salva no caminho informado."""
    c = canvas.Canvas(caminho, pagesize=A4)
    largura, altura_pagina = A4
    margem = 20 * mm

    # Cabeçalho
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor("#00B4D8")
    c.drawString(margem, altura_pagina - 40 * mm, "Relatório de IMC")

    c.setFont("Helvetica", 11)
    c.setFillColor("#000000")
    c.drawString(margem, altura_pagina - 52 * mm, f"Emitido em: {data or ''}")

    y = altura_pagina - 80 * mm

    def bloco(titulo, linhas):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor("#00B4D8")
        c.drawString(margem, y, titulo)
        y -= 8 * mm
        c.setFont("Helvetica", 11)
        c.setFillColor("#000000")
        for rotulo, valor in linhas:
            c.drawString(margem + 5 * mm, y, f"{rotulo}: {valor}")
            y -= 7 * mm
        y -= 6 * mm

    bloco("Dados do Paciente", [
        ("Nome", nome),
        ("Idade", f"{idade} anos"),
        ("Gênero", genero),
        ("Data da medição", ""),
    ])

    bloco("Medição", [
        ("Peso", f"{peso:.1f} kg"),
        ("Altura", f"{altura:.2f} m"),
        ("IMC", f"{imc:.2f}"),
        ("Classificação", classe),
    ])

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor("#00B4D8")
    c.drawString(margem, y, "Resultado")
    y -= 8 * mm
    c.setFillColor(cor)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margem + 5 * mm, y, f"{classe}  (IMC {imc:.2f})")
    y -= 9 * mm

    c.setFont("Helvetica", 11)
    c.setFillColor("#000000")
    c.drawString(margem + 5 * mm, y,
                 f"Faixa de peso recomendada para a altura: {p_min:.1f} kg a {p_max:.1f} kg")
    y -= 8 * mm

    if meta is not None:
        c.setFont("Helvetica", 11)
        c.drawString(margem + 5 * mm, y, f"Peso meta definido: {meta:.1f} kg")

    # Rodapé
    c.setFont("Helvetica", 9)
    c.setFillColor("#8A8F98")
    c.drawCentredString(largura / 2, 15 * mm,
                        "Classificação baseada nas diretrizes da OMS (adultos) e SBGG/OPAS (idosos).")

    c.save()
    return caminho


def gerar_pdf_grafico(caminho, nome, png_bytes):
    """Gera um PDF contendo o gráfico de evolução informado (bytes PNG)."""
    c = canvas.Canvas(caminho, pagesize=A4)
    largura, altura_pagina = A4
    margem = 20 * mm

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor("#00B4D8")
    c.drawString(margem, altura_pagina - 35 * mm, "Evolução do IMC")
    c.setFont("Helvetica", 12)
    c.setFillColor("#000000")
    c.drawString(margem, altura_pagina - 46 * mm, f"Paciente: {nome}")

    img = Image(io.BytesIO(png_bytes))
    img_w, img_h = img.imageWidth, img.imageHeight
    max_w = largura - 2 * margem
    escala = max_w / img_w
    img_w *= escala
    img_h *= escala

    x = (largura - img_w) / 2
    y = (altura_pagina - 70 * mm) - img_h
    img.drawOn(c, x, y)

    c.setFont("Helvetica", 9)
    c.setFillColor("#8A8F98")
    c.drawCentredString(largura / 2, 15 * mm,
                        "Gráfico da evolução do IMC ao longo das medições.")
    c.save()
    return caminho
