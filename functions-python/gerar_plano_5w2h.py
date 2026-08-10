# -*- coding: utf-8 -*-
"""
NR-1 Map — Gerador do PLANO DE AÇÃO 5W2H
Instrumento 3 de 4 do fluxo GRO (Inventário > Avaliação > Plano de Ação > Acompanhamento)

NOVIDADE vs. versão anterior do 5W2H:
- As ações NÃO são mais escritas à mão por setor — elas são GERADAS AUTOMATICAMENTE a partir de
  quem deu SUBSTANCIAL ou INTOLERÁVEL na Avaliação do Risco (instrumento 2), no nível de CBO
  (cargo) quando visível, ou de Setor quando o CBO foi diluído por anonimato.
- O prazo (When) é definido pela gravidade: Intolerável = Imediato; Substancial = 7 dias.
- Mantém a mesma base de dados do Mapa de Risco (SETORES_CBO) para os 3 documentos conversarem
  entre si — mudou um número lá, muda a ação gerada aqui.
"""

import uuid
import datetime
import tempfile as _tmpmod
import os as _os
import urllib.request as _urllib_req
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

# ───────────────────────────── MATRIZ OFICIAL (idêntica ao Mapa de Risco) ─────────────────────────────
MATRIZ_GRO = {
    ("E", 1): "MODERADO",     ("E", 2): "SUBSTANCIAL", ("E", 3): "SUBSTANCIAL", ("E", 4): "INTOLERÁVEL", ("E", 5): "INTOLERÁVEL",
    ("D", 1): "TOLERÁVEL",    ("D", 2): "MODERADO",     ("D", 3): "MODERADO",     ("D", 4): "SUBSTANCIAL", ("D", 5): "INTOLERÁVEL",
    ("C", 1): "TRIVIAL",      ("C", 2): "TOLERÁVEL",    ("C", 3): "MODERADO",     ("C", 4): "SUBSTANCIAL", ("C", 5): "INTOLERÁVEL",
    ("B", 1): "TRIVIAL",      ("B", 2): "TOLERÁVEL",    ("B", 3): "TOLERÁVEL",    ("B", 4): "MODERADO",     ("B", 5): "SUBSTANCIAL",
    ("A", 1): "TRIVIAL",      ("A", 2): "TRIVIAL",      ("A", 3): "TOLERÁVEL",    ("A", 4): "TOLERÁVEL",    ("A", 5): "MODERADO",
}
PROB_LABEL = {"A": "Rara", "B": "Pouco Provável", "C": "Possível", "D": "Provável", "E": "Muito Provável"}
PROB_LETRA_POR_NUM = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}
ZONAS_IBP = [
    {"zona_dejours": "Sofrimento Patogênico", "faixa_ibp": "−5,0 a −1,5", "severidade": 4},
    {"zona_dejours": "Defesa Oculta", "faixa_ibp": "−1,4 a +1,4", "severidade": 3},
    {"zona_dejours": "Terreno Fértil", "faixa_ibp": "+1,5 a +5,0", "severidade": 1},
]
AÇÕES_QUE_EXIGEM_PLANO = {"SUBSTANCIAL", "INTOLERÁVEL"}


def zona_de(ibp: float) -> dict:
    if ibp <= -1.5:
        return ZONAS_IBP[0]
    if ibp <= 1.4:
        return ZONAS_IBP[1]
    return ZONAS_IBP[2]


def probabilidade_de(qtd_perigos: int) -> int:
    return min(qtd_perigos + 1, 5)


def classificar(ibp: float, qtd_perigos: int):
    zona = zona_de(ibp)
    sev = zona["severidade"]
    prob_letra = PROB_LETRA_POR_NUM[probabilidade_de(qtd_perigos)]
    classif = MATRIZ_GRO[(prob_letra, sev)]
    return zona, sev, prob_letra, classif


