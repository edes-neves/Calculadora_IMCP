import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image


def _quebrar_linhas(texto, canvas, largura_util):
    """Quebra um texto longo em várias linhas respeitando a largura disponível."""
    palavras = texto.split()
    linhas, atual = [], ""
    for pal in palavras:
        teste = f"{atual} {pal}".strip()
        if canvas.stringWidth(teste, "Helvetica", 10.5) <= largura_util:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = pal
    if atual:
        linhas.append(atual)
    return linhas


def _gerar_recomendacao(classe, saude, p_min, p_max):
    """Monta uma recomendação personalizada com base na classificação e nas medidas."""
    texto = (f"Recomenda-se manter o peso dentro da faixa ideal de "
             f"{p_min:.1f} kg a {p_max:.1f} kg, aliado a alimentação equilibrada "
             f"e atividade física regular.")
    if saude:
        _, _, _, cintura, quadril, _g, rcq, risco = saude
        if risco == "Elevado":
            texto += (" Atenção: a circunferência da cintura indica risco cardiovascular "
                      "elevado; considere o acompanhamento de um profissional de saúde.")
        elif risco == "Moderado":
            texto += (" A circunferência da cintura indica risco cardiovascular moderado; "
                      "é recomendável acompanhar a medida e melhorar hábitos.")
        if rcq is not None:
            if rcq >= 0.90:
                texto += " O excesso de gordura abdominal (RCQ) merece atenção."
            elif rcq <= 0.80 and _g is not None:
                texto += " O perfil de gordura corporal está adequado."
    if "Abaixo do Peso" in classe or "Baixo Peso" in classe:
        texto += (" Seu IMC está abaixo do recomendado; busque um plano nutricional "
                  "para ganho de peso saudável.")
    elif "Sobrepeso" in classe:
        texto += (" O sobrepeso aumenta o risco de doenças crônicas; a perda moderada "
                  "de peso já traz benefícios significativos.")
    elif "Obesidade" in classe:
        texto += (" O quadro de obesidade deve ser acompanhado por profissionais de "
                  "saúde para um plano de redução de peso seguro.")
    else:
        texto += " Mantenha os bons hábitos para conservar o estado atual."
    return texto


def gerar_pdf_relatorio(caminho, nome, idade, genero, peso, altura, imc, classe,
                        p_min, p_max, cor="#333333", meta=None, data=None, saude=None,
                        nutricional=None):
    """Gera um PDF com o resultado da medição e salva no caminho informado.

    ``saude`` é opcional e deve ser uma tupla na ordem retornada por
    ``Database.buscar_ultima_medicao_detalhada``:
    (peso, altura, imc, cintura_cm, quadril_cm, gordura_pct, rcq, risco_cintura).

    ``nutricional`` é opcional e segue ``Database.buscar_ultimo_nutricional``:
    (tmb_mifflin, tmb_harris, fator_atividade, metodo_tmb, get_total, data_registro).
    """
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

    if saude:
        _, _, _, cintura, quadril, gordura, rcq, risco = saude
        linhas = []
        if cintura is not None:
            linhas.append(("Cintura", f"{cintura:.0f} cm"))
        if quadril is not None:
            linhas.append(("Quadril", f"{quadril:.0f} cm"))
        if gordura is not None:
            linhas.append(("Gordura corporal (estimada)", f"{gordura:.1f}%"))
        if rcq is not None:
            linhas.append(("RCQ", f"{rcq:.2f}"))
        if risco is not None:
            linhas.append(("Risco (circ. cintura)", risco))
        if linhas:
            bloco("Composição corporal", linhas)

    # Bloco de gasto energético (TMB e GET) quando disponível
    if nutricional:
        tmb_miff, tmb_har, fator, metodo, _get_total, _data_nutri = nutricional
        linhas = []
        if tmb_miff is not None:
            linhas.append(("TMB (Mifflin-St Jeor)", f"{tmb_miff:.0f} kcal/dia"))
        if tmb_har is not None:
            linhas.append(("TMB (Harris-Benedict)", f"{tmb_har:.0f} kcal/dia"))
        if fator is not None and _get_total is not None:
            linhas.append(("Fator de atividade", f"{fator:.2f}"))
            linhas.append(("GET", f"{_get_total:.0f} kcal/dia"))
        if linhas:
            bloco("Gasto Energético", linhas)

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

    # Recomendação personalizada
    recomendacao = _gerar_recomendacao(classe, saude, p_min, p_max)
    if recomendacao:
        y -= 12 * mm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor("#00B4D8")
        c.drawString(margem, y, "Recomendações")
        y -= 8 * mm
        c.setFont("Helvetica", 10.5)
        c.setFillColor("#000000")
        # Quebra o texto em várias linhas respeitando a largura útil
        largura_util = (largura - 2 * margem - 10 * mm)
        linhas_texto = _quebrar_linhas(recomendacao, c, largura_util)
        for lin in linhas_texto:
            c.drawString(margem + 5 * mm, y, lin)
            y -= 6 * mm

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
