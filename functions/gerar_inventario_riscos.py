# -*- coding: utf-8 -*-
"""
NR-1 Map — Gerador do INVENTÁRIO DE RISCOS
Instrumento 1 de 4 do fluxo GRO (Inventário > Avaliação > Plano de Ação > Acompanhamento)

Mantém o MESMO padrão visual já aprovado nos 3 documentos existentes:
- Cabeçalho com [LOGO PARCEIRO] [LOGO EMPRESA] + nome empresa + "NR-1Map" + título do documento
- Rodapé "NR-1 Map · Conformidade Portaria MTE 1.419/2024 · Página N"
- Bloco final de Assinatura e Validação com rastro digital (UUID, IP, UTC)

Regra de ouro do projeto: o conceito próprio da Lucia (IBP / Dejours: Sofrimento
Patogênico, Defesa Oculta, Terreno Fértil) SEMPRE aparece, mas sempre adaptado e
colocado lado a lado com o termo técnico oficial da norma/GRO.

NOTA DE INTEGRAÇÃO: hoje os dados (setores, perigos, IBP) estão fixos como exemplo
(empresa "Clínica Vida S.A."), igual aos 3 documentos anteriores — assim como eles,
este gerador também precisa futuramente ser conectado a dados reais do Firestore.
"""

import uuid
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ───────────────────────────── CORES (identidade oficial NR-1 Map: verde + roxo) ─────────────────────────────
VERDE_NR1 = colors.HexColor('#0A6E4F')      # verde institucional NR-1 Map
ROXO_NR1 = colors.HexColor('#7B00C4')       # roxo institucional NR-1 Map
VERDE_CLARO = colors.HexColor('#E6F4EF')    # fundo suave para faixas/realces
ROXO_CLARO = colors.HexColor('#F3E8FB')     # fundo suave para realces secundários
AZUL_ESCURO = colors.HexColor('#1F2937')
CINZA_TEXTO = colors.HexColor('#374151')
CINZA_CLARO = colors.HexColor('#F3F4F6')
LINHA = colors.HexColor('#D1D5DB')
VERDE_OK = colors.HexColor('#16A34A')
AMARELO = colors.HexColor('#FACC15')
LARANJA = colors.HexColor('#F97316')
VERMELHO = colors.HexColor('#DC2626')
AZUL_CLARO = colors.HexColor('#7DD3FC')  # nível "Trivial" — escala oficial AIHA

# Cores de fundo (badge) por Zona Dejours — usadas na legenda e na tabela de perigos
ZONA_COR_FUNDO = {
    "Sofrimento Patogênico": colors.HexColor('#FBD5D5'),  # vermelho claro
    "Defesa Oculta": colors.HexColor('#FFF1B8'),           # amarelo claro
    "Terreno Fértil": colors.HexColor('#D2F2E2'),          # verde claro
}

# ───────────────────────────── ZONAS — IBP (Dejours) × OFICIAL (GRO) ─────────────────────────────
# Conversão oficial: zona Dejours -> faixa de Severidade média do setor (a Probabilidade
# vem da recorrência de respostas críticas no Pulso Semanal, conforme combinado).
ZONAS_IBP = [
    {
        "zona_dejours": "Sofrimento Patogênico",
        "faixa_ibp": "−5,0 a −1,5",
        "severidade_oficial": "4 a 5 (Maior / Extrema)",
        "status_oficial": "Risco Crítico — exige ação imediata conforme GRO/NR-1",
    },
    {
        "zona_dejours": "Defesa Oculta",
        "faixa_ibp": "−1,4 a +1,4",
        "severidade_oficial": "2 a 3 (Menor / Moderada)",
        "status_oficial": "Alerta — risco de Burnout mascarado, exige monitoramento",
    },
    {
        "zona_dejours": "Terreno Fértil",
        "faixa_ibp": "+1,5 a +5,0",
        "severidade_oficial": "1 (Leve)",
        "status_oficial": "Ambiente psicologicamente seguro",
    },
]

# ───────────────────────────── DADOS DE EXEMPLO (mesma empresa dos outros 3 docs) ─────────────────────────────
EMPRESA = "Clínica Vida S.A."
REFERENCIA = "Junho de 2026"