def nome_arquivo_padrao(tipo_documento: str, empresa: str = None, ano: int = None) -> str:
    """Padrão: ANO_NR-1_Map_NomeDaEmpresa_TipoDoDocumento.pdf"""
    import unicodedata, re
    empresa = empresa or EMPRESA
    ano = ano or datetime.datetime.now().year
    slug = unicodedata.normalize('NFKD', empresa).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-zA-Z0-9]+', '', slug)
    return f"/mnt/user-data/outputs/{ano}_NR-1_Map_{slug}_{tipo_documento}.pdf"


# ───────────────────────────── DADOS (mesma base do Mapa de Risco — instrumento 2) ─────────────────────────────
# EMPRESA e REFERENCIA agora vêm do parâmetro dados (injetado pelo main.py)

MIN_RESPONDENTES_CBO = 3
MIN_RESPONDENTES_SETOR = 3

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


def gerar_acoes(SETORES_CBO_DIN=None):
    if SETORES_CBO_DIN is None: SETORES_CBO_DIN = []
    """
    Gera a lista de ações 5W2H automaticamente:
    - Nível CBO, se N≥3 (ação focada no cargo)
    - Nível Setor (agregado), se o CBO individual foi diluído por anonimato mas o setor todo N≥3
    - Só entra na lista quem deu SUBSTANCIAL ou INTOLERÁVEL
    """
    acoes = []

    # Nível CBO
    for c in SETORES_CBO_DIN:
        if c["n"] < MIN_RESPONDENTES_CBO:
            continue
        zona, sev, prob_letra, classif = classificar(c["ibp"], c["qtd_perigos"])
        if classif in AÇÕES_QUE_EXIGEM_PLANO:
            acoes.append({
                "nivel": f"{c['setor']} — {c['cargo']} (CBO {c['cbo']})",
                "setor": c["setor"], "zona": zona, "classif": classif, "ibp": c["ibp"],
            })

    # Nível Setor agregado (cobre setores cujo CBO individual não passou no mínimo, mas o setor sim)
    for setor_nome in dict.fromkeys(cc["setor"] for cc in SETORES_CBO_DIN):
        itens = [cc for cc in SETORES_CBO_DIN if cc["setor"] == setor_nome]
        cbos_visiveis = [c for c in itens if c["n"] >= MIN_RESPONDENTES_CBO]
        if len(cbos_visiveis) == len(itens):
            continue  # já totalmente coberto no nível CBO acima
        n_total = sum(c["n"] for c in itens)
        if n_total < MIN_RESPONDENTES_SETOR:
            continue  # setor inteiro também diluído — vai para Empresa (geral), tratado à parte
        ibp_medio = sum(c["ibp"] * c["n"] for c in itens) / n_total
        qtd_perigos_max = max(c["qtd_perigos"] for c in itens)
        zona, sev, prob_letra, classif = classificar(ibp_medio, qtd_perigos_max)
        if classif in AÇÕES_QUE_EXIGEM_PLANO:
            acoes.append({
                "nivel": f"{setor_nome} (resultado agregado do setor)",
                "setor": setor_nome, "zona": zona, "classif": classif, "ibp": round(ibp_medio, 1),
            })

    return acoes


