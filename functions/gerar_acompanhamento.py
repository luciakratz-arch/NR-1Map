# -*- coding: utf-8 -*-
"""
NR-1 Map — Gerador do ACOMPANHAMENTO (Evidências de Gestão Contínua)
Instrumento 4 de 4 do fluxo GRO (Inventário > Avaliação > Plano de Ação > Acompanhamento)

Este é o documento que prova ao fiscal que as ações do Plano 5W2H (instrumento 3) realmente
aconteceram: mostra o status de cada ação, quem alterou e quando, e principalmente a
REMEDIÇÃO DO IBP — comparação entre a medição que gerou a ação (instrumento 2) e a medição
mais recente do mesmo setor/CBO, comprovando (ou não) a eficácia da intervenção.

Em produção, os dados de "status_log" vêm do painel ao vivo (painel.html → tela "Plano de
Ação"), onde cada mudança de status fica registrada com data/hora/usuário — esse PDF é só a
fotografia formal desse histórico, exportada para anexação ao PGR.
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
AMARELO_STATUS = colors.HexColor('#FFF1B8')
VERMELHO_STATUS = colors.HexColor('#FBD5D5')
VERDE_STATUS = colors.HexColor('#D2F2E2')

STATUS_COR = {
    "Concluída": VERDE_STATUS,
    "Em andamento": AMARELO_STATUS,
    "Pendente": VERMELHO_STATUS,
}

# ───────────────────────────── DADOS (mesma base de Setor/CBO dos instrumentos 2 e 3) ─────────────────────────────
EMPRESA = "Clínica Vida S.A."
REFERENCIA = "Ciclo: Junho → Julho de 2026"

# Cada item liga: ação do 5W2H + histórico de status (vindo do painel ao vivo) + IBP antes/depois
ACOMPANHAMENTO = [
    {
        "nivel": "Operações / Linha A — Operador de Linha (CBO 7170)",
        "classif_origem": "Intolerável",
        "status_atual": "Em andamento",
        "ibp_antes": -3.6,
        "ibp_depois": -2.1,
        "data_remedicao": "28/06/2026",
        "historico": [
            ("18/06/2026 09:14", "Gestor de RH", "Ação criada (Pendente)"),
            ("20/06/2026 14:02", "Gestor de RH", "Status alterado para Em andamento — Espaço de Fala Coletivo realizado"),
            ("28/06/2026 11:30", "Sistema (Pulso)", "Nova medição de IBP registrada: -2,1 (melhora de +1,5)"),
        ],
    },
    {
        "nivel": "RH / Gestão de Pessoas — Assistente de RH (CBO 3514)",
        "classif_origem": "Substancial",
        "status_atual": "Pendente",
        "ibp_antes": -1.6,
        "ibp_depois": None,
        "data_remedicao": None,
        "historico": [
            ("18/06/2026 09:20", "Gestor de RH", "Ação criada (Pendente)"),
        ],
    },
    {
        "nivel": "Comercial / Vendas — Representante Comercial (CBO 3541)",
        "classif_origem": "Substancial",
        "status_atual": "Concluída",
        "ibp_antes": -0.2,
        "ibp_depois": 0.9,
        "data_remedicao": "25/06/2026",
        "historico": [
            ("12/06/2026 08:40", "Liderança direta", "Ação criada (Pendente)"),
            ("19/06/2026 16:10", "Liderança direta", "Status alterado para Em andamento"),
            ("25/06/2026 10:05", "Liderança direta", "Status alterado para Concluída — Pesquisa Pulso direcionada finalizada"),
            ("25/06/2026 10:06", "Sistema (Pulso)", "Nova medição de IBP registrada: +0,9 (melhora de +1,1)"),
        ],
    },
]


def eficacia(ibp_antes, ibp_depois):
    if ibp_depois is None:
        return None, "Aguardando nova medição"
    delta = round(ibp_depois - ibp_antes, 1)
    if delta > 0.3:
        return delta, "Eficácia comprovada — melhora no IBP"
    if delta < -0.3:
        return delta, "Atenção — piora no IBP, revisar ação"
    return delta, "Estável — sem variação significativa ainda"


def nome_arquivo_padrao(tipo_documento: str, empresa: str = None, ano: int = None) -> str:
    """Padrão: ANO_NR-1_Map_NomeDaEmpresa_TipoDoDocumento.pdf"""
    import unicodedata, re
    empresa = empresa or EMPRESA
    ano = ano or datetime.datetime.now().year
    slug = unicodedata.normalize('NFKD', empresa).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-zA-Z0-9]+', '', slug)
    return f"/mnt/user-data/outputs/{ano}_NR-1_Map_{slug}_{tipo_documento}.pdf"


# ───────────────────────────── ESTILOS ─────────────────────────────
styles = getSampleStyleSheet()
s_h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=15, textColor=VERDE_NR1,
                       spaceAfter=4, fontName='Helvetica-Bold')
s_sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9.5, textColor=CINZA_TEXTO, spaceAfter=10)
s_h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11.5, textColor=ROXO_NR1,
                       spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
s_h3 = ParagraphStyle('h3', parent=styles['Heading3'], fontSize=10.5, textColor=AZUL_ESCURO,
                       spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')
s_body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, textColor=CINZA_TEXTO, leading=13)
s_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.3, textColor=CINZA_TEXTO, leading=11)
s_cell_bold = ParagraphStyle('cellb', parent=s_cell, fontName='Helvetica-Bold')
s_badge = ParagraphStyle('badge', parent=s_cell, fontName='Helvetica-Bold', textColor=colors.black,
                          alignment=TA_CENTER)


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
    canvas_obj.drawCentredString(w / 2, h - 31 * mm, "ACOMPANHAMENTO — EVIDÊNCIAS DE GESTÃO CONTÍNUA")

    canvas_obj.setStrokeColor(VERDE_NR1)
    canvas_obj.setLineWidth(1.2)
    canvas_obj.line(20 * mm, h - 34 * mm, w - 20 * mm, h - 34 * mm)

    canvas_obj.setFont('Helvetica', 7.5)
    canvas_obj.setFillColor(CINZA_TEXTO)
    canvas_obj.drawString(20 * mm, 12 * mm, "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
    canvas_obj.drawRightString(w - 20 * mm, 12 * mm, f"Página {doc.page}")
    canvas_obj.restoreState()


def gerar_acompanhamento(output_path=None):
    output_path = output_path or nome_arquivo_padrao("Acompanhamento")
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=38 * mm, bottomMargin=20 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph("Acompanhamento — Evidências de Gestão Contínua", s_h1))
    story.append(Paragraph(
        f"{EMPRESA} · {REFERENCIA} · Documento para anexação ao PGR (NR-1) — "
        f"4º instrumento do fluxo GRO (Inventário → Avaliação → Plano de Ação → <b>Acompanhamento</b>)",
        s_sub
    ))
    story.append(Paragraph(
        "Este documento comprova o monitoramento das ações do Plano 5W2H (instrumento 3), conforme item "
        "1.5.4.4.6 da NR-1, que exige evidência de gestão contínua. Para cada ação, registra-se o "
        "histórico de status (com data e responsável) e a <b>remedição do IBP</b> — comparação entre a "
        "medição que originou a ação e a medição mais recente do mesmo setor/CBO, comprovando a eficácia "
        "da intervenção.",
        s_body
    ))
    story.append(Spacer(1, 5 * mm))

    for i, item in enumerate(ACOMPANHAMENTO, start=1):
        story.append(Paragraph(f"Ação {i} — {item['nivel']}", s_h3))

        delta, msg_eficacia = eficacia(item["ibp_antes"], item["ibp_depois"])
        depois_txt = f"{item['ibp_depois']:+.1f}" if item["ibp_depois"] is not None else "—"
        delta_txt = f"{delta:+.1f}" if delta is not None else "—"

        # Badge de status + remedição IBP
        badge_row = [
            Paragraph(f"Status: {item['status_atual']}", s_badge),
            Paragraph(f"Origem: {item['classif_origem']}", s_badge),
            Paragraph(f"IBP antes: {item['ibp_antes']:+.1f}", s_badge),
            Paragraph(f"IBP depois: {depois_txt}", s_badge),
            Paragraph(f"Δ {delta_txt}", s_badge),
        ]
        t_badge = Table([badge_row], colWidths=[35.8 * mm] * 5)
        t_badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), STATUS_COR.get(item["status_atual"], CINZA_CLARO)),
            ('BACKGROUND', (1, 0), (1, 0), CINZA_CLARO),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#FBD5D5')),
            ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#D2F2E2') if item["ibp_depois"] is not None else CINZA_CLARO),
            ('BACKGROUND', (4, 0), (4, 0), colors.HexColor('#D2F2E2') if (delta or 0) > 0 else CINZA_CLARO),
            ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_badge)
        story.append(Spacer(1, 1.5 * mm))
        story.append(Paragraph(f"<i>{msg_eficacia}</i>", s_body))
        story.append(Spacer(1, 2 * mm))

        # Histórico (linha do tempo)
        hist_rows = [["Data/Hora", "Responsável", "Evento"]]
        for data, resp, evento in item["historico"]:
            hist_rows.append([
                Paragraph(data, s_cell),
                Paragraph(resp, s_cell),
                Paragraph(evento, s_cell),
            ])
        t_hist = Table(hist_rows, colWidths=[32 * mm, 32 * mm, 110 * mm])
        t_hist.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL_ESCURO),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_hist)
        story.append(Spacer(1, 7 * mm))

    story.append(Paragraph(
        "<b>Nota de coerência (item verificado pela fiscalização):</b> toda ação registrada no instrumento "
        "3 (Plano de Ação) deve aparecer aqui com seu histórico de status. Ações concluídas com remedição "
        "positiva do IBP encerram o ciclo daquele perigo; ações sem melhora (Δ negativo ou nulo) devem ser "
        "revisadas e podem gerar uma nova ação no próximo ciclo do Plano 5W2H.",
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
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
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
    gerar_acompanhamento()