# Cada perigo nasce de uma resposta crítica (nota baixa) nas 101 perguntas oficiais,
# agrupado por subcategoria. origem="pesquisa" = veio automático da nota Likert.
# origem="manual" = foi adicionado manualmente pelo RH/Parceiro (perigo não-psicossocial
# ou não capturado pelas 101 perguntas, ex: observação de campo).
INVENTARIO = [
    {
        "setor": "Operações / Linha A",
        "ibp": -3.4,
        "perigos": [
            {"perigo": "Sobrecarga de trabalho / ritmo acelerado", "subcategoria": "1.1 Ritmo de Trabalho, Cadência e Pressão de Tempo", "origem": "pesquisa"},
            {"perigo": "Pressão por metas com prazos pouco realistas", "subcategoria": "1.1 Ritmo de Trabalho, Cadência e Pressão de Tempo", "origem": "pesquisa"},
            {"perigo": "Ausência de pausas regulares de descompressão", "subcategoria": "1.2 Limitações Biológicas, Pausas e Espaços de Descompressão", "origem": "pesquisa"},
        ],
    },
    {
        "setor": "Comercial / Vendas",
        "ibp": 0.0,
        "perigos": [
            {"perigo": "Ativismo / horas extras ocultas não comunicadas à liderança", "subcategoria": "1.3 Stresse, Ansiedade e Esgotamento Psicossomático", "origem": "pesquisa"},
            {"perigo": "Defesa coletiva mascarando sinais individuais de sofrimento", "subcategoria": "3.4 Reconhecimento e Julgamento de Valor", "origem": "pesquisa"},
        ],
    },
    {
        "setor": "RH / Gestão de Pessoas",
        "ibp": -1.2,
        "perigos": [
            {"perigo": "Sobrecarga emocional por exposição constante a casos sensíveis", "subcategoria": "1.3 Stresse, Ansiedade e Esgotamento Psicossomático", "origem": "pesquisa"},
            {"perigo": "Falta de supervisão de pares / espaço de fala estruturado", "subcategoria": "2.3 Segurança Psicológica e Direito ao Erro", "origem": "pesquisa"},
            {"perigo": "Iluminação inadequada na sala de atendimento individual", "subcategoria": "Observação de campo (não-psicossocial)", "origem": "manual"},
        ],
    },
    {
        "setor": "TI / Engenharia",
        "ibp": 2.5,
        "perigos": [],
    },
    {
        "setor": "Administrativo / Recepção",
        "ibp": 1.1,
        "perigos": [],
    },
]


def zona_de(ibp: float) -> dict:
    if ibp <= -1.5:
        return ZONAS_IBP[0]
    if ibp <= 1.4:
        return ZONAS_IBP[1]
    return ZONAS_IBP[2]


# ───────────────────────────── ESTILOS ─────────────────────────────
styles = getSampleStyleSheet()
s_h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=15, textColor=VERDE_NR1,
                       spaceAfter=4, fontName='Helvetica-Bold')
s_sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9.5, textColor=CINZA_TEXTO,
                        spaceAfter=10)
s_h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11.5, textColor=ROXO_NR1,
                       spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
s_body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, textColor=CINZA_TEXTO,
                         leading=13)
s_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.3, textColor=CINZA_TEXTO,
                         leading=11)
s_cell_bold = ParagraphStyle('cellb', parent=s_cell, fontName='Helvetica-Bold')
s_legend = ParagraphStyle('legend', parent=styles['Normal'], fontSize=8, textColor=CINZA_TEXTO,
                           leading=12)


