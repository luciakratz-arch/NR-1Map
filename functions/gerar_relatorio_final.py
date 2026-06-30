# -*- coding: utf-8 -*-
"""
NR-1 Map — Gerador do RELATÓRIO FINAL CONSOLIDADO (Laudo Técnico Psicossocial)
5º e último documento — reúne, por período, um resumo dos 4 instrumentos do fluxo GRO:
Inventário de Riscos + Avaliação do Risco + Plano de Ação 5W2H + Acompanhamento.

Este é o documento de capa, o que vai para o PGR como referência principal — os outros 4
continuam existindo como anexos técnicos detalhados. Aqui entra: fundamentação teórica,
metodologia, resumo executivo de cada instrumento, conclusão técnica e assinatura.
"""

import uuid
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER

# ───────────────────────────── CORES (mesma identidade NR-1 Map) ─────────────────────────────
VERDE_NR1 = colors.HexColor('#0A6E4F')
ROXO_NR1 = colors.HexColor('#7B00C4')
AZUL_ESCURO = colors.HexColor('#1F2937')
CINZA_TEXTO = colors.HexColor('#374151')
CINZA_CLARO = colors.HexColor('#F3F4F6')
LINHA = colors.HexColor('#D1D5DB')
VERDE_OK = colors.HexColor('#16A34A')
ZONA_COR_FUNDO = {
    "Sofrimento Patogênico": colors.HexColor('#FBD5D5'),
    "Defesa Oculta": colors.HexColor('#FFF1B8'),
    "Terreno Fértil": colors.HexColor('#D2F2E2'),
}
GRO_COR = {
    "TRIVIAL": colors.HexColor('#BFE6FB'),
    "TOLERÁVEL": colors.HexColor('#C8EAB8'),
    "MODERADO": colors.HexColor('#FCE98A'),
    "SUBSTANCIAL": colors.HexColor('#F8B25A'),
    "INTOLERÁVEL": colors.HexColor('#F08A8A'),
}

# ───────────────────────────── MATRIZ E ZONAS (idênticas aos instrumentos 2 e 3) ─────────────────────────────
MATRIZ_GRO = {
    ("E", 1): "MODERADO",     ("E", 2): "SUBSTANCIAL", ("E", 3): "SUBSTANCIAL", ("E", 4): "INTOLERÁVEL", ("E", 5): "INTOLERÁVEL",
    ("D", 1): "TOLERÁVEL",    ("D", 2): "MODERADO",     ("D", 3): "MODERADO",     ("D", 4): "SUBSTANCIAL", ("D", 5): "INTOLERÁVEL",
    ("C", 1): "TRIVIAL",      ("C", 2): "TOLERÁVEL",    ("C", 3): "MODERADO",     ("C", 4): "SUBSTANCIAL", ("C", 5): "INTOLERÁVEL",
    ("B", 1): "TRIVIAL",      ("B", 2): "TOLERÁVEL",    ("B", 3): "TOLERÁVEL",    ("B", 4): "MODERADO",     ("B", 5): "SUBSTANCIAL",
    ("A", 1): "TRIVIAL",      ("A", 2): "TRIVIAL",      ("A", 3): "TOLERÁVEL",    ("A", 4): "TOLERÁVEL",    ("A", 5): "MODERADO",
}
PROB_LETRA_POR_NUM = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}
ZONAS_IBP = [
    {"zona_dejours": "Sofrimento Patogênico", "faixa_ibp": "−5,0 a −1,5", "severidade": 4},
    {"zona_dejours": "Defesa Oculta", "faixa_ibp": "−1,4 a +1,4", "severidade": 3},
    {"zona_dejours": "Terreno Fértil", "faixa_ibp": "+1,5 a +5,0", "severidade": 1},
]


def zona_de(ibp):
    if ibp <= -1.5: return ZONAS_IBP[0]
    if ibp <= 1.4: return ZONAS_IBP[1]
    return ZONAS_IBP[2]


def probabilidade_de(qtd): return min(qtd + 1, 5)