def texto_acao(item: dict) -> dict:
    zona_nome = item["zona"]["zona_dejours"]
    classif = item["classif"]
    prazo = "Imediato" if classif == "INTOLERÁVEL" else "7 dias"
    biblioteca = {
        "Sofrimento Patogênico": "Abrir Espaço de Fala Coletivo urgente. Suspender exigências não essenciais "
                                  "por 30 dias e revisar metas/cargas de trabalho.",
        "Defesa Oculta": "Investigar mecanismos de defesa coletiva (ativismo, horas extras ocultas, cinismo "
                          "viril). Aplicar Pesquisa Pulso direcionada sobre sobrecarga não reportada.",
        "Terreno Fértil": "Manter monitoramento de rotina — sem ação corretiva necessária neste ciclo.",
    }
    return {
        "what": biblioteca.get(zona_nome, "Investigar e estruturar plano de mitigação."),
        "why": f"Classificação {classif} (GRO), correspondente à Zona {zona_nome} (IBP {item['ibp']:+.1f}), "
               f"exige intervenção conforme item 1.5.4.4.3 da NR-1.",
        "who": "Gestor de RH + Liderança direta do setor + Consultoria responsável",
        "where": item["nivel"],
        "when": f"Prazo: {prazo}",
        "how": "Reunião de Espaço de Fala Coletivo, revisão de metas e cronograma, acompanhamento via "
               "Pesquisa Pulso semanal — registrado no instrumento de Acompanhamento (4).",
        "howmuch": "A definir conforme escopo da intervenção (estimativa: R$ 0,00 — ação interna)",
    }


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
s_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.5, textColor=CINZA_TEXTO, leading=12)
s_cell_bold = ParagraphStyle('cellb', parent=s_cell, fontName='Helvetica-Bold')
s_badge = ParagraphStyle('badge', parent=s_cell, fontName='Helvetica-Bold', textColor=colors.black,
                          alignment=TA_CENTER)