# ───────────────────────────── CABEÇALHO / RODAPÉ (idêntico aos outros 3 docs) ─────────────────────────────
def desenhar_cabecalho_rodape(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4

    # Cabeçalho
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
    canvas_obj.drawCentredString(w / 2, h - 31 * mm, "INVENTÁRIO DE RISCOS PSICOSSOCIAIS")

    canvas_obj.setStrokeColor(VERDE_NR1)
    canvas_obj.setLineWidth(1.2)
    canvas_obj.line(20 * mm, h - 34 * mm, w - 20 * mm, h - 34 * mm)

    # Rodapé
    canvas_obj.setFont('Helvetica', 7.5)
    canvas_obj.setFillColor(CINZA_TEXTO)
    canvas_obj.drawString(20 * mm, 12 * mm,
                           "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
    canvas_obj.drawRightString(w - 20 * mm, 12 * mm, f"Página {doc.page}")

    canvas_obj.restoreState()


# ───────────────────────────── MONTAGEM DO DOCUMENTO ─────────────────────────────
def gerar_inventario(output_path="/mnt/user-data/outputs/nr1map-inventario-riscos.pdf"):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=38 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    story = []

    story.append(Paragraph("Inventário de Riscos Psicossociais", s_h1))
    story.append(Paragraph(
        f"{EMPRESA} · Referência: {REFERENCIA} · Documento para anexação ao PGR (NR-1) — "
        f"1º instrumento do fluxo GRO (Inventário → Avaliação → Plano de Ação → Acompanhamento)",
        s_sub
    ))
    story.append(Paragraph(
        "Este Inventário registra os perigos psicossociais identificados por setor, conforme item "
        "1.5.4.4.1 da NR-1 (Portaria MTE 1.419/2024), que exige o registro dos perigos antes da etapa "
        "de Avaliação do Risco. Os perigos têm duas origens possíveis: gerados automaticamente a partir de "
        "respostas críticas das 101 perguntas oficiais do Diagnóstico NR-1 Map (escala Likert), ou inseridos "
        "manualmente pelo RH/Parceiro quando observados em campo e não capturados pela pesquisa.",
        s_body
    ))
    story.append(Spacer(1, 4 * mm))

    # ── Legenda de zonas (IBP/Dejours lado a lado com severidade oficial) ──
    story.append(Paragraph("Correspondência: Zona Dejours (IBP) × Severidade Oficial (GRO)", s_h2))
    s_cell_header = ParagraphStyle('cellh', parent=s_cell, fontName='Helvetica-Bold',
                                    textColor=colors.white, fontSize=8.3)
    s_zona_dejours = ParagraphStyle('zonad', parent=s_cell_bold, textColor=colors.black,
                                     alignment=TA_CENTER)

    legend_rows = [[
        Paragraph("Zona (IBP/Dejours)", s_cell_header),
        Paragraph("Faixa de IBP", s_cell_header),
        Paragraph("Severidade Oficial Correspondente", s_cell_header),
        Paragraph("Status", s_cell_header),
    ]]
    for z in ZONAS_IBP:
        legend_rows.append([
            Paragraph(z["zona_dejours"], s_zona_dejours),
            Paragraph(z["faixa_ibp"], s_cell),
            Paragraph(z["severidade_oficial"], s_cell),
            Paragraph(z["status_oficial"], s_cell),
        ])
    t_legend = Table(legend_rows, colWidths=[34 * mm, 22 * mm, 44 * mm, 70 * mm])
    legend_zone_bg = [
        ('BACKGROUND', (0, i), (0, i), ZONA_COR_FUNDO[z["zona_dejours"]])
        for i, z in enumerate(ZONAS_IBP, start=1)
    ]
    t_legend.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        *legend_zone_bg,
    ]))
    story.append(t_legend)
    story.append(Spacer(1, 6 * mm))

    # ── Inventário por setor ──
    story.append(Paragraph("Perigos Identificados por Setor", s_h2))

    header = ["Setor", "Perigo Identificado", "Subcategoria de Origem", "Origem", "Zona (IBP)"]
    rows = [header]
    span_commands = []  # (col, row_start, row_end) a mesclar
    zona_bg_commands = []  # fundo colorido por zona, célula a célula
    current_row = 1
    for setor in INVENTARIO:
        zona = zona_de(setor["ibp"])
        zona_cell = Paragraph(f"{zona['zona_dejours']}<br/>({setor['ibp']:+.1f})", s_zona_dejours)
        if not setor["perigos"]:
            rows.append([
                Paragraph(setor["setor"], s_cell_bold),
                Paragraph("Nenhum perigo crítico identificado neste ciclo.", s_cell),
                "—", "—",
                zona_cell,
            ])
            zona_bg_commands.append(('BACKGROUND', (4, current_row), (4, current_row),
                                      ZONA_COR_FUNDO[zona["zona_dejours"]]))
            current_row += 1
            continue

        row_start = current_row
        for p in setor["perigos"]:
            origem_label = "Pesquisa (auto)" if p["origem"] == "pesquisa" else "Manual (RH/Parceiro)"
            rows.append([
                Paragraph(setor["setor"], s_cell_bold),
                Paragraph(p["perigo"], s_cell),
                Paragraph(p["subcategoria"], s_cell),
                Paragraph(origem_label, s_cell),
                zona_cell,
            ])
            current_row += 1
        row_end = current_row - 1
        zona_bg_commands.append(('BACKGROUND', (4, row_start), (4, row_end),
                                  ZONA_COR_FUNDO[zona["zona_dejours"]]))
        if row_end > row_start:
            span_commands.append(('SPAN', (0, row_start), (0, row_end)))
            span_commands.append(('SPAN', (4, row_start), (4, row_end)))

    t_inv = Table(rows, colWidths=[28 * mm, 48 * mm, 42 * mm, 26 * mm, 26 * mm], repeatRows=1)
    t_inv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (1, 1), (3, -1), [colors.white, CINZA_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        *span_commands,
        *zona_bg_commands,
    ]))
    story.append(t_inv)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(
        "<b>Nota de coerência (item verificado pela fiscalização):</b> todo perigo listado neste "
        "Inventário deve necessariamente aparecer classificado na etapa seguinte — Avaliação do Risco "
        "(Mapa de Risco) — com sua respectiva Severidade × Probabilidade. Nenhum perigo pode ser "
        "tratado no Plano de Ação sem antes constar neste Inventário.",
        s_body
    ))

    story.append(PageBreak())

    # ── Assinatura e validação (idêntico padrão dos outros 3 docs) ──
    story.append(Paragraph("Assinatura e Validação", s_h2))
    story.append(Paragraph("✓ DOCUMENTO ASSINADO ELETRONICAMENTE", ParagraphStyle(
        'assinado', parent=s_body, textColor=VERDE_OK, fontName='Helvetica-Bold', fontSize=10
    )))
    story.append(Spacer(1, 3 * mm))

    agora = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S UTC")
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
    gerar_inventario()