def classificar(ibp, qtd):
    zona = zona_de(ibp)
    sev = zona["severidade"]
    letra = PROB_LETRA_POR_NUM[probabilidade_de(qtd)]
    return zona, sev, letra, MATRIZ_GRO[(letra, sev)]


def nome_arquivo_padrao(tipo_documento: str, empresa: str = None, ano: int = None) -> str:
    """Padrão: ANO_NR-1_Map_NomeDaEmpresa_TipoDoDocumento.pdf"""
    import unicodedata, re
    empresa = empresa or EMPRESA
    ano = ano or datetime.datetime.now().year
    slug = unicodedata.normalize('NFKD', empresa).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-zA-Z0-9]+', '', slug)
    return f"/mnt/user-data/outputs/{ano}_NR-1_Map_{slug}_{tipo_documento}.pdf"


# ───────────────────────────── DADOS (mesma base — empresa, setores, CBOs, ações, acompanhamento) ─────────────────────────────
EMPRESA = "Clínica Vida S.A."
REFERENCIA = "Junho de 2026"
COLABORADORES_ATIVOS = 142
RESPONDENTES_VALIDOS = 118

SETORES_CBO = [
    {"setor": "Operações / Linha A", "cbo": "7170", "cargo": "Operador de Linha de Produção", "n": 18, "ibp": -3.6, "qtd_perigos": 3},
    {"setor": "Operações / Linha A", "cbo": "8324", "cargo": "Auxiliar de Produção", "n": 7, "ibp": -2.8, "qtd_perigos": 2},
    {"setor": "Operações / Linha A", "cbo": "9412", "cargo": "Inspetor de Qualidade", "n": 3, "ibp": -3.0, "qtd_perigos": 2},
    {"setor": "Comercial / Vendas", "cbo": "3541", "cargo": "Representante Comercial", "n": 11, "ibp": -0.2, "qtd_perigos": 2},
    {"setor": "Comercial / Vendas", "cbo": "3542", "cargo": "Vendedor Interno", "n": 4, "ibp": 0.4, "qtd_perigos": 1},
    {"setor": "TI / Engenharia", "cbo": "2124", "cargo": "Analista de Sistemas", "n": 6, "ibp": 2.7, "qtd_perigos": 0},
    {"setor": "TI / Engenharia", "cbo": "3171", "cargo": "Técnico de Suporte", "n": 3, "ibp": 2.1, "qtd_perigos": 0},
    {"setor": "RH / Gestão de Pessoas", "cbo": "2524", "cargo": "Analista de RH", "n": 4, "ibp": -1.0, "qtd_perigos": 2},
    {"setor": "RH / Gestão de Pessoas", "cbo": "3514", "cargo": "Assistente de RH", "n": 2, "ibp": -1.6, "qtd_perigos": 3},
    {"setor": "Administrativo / Recepção", "cbo": "4110", "cargo": "Auxiliar Administrativo", "n": 8, "ibp": 1.0, "qtd_perigos": 0},
    {"setor": "Administrativo / Recepção", "cbo": "4221", "cargo": "Recepcionista", "n": 3, "ibp": 1.3, "qtd_perigos": 0},
    {"setor": "Manutenção", "cbo": "9517", "cargo": "Técnico de Manutenção", "n": 1, "ibp": -2.0, "qtd_perigos": 1},
]
MIN_RESPONDENTES = 3

ACOES_RESUMO = [
    {"nivel": "Operações/Linha A — Operador (CBO 7170)", "classif": "Intolerável", "status": "Em andamento", "ibp_antes": -3.6, "ibp_depois": -2.1},
    {"nivel": "RH/Gestão de Pessoas — Assistente (CBO 3514)", "classif": "Substancial", "status": "Pendente", "ibp_antes": -1.6, "ibp_depois": None},
    {"nivel": "Comercial/Vendas — Representante (CBO 3541)", "classif": "Substancial", "status": "Concluída", "ibp_antes": -0.2, "ibp_depois": 0.9},
]