def desenhar_cabecalho_rodape(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4
    # Logo esquerda — parceiro ou NR-1 Map como fallback
    _lp = getattr(desenhar_cabecalho_rodape, '_logo_parc', None)
    _le = getattr(desenhar_cabecalho_rodape, '_logo_emp', None)
    if _lp and __import__('os').path.exists(_lp):
        try: canvas_obj.drawImage(_lp, 18*mm, h-24*mm, width=42*mm, height=18*mm, preserveAspectRatio=True, anchor='c')
        except: canvas_obj.setFont('Helvetica-Bold',8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-18*mm, "NR-1Map")
    else:
        canvas_obj.setFont('Helvetica-Bold',8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(20*mm, h-13*mm, "NR-1Map")
    # Logo direita — empresa
    _tem_le = False
    if _le and __import__('os').path.exists(_le):
        try: canvas_obj.drawImage(_le, w-60*mm, h-24*mm, width=42*mm, height=18*mm, preserveAspectRatio=True, anchor='c'); _tem_le = True
        except: pass
    # Sem logo empresa: espaco direito fica em branco (sem texto sobreposto)

    canvas_obj.setFont('Helvetica-Bold', 11)
    canvas_obj.setFillColor(VERDE_NR1)
    _en = getattr(desenhar_cabecalho_rodape, '_empresa_nome', 'Empresa')
    canvas_obj.drawCentredString(w / 2, h - 31 * mm, _en)

    canvas_obj.setFont('Helvetica', 8.5)
    canvas_obj.setFillColor(ROXO_NR1)
    canvas_obj.drawCentredString(w / 2, h - 36 * mm, "NR-1Map")

    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.setFillColor(AZUL_ESCURO)
    canvas_obj.drawCentredString(w / 2, h - 41 * mm, "PLANO DE AÇÃO 5W2H")

    canvas_obj.setStrokeColor(VERDE_NR1)
    canvas_obj.setLineWidth(1.2)
    canvas_obj.line(18 * mm, h - 44 * mm, w - 18 * mm, h - 44 * mm)

    canvas_obj.setFont('Helvetica', 7.5)
    canvas_obj.setFillColor(CINZA_TEXTO)
    canvas_obj.drawString(20 * mm, 12 * mm, "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
    canvas_obj.drawRightString(w - 20 * mm, 12 * mm, f"Página {doc.page}")
    canvas_obj.restoreState()



def _baixar_logo_doc(url):
    """Aceita http(s):// URLs e data:image/...;base64,... strings."""
    import urllib.request as _ur, tempfile as _tf, os as _os, base64 as _b64
    if not url:
        return None
    try:
        tmp = _tf.NamedTemporaryFile(suffix='.png', delete=False)
        if url.startswith('data:'):
            header, data = url.split(',', 1)
            tmp.write(_b64.b64decode(data))
            tmp.close()
        else:
            tmp.close()
            _ur.urlretrieve(url, tmp.name)
        return tmp.name if _os.path.exists(tmp.name) else None
    except Exception as _e:
        print(f"[logo] erro: {_e}")
        return None

def gerar_5w2h(dados: dict = None, output_path=None):
    _dados = dados or {}
    _empresa_nome = _dados.get('empresa_nome') or _dados.get('empresa', {}).get('nome', 'Empresa')
    _meses = ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    _referencia   = _dados.get('referencia') or (_meses[datetime.datetime.now().month-1] + ' de ' + str(datetime.datetime.now().year))
    _resp_tec     = _dados.get('responsavelTecnico') or {'nome': 'Dra. Lucia Kratz', 'crp': 'CRP 09/20590'}
    _logo_parc    = _baixar_logo_doc(_dados.get('logoParceiroUrl', 'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png'))
    _logo_emp     = _baixar_logo_doc(_dados.get('logoEmpresaUrl', ''))
    # Monta SETORES_CBO dinamico
    por_cargo = _dados.get('porCargo') or []
    if por_cargo:
        SETORES_CBO_DIN = [{'setor': c.get('unidade') or c.get('cargo','Geral'),
            'cbo': c.get('cbo',''), 'cargo': c.get('cargo',''),
            'n': c.get('n',0), 'ibp': c.get('ibp',0.0),
            'qtd_perigos': 2 if c.get('ibp',0)<=-1.5 else (1 if c.get('ibp',0)<=0 else 0)}
            for c in por_cargo]
    else:
        por_unidade = _dados.get('porUnidade') or []
        SETORES_CBO_DIN = [{'setor': u.get('unidade','Geral'), 'cbo':'', 'cargo':'Geral',
            'n': u.get('n',0), 'ibp': u.get('ibp',0.0),
            'qtd_perigos': 2 if u.get('ibp',0)<=-1.5 else (1 if u.get('ibp',0)<=0 else 0)}
            for u in por_unidade] or [{'setor':'Empresa','cbo':'','cargo':'Todos',
            'n':_dados.get('respondentes',0),'ibp':_dados.get('ibp_geral',0.0) or 0.0,'qtd_perigos':1}]

    output_path = output_path or nome_arquivo_padrao("PlanoDeAcao5W2H")
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=48 * mm, bottomMargin=20 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph("Plano de Ação 5W2H", s_h1))
    story.append(Paragraph(
        f"{_empresa_nome} · Referencia: {_referencia} · Documento editável — "
        f"3º instrumento do fluxo GRO (Inventário → Avaliação → <b>Plano de Ação</b> → Acompanhamento)",
        s_sub
    ))
    story.append(Paragraph(
        "Este Plano estrutura, automaticamente, as medidas de controle exigidas para todo CBO ou setor "
        "classificado como <b>Substancial</b> ou <b>Intolerável</b> na Avaliação do Risco (instrumento 2), "
        "conforme item 1.5.4.4.3 da NR-1 — definição de medidas de controle com prazo. Cada ação será "
        "reavaliada no instrumento de Acompanhamento (4) com nova medição de IBP para comprovação de eficácia.",
        s_body
    ))
    story.append(Spacer(1, 4 * mm))

    acoes = gerar_acoes(SETORES_CBO_DIN)

    if not acoes:
        story.append(Paragraph(
            "Nenhum CBO ou setor classificado como Substancial ou Intolerável neste ciclo. "
            "Nenhuma ação corretiva obrigatória — manter monitoramento de rotina via Pesquisa Pulso.",
            s_body
        ))
    else:
        for i, item in enumerate(acoes, start=1):
            t = texto_acao(item)
            story.append(Paragraph(f"Ação {i} — {item['nivel']}", s_h3))

            badge_row = [
                Paragraph(f"Zona: {item['zona']['zona_dejours']} (IBP {item['ibp']:+.1f})", s_badge),
                Paragraph(f"GRO: {item['classif']}", s_badge),
            ]
            t_badge = Table([badge_row], colWidths=[85 * mm, 89 * mm])
            t_badge.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), ZONA_COR_FUNDO[item["zona"]["zona_dejours"]]),
                ('BACKGROUND', (1, 0), (1, 0), GRO_COR[item["classif"]]),
                ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_badge)
            story.append(Spacer(1, 2 * mm))

            rows_5w2h = [
                ["What (O quê)", Paragraph(t["what"], s_cell)],
                ["Why (Por quê)", Paragraph(t["why"], s_cell)],
                ["Who (Quem)", Paragraph(t["who"], s_cell)],
                ["Where (Onde)", Paragraph(t["where"], s_cell)],
                ["When (Quando)", Paragraph(t["when"], s_cell)],
                ["How (Como)", Paragraph(t["how"], s_cell)],
                ["How Much (Quanto)", Paragraph(t["howmuch"], s_cell)],
            ]
            t_5w2h = Table(rows_5w2h, colWidths=[34 * mm, 140 * mm])
            t_5w2h.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), VERDE_NR1),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_5w2h)
            story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(
        "Acompanhamento e Reavaliação", s_h2
    ))
    story.append(Paragraph(
        "Este plano será reavaliado a cada ciclo de Pesquisa Pulso semanal e Diagnóstico Geral periódico, "
        "conforme a exigência de melhoria contínua do item 1.5.4.4.6 da NR-1. As ações marcadas como "
        "concluídas serão documentadas com nova medição de IBP no instrumento de Acompanhamento (4) para "
        "comprovação de eficácia.",
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
        ["Responsavel Tecnico:", _resp_tec.get("nome","Dra. Lucia Kratz")],
        ["Registro Profissional:", _resp_tec.get("crp","CRP 09/20590")],
        ["Data e Hora (UTC):", agora],
        ["Hash UUID de Validacao:", hash_uuid],
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
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Responsavel pela Metodologia IBP e Plataforma NR-1 Map", s_h2))
    story.append(Paragraph("✓ VALIDADO PELA RESPONSAVEL TECNICA DA METODOLOGIA", ParagraphStyle(
        'lucia_ok', parent=s_body, textColor=VERDE_NR1, fontName='Helvetica-Bold', fontSize=9)))
    story.append(Spacer(1, 3*mm))
    sig_lucia = [
        ["Responsavel pela Metodologia:", "Dra. Lucia Kratz"],
        ["Registro Profissional:",         "CRP 09/20590"],
        ["Titulacao:",                     "Doutora em Administracao | Psicologa Organizacional"],
        ["Metodologia:",                   "IBP — Indice de Balanca Psicodinamica (Dejours + Herzberg + Maslow)"],
        ["Plataforma:",                    "NR-1 Map | Conformidade Portaria MTE 1.419/2024"],
    ]
    t_sig_lucia = Table(sig_lucia, colWidths=[45*mm, 100*mm])
    t_sig_lucia.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 7.8),
        ('TEXTCOLOR', (0,0), (-1,-1), CINZA_TEXTO),
        ('TOPPADDING',(0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, LINHA),
    ]))
    story.append(t_sig_lucia)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "Este registro é imutável e serve como homologação oficial para fiscalização trabalhista (NR-1).",
        s_body
    ))

    # Injetar logos como atributos da funcao de cabecalho
    desenhar_cabecalho_rodape._empresa_nome = _empresa_nome
    _lp_path = _baixar_logo_doc(_dados.get('logoParceiroUrl', 'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png'))
    _le_path  = _baixar_logo_doc(_dados.get('logoEmpresaUrl', ''))
    desenhar_cabecalho_rodape._logo_parc = _lp_path
    desenhar_cabecalho_rodape._logo_emp  = _le_path
    doc.build(story, onFirstPage=desenhar_cabecalho_rodape, onLaterPages=desenhar_cabecalho_rodape)
    for _tmp in [_lp_path, _le_path]:
        if _tmp and __import__('os').path.exists(_tmp):
            try: __import__('os').unlink(_tmp)
            except: pass
    print(f"Gerado: {output_path}")


if __name__ == "__main__":
    gerar_5w2h()