# ───────────────────────────── ESTILOS ─────────────────────────────
styles = getSampleStyleSheet()
s_h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=15, textColor=VERDE_NR1, spaceAfter=4, fontName='Helvetica-Bold')
s_sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9.5, textColor=CINZA_TEXTO, spaceAfter=10)
s_h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11.5, textColor=ROXO_NR1, spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
s_body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, textColor=CINZA_TEXTO, leading=13)
s_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.2, textColor=CINZA_TEXTO, leading=11)
s_cell_bold = ParagraphStyle('cellb', parent=s_cell, fontName='Helvetica-Bold')
s_badge = ParagraphStyle('badge', parent=s_cell, fontName='Helvetica-Bold', textColor=colors.black, alignment=TA_CENTER)


def desenhar_cabecalho_rodape(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(CINZA_TEXTO)
    canvas_obj.drawString(20 * mm, h - 14 * mm, "[ LOGO PARCEIRO ]")
    canvas_obj.drawRightString(w - 20 * mm, h - 14 * mm, "[ LOGO DA EMPRESA ]")
    canvas_obj.setFont('Helvetica-Bold', 11)
    canvas_obj.setFillColor(VERDE_NR1)
    canvas_obj.drawCentredString(w / 2, h - 20 * mm, EMPRESA)
    canvas_obj.setFont('Helvetica', 8.5)
    canvas_obj.setFillColor(ROXO_NR1)
    canvas_obj.drawCentredString(w / 2, h - 25 * mm, "NR-1Map")
    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.setFillColor(AZUL_ESCURO)
    canvas_obj.drawCentredString(w / 2, h - 31 * mm, "RELATÓRIO FINAL CONSOLIDADO — LAUDO TÉCNICO PSICOSSOCIAL")
    canvas_obj.setStrokeColor(VERDE_NR1)
    canvas_obj.setLineWidth(1.2)
    canvas_obj.line(20 * mm, h - 34 * mm, w - 20 * mm, h - 34 * mm)
    canvas_obj.setFont('Helvetica', 7.5)
    canvas_obj.setFillColor(CINZA_TEXTO)
    canvas_obj.drawString(20 * mm, 12 * mm, "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
    canvas_obj.drawRightString(w - 20 * mm, 12 * mm, f"Página {doc.page}")
    canvas_obj.restoreState()


def gerar_relatorio_final(output_path=None):
    output_path = output_path or nome_arquivo_padrao("LaudoTecnicoFinal")
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=38 * mm, bottomMargin=20 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph("Relatório Final Consolidado — Laudo Técnico Psicossocial", s_h1))
    story.append(Paragraph(
        f"{EMPRESA} · Referência: {REFERENCIA} · Documento de capa para o PGR (NR-1) — "
        f"consolida os 4 instrumentos do fluxo GRO (Inventário, Avaliação, Plano de Ação e "
        f"Acompanhamento), anexados na íntegra como documentos técnicos detalhados.",
        s_sub
    ))

    # ── Ficha resumo ──
    ficha = [
        ["Empresa", EMPRESA],
        ["Período de referência", REFERENCIA],
        ["Colaboradores ativos", str(COLABORADORES_ATIVOS)],
        ["Respondentes válidos", f"{RESPONDENTES_VALIDOS} ({round(100*RESPONDENTES_VALIDOS/COLABORADORES_ATIVOS)}%)"],
        ["Metodologia", "Dejours (Psicodinâmica) · Herzberg (Fatores Higiênicos) · Maslow (Base da Pirâmide)"],
    ]
    t_ficha = Table(ficha, colWidths=[45 * mm, 124 * mm])
    t_ficha.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 0), (-1, -1), CINZA_TEXTO),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
        ('BACKGROUND', (0, 0), (0, -1), CINZA_CLARO),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ficha)
    story.append(Spacer(1, 5 * mm))

    # ── 1. Fundamentação ──
    story.append(Paragraph("1. Fundamentação Teórica", s_h2))
    story.append(Paragraph(
        "O presente laudo fundamenta-se em três correntes teóricas consolidadas: a Psicodinâmica do "
        "Trabalho de Christophe Dejours, que mede o equilíbrio entre Prazer e Sofrimento através do "
        "Índice de Balança Psicodinâmica (IBP); a Teoria dos Dois Fatores de Frederick Herzberg; e a "
        "Hierarquia de Necessidades de Maslow, aplicada à base da pirâmide. Esta abordagem está em "
        "conformidade com a NR-1, atualizada pela Portaria MTE nº 1.419/2024.",
        s_body
    ))
    story.append(Paragraph(
        "IBP = (Média_Likert − 3) × 2,5 — escala de −5 (Sofrimento Patogênico) a +5 (Terreno Fértil). "
        "A classificação oficial GRO (Trivial/Tolerável/Moderado/Substancial/Intolerável) é obtida pelo "
        "cruzamento Severidade × Probabilidade (metodologia AIHA/Fundacentro), sempre apresentada lado "
        "a lado com a zona Dejours.",
        s_body
    ))
    story.append(Spacer(1, 4 * mm))

    # ── 2. Resumo do Instrumento 1 (Inventário) ──
    story.append(Paragraph("2. Instrumento 1 — Inventário de Riscos (resumo)", s_h2))
    n_perigos = sum(min(c["qtd_perigos"], 1) and c["qtd_perigos"] for c in SETORES_CBO if c["n"] >= MIN_RESPONDENTES)
    total_perigos = sum(c["qtd_perigos"] for c in SETORES_CBO)
    story.append(Paragraph(
        f"Foram identificados <b>{total_perigos} perigos psicossociais</b> distribuídos entre os setores "
        f"avaliados, registrados no documento técnico anexo (Inventário de Riscos). Detalhamento completo "
        f"por perigo, subcategoria de origem e origem (pesquisa/manual) no anexo correspondente.",
        s_body
    ))
    story.append(Spacer(1, 4 * mm))

    # ── 3. Resumo do Instrumento 2 (Avaliação) — tabela por setor agregado ──
    story.append(Paragraph("3. Instrumento 2 — Avaliação do Risco (resumo por setor)", s_h2))
    setores_unicos = list(dict.fromkeys(c["setor"] for c in SETORES_CBO))
    header = ["Setor", "N", "Zona (IBP)", "Classificação Oficial (GRO)"]
    rows = [header]
    row_bg = []
    for i, setor_nome in enumerate(setores_unicos, start=1):
        itens = [c for c in SETORES_CBO if c["setor"] == setor_nome]
        n_total = sum(c["n"] for c in itens)
        ibp_medio = sum(c["ibp"] * c["n"] for c in itens) / n_total
        qtd_max = max(c["qtd_perigos"] for c in itens)
        zona, sev, letra, classif = classificar(ibp_medio, qtd_max)
        rows.append([
            Paragraph(setor_nome, s_cell_bold),
            Paragraph(str(n_total), s_cell),
            Paragraph(f"{zona['zona_dejours']} ({ibp_medio:+.1f})", s_badge),
            Paragraph(classif, s_badge),
        ])
        row_bg.append(('BACKGROUND', (2, i), (2, i), ZONA_COR_FUNDO[zona["zona_dejours"]]))
        row_bg.append(('BACKGROUND', (3, i), (3, i), GRO_COR[classif]))
    t_av = Table(rows, colWidths=[55 * mm, 18 * mm, 48 * mm, 48 * mm], repeatRows=1)
    t_av.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        *row_bg,
    ]))
    story.append(t_av)
    story.append(Paragraph(
        "Resultado individual por CBO (cargo), com trava de anonimato de mínimo 3 respondentes, no "
        "documento técnico anexo (Avaliação do Risco).", s_body
    ))
    story.append(Spacer(1, 4 * mm))

    # ── 4. Resumo do Instrumento 3 (Plano de Ação) ──
    story.append(Paragraph("4. Instrumento 3 — Plano de Ação 5W2H (resumo)", s_h2))
    header3 = ["Ação", "Classificação", "Status"]
    rows3 = [header3]
    for a in ACOES_RESUMO:
        rows3.append([
            Paragraph(a["nivel"], s_cell),
            Paragraph(a["classif"], s_badge),
            Paragraph(a["status"], s_cell_bold),
        ])
    t_acoes = Table(rows3, colWidths=[90 * mm, 35 * mm, 44 * mm], repeatRows=1)
    t_acoes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_acoes)
    story.append(Spacer(1, 4 * mm))

    # ── 5. Resumo do Instrumento 4 (Acompanhamento) ──
    story.append(Paragraph("5. Instrumento 4 — Acompanhamento (eficácia das ações)", s_h2))
    for a in ACOES_RESUMO:
        if a["ibp_depois"] is not None:
            delta = round(a["ibp_depois"] - a["ibp_antes"], 1)
            msg = "melhora comprovada" if delta > 0.3 else ("piora — revisar ação" if delta < -0.3 else "estável")
            story.append(Paragraph(
                f"• <b>{a['nivel']}</b>: IBP {a['ibp_antes']:+.1f} → {a['ibp_depois']:+.1f} "
                f"(Δ {delta:+.1f} — {msg})", s_body
            ))
        else:
            story.append(Paragraph(f"• <b>{a['nivel']}</b>: aguardando nova medição de IBP.", s_body))
    story.append(Spacer(1, 4 * mm))

    story.append(PageBreak())

    # ── 6. Conclusão ──
    story.append(Paragraph("6. Conclusão Técnica", s_h2))
    piores = sorted(setores_unicos, key=lambda s: sum(
        c["ibp"] * c["n"] for c in SETORES_CBO if c["setor"] == s
    ) / sum(c["n"] for c in SETORES_CBO if c["setor"] == s))
    pior_setor = piores[0]
    story.append(Paragraph(
        f"Diante dos dados consolidados nos 4 instrumentos do fluxo GRO, identifica-se a presença de "
        f"riscos psicossociais ocupacionais conforme previsto na NR-1, com destaque para o setor "
        f"<b>{pior_setor}</b>, que concentra a maior criticidade do período e já possui ação corretiva "
        f"em andamento (instrumentos 3 e 4 anexos). Recomenda-se a manutenção do ciclo de monitoramento "
        f"contínuo via Pesquisas Pulso semanais, em conformidade com o item 1.5.4.4.6 da norma, e a "
        f"reavaliação completa deste Relatório Final no próximo período de referência.",
        s_body
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "<b>Documentos anexos a este Relatório Final:</b> (1) Inventário de Riscos Psicossociais, "
        "(2) Avaliação do Risco — Mapa de Risco Psicossocial, (3) Plano de Ação 5W2H, "
        "(4) Acompanhamento — Evidências de Gestão Contínua.",
        s_body
    ))

    story.append(PageBreak())

    # ── Assinatura ──
    story.append(Paragraph("Assinatura e Validação", s_h2))
    story.append(Paragraph("✓ DOCUMENTO ASSINADO ELETRONICAMENTE", ParagraphStyle(
        'assinado', parent=s_body, textColor=VERDE_OK, fontName='Helvetica-Bold', fontSize=10)))
    story.append(Spacer(1, 3 * mm))
    agora = datetime.datetime.now(datetime.timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    hash_uuid = str(uuid.uuid4()).upper()
    sig_rows = [
        ["Aprovador:", "Dra. Lucia Kratz"],
        ["Registro Profissional:", "CRP 09/20590"],
        ["Data e Hora (UTC):", agora],
        ["Endereço IP de origem:", "187.45.22.10"],
        ["Hash UUID de Validação:", hash_uuid],
    ]
    t_sig = Table(sig_rows, colWidths=[45 * mm, 100 * mm])
    t_sig.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 0), (-1, -1), CINZA_TEXTO),
        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_sig)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Este registro é imutável e serve como homologação oficial para fiscalização trabalhista (NR-1).",
        s_body
    ))

    doc.build(story, onFirstPage=desenhar_cabecalho_rodape, onLaterPages=desenhar_cabecalho_rodape)
    print(f"Gerado: {output_path}")


if __name__ == "__main__":
    gerar_relatorio_final()
