# -*- coding: utf-8 -*-
"""
NR-1 Map — Gerador da AVALIAÇÃO DO RISCO (Mapa de Risco)
Instrumento 2 de 4 do fluxo GRO (Inventário > Avaliação > Plano de Ação > Acompanhamento)

NOVIDADE vs. versão anterior do Mapa de Risco:
- Corrige a divergência de zonas: usa as 3 ZONAS OFICIAIS travadas (Sofrimento Patogênico,
  Defesa Oculta, Terreno Fértil) — não mais as 5 sub-zonas que existiam antes.
- Adiciona a MATRIZ OFICIAL DO GRO (Severidade × Probabilidade → Trivial/Tolerável/
  Moderado/Substancial/Intolerável), conforme metodologia AIHA recomendada pela Fundacentro,
  lado a lado com o IBP/Dejours — nunca um substitui o outro (regra travada).
- Cada perigo deste documento corresponde a um perigo já listado no Inventário de Riscos
  (instrumento 1) — mantém a "coerência" que o fiscal verifica entre as etapas do GRO.

Metodologia de cálculo (assumida nesta versão, ajustável):
- Severidade: derivada da Zona Dejours (Sofrimento Patogênico=4, Defesa Oculta=3 — tratada
  como risco "mascarado" e não-trivial mesmo com IBP próximo de zero —, Terreno Fértil=1).
- Probabilidade: derivada da recorrência de perigos identificados no Inventário para aquele
  setor (proxy de recorrência das respostas críticas no Pulso Semanal): 0 perigos=A(Rara),
  1=B, 2=C, 3=D, 4+=E(Muito Provável).
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

# ───────────────────────────── CORES (identidade NR-1 Map + classificação oficial GRO) ─────────────────────────────
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

# Cores oficiais da classificação GRO (escala AIHA/Fundacentro)
GRO_COR = {
    "TRIVIAL": colors.HexColor('#BFE6FB'),
    "TOLERÁVEL": colors.HexColor('#C8EAB8'),
    "MODERADO": colors.HexColor('#FCE98A'),
    "SUBSTANCIAL": colors.HexColor('#F8B25A'),
    "INTOLERÁVEL": colors.HexColor('#F08A8A'),
}

# ───────────────────────────── MATRIZ OFICIAL 5×5 (Severidade × Probabilidade) ─────────────────────────────
# Linhas = letra de probabilidade (A Rara ... E Muito Provável) | Colunas = severidade 1..5
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


def zona_de(ibp: float) -> dict:
    if ibp <= -1.5:
        return ZONAS_IBP[0]
    if ibp <= 1.4:
        return ZONAS_IBP[1]
    return ZONAS_IBP[2]


def nome_arquivo_padrao(tipo_documento: str, empresa: str = None, ano: int = None) -> str:
    """Padrão: ANO_NR-1_Map_NomeDaEmpresa_TipoDoDocumento.pdf"""
    import unicodedata, re
    empresa = empresa or EMPRESA
    ano = ano or datetime.datetime.now().year
    slug = unicodedata.normalize('NFKD', empresa).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-zA-Z0-9]+', '', slug)
    return f"/mnt/user-data/outputs/{ano}_NR-1_Map_{slug}_{tipo_documento}.pdf"


def probabilidade_de(qtd_perigos: int) -> int:
    return min(qtd_perigos + 1, 5)  # 0 perigos->1(A) ... 4+ perigos->5(E)


# ───────────────────────────── DADOS (mesma base do Inventário — mesma empresa, mesmos setores) ─────────────────────────────
# EMPRESA e REFERENCIA agora vêm do parâmetro dados (injetado pelo main.py)


# Cruzamento por CBO — VÁRIOS CBOs por setor (estrutura real), agregados depois para o coletivo.
# REGRA DE ANONIMATO: CBO com N < 3 respondentes é diluído na média geral do setor (não aparece
# linha própria), conforme trava de proteção por volume de CBO.
MIN_RESPONDENTES_CBO = 3
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


def agregar_setor(setor_nome: str, _sc=None):
    """Agrega os CBOs (incluindo os diluídos por anonimato) em um IBP médio ponderado do setor."""
    _base = _sc if _sc is not None else SETORES_CBO
    itens = [c for c in _base if c["setor"] == setor_nome]
    n_total = sum(c["n"] for c in itens)
    ibp_medio = sum(c["ibp"] * c["n"] for c in itens) / n_total if n_total else 0
    qtd_perigos_max = max((c["qtd_perigos"] for c in itens), default=0)
    return {"setor": setor_nome, "ibp": round(ibp_medio, 1), "qtd_perigos": qtd_perigos_max, "n_total": n_total}


MIN_RESPONDENTES_SETOR = 3  # mesma trava de anonimato, aplicada agora também ao nível do setor

SETORES_BRUTOS = [agregar_setor(nome) for nome in dict.fromkeys(c["setor"] for c in SETORES_CBO)]

# Cascata de diluição: setor com n_total < 3 não aparece sozinho — entra no pool da Empresa (geral)
SETORES = [s for s in SETORES_BRUTOS if s["n_total"] >= MIN_RESPONDENTES_SETOR]
SETORES_DILUIDOS = [s for s in SETORES_BRUTOS if s["n_total"] < MIN_RESPONDENTES_SETOR]

if SETORES_DILUIDOS:
    n_dil = sum(s["n_total"] for s in SETORES_DILUIDOS)
    ibp_dil = sum(s["ibp"] * s["n_total"] for s in SETORES_DILUIDOS) / n_dil if n_dil else 0
    qtd_perigos_dil = max((s["qtd_perigos"] for s in SETORES_DILUIDOS), default=0)
    EMPRESA_GERAL = {
        "setor": "Demais setores (agregado — empresa geral)",
        "ibp": round(ibp_dil, 1), "qtd_perigos": qtd_perigos_dil, "n_total": n_dil,
        "setores_origem": [s["setor"] for s in SETORES_DILUIDOS],
    }
    SETORES.append(EMPRESA_GERAL)
else:
    EMPRESA_GERAL = None

# ───────────────────────────── ESTILOS ─────────────────────────────
styles = getSampleStyleSheet()
s_h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=15, textColor=VERDE_NR1,
                       spaceAfter=4, fontName='Helvetica-Bold')
s_sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9.5, textColor=CINZA_TEXTO, spaceAfter=10)
s_h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11.5, textColor=ROXO_NR1,
                       spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
s_body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, textColor=CINZA_TEXTO, leading=13)
s_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.3, textColor=CINZA_TEXTO, leading=11)
s_cell_bold = ParagraphStyle('cellb', parent=s_cell, fontName='Helvetica-Bold')
s_cell_center = ParagraphStyle('cellc', parent=s_cell, alignment=TA_CENTER)
s_badge = ParagraphStyle('badge', parent=s_cell, fontName='Helvetica-Bold', textColor=colors.black,
                          alignment=TA_CENTER)
s_matriz_cell = ParagraphStyle('matrizcell', parent=s_cell, fontName='Helvetica-Bold', fontSize=7,
                                textColor=colors.black, alignment=TA_CENTER, leading=9)
s_matriz_header = ParagraphStyle('matrizh', parent=s_matriz_cell, textColor=colors.white)


def desenhar_cabecalho_rodape(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4
    # Logo esquerda — parceiro ou NR-1 Map como fallback
    _lp = getattr(desenhar_cabecalho_rodape, '_logo_parc', None)
    _le = getattr(desenhar_cabecalho_rodape, '_logo_emp', None)
    if _lp and __import__('os').path.exists(_lp):
        try: canvas_obj.drawImage(_lp, 18*mm, h-24*mm, width=50*mm, height=14*mm, preserveAspectRatio=True, anchor='c')
        except:
            canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-20*mm, 'NR-1Map')
    else:
        canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-20*mm, 'NR-1Map')
    # Logo direita — empresa
    _tem_le = False
    if _le and __import__('os').path.exists(_le):
        try: canvas_obj.drawImage(_le, w-60*mm, h-24*mm, width=50*mm, height=14*mm, preserveAspectRatio=True, anchor='c'); _tem_le = True
        except: pass
    # Sem logo empresa: espaco direito fica em branco (sem texto sobreposto)

    _en = getattr(desenhar_cabecalho_rodape, '_empresa_nome', 'Empresa')

    canvas_obj.setStrokeColor(VERDE_NR1)
    canvas_obj.setLineWidth(1.2)
    canvas_obj.line(18 * mm, h - 26 * mm, w - 18 * mm, h - 26 * mm)

    canvas_obj.setFont('Helvetica-Bold', 9.5)
    canvas_obj.setFillColor(VERDE_NR1)
    canvas_obj.drawCentredString(w / 2, h - 31 * mm, _en)

    canvas_obj.setFont('Helvetica', 8.5)
    canvas_obj.setFillColor(ROXO_NR1)
    canvas_obj.drawCentredString(w / 2, h - 36 * mm, "NR-1Map")

    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.setFillColor(AZUL_ESCURO)
    canvas_obj.drawCentredString(w / 2, h - 41 * mm, "AVALIACAO DO RISCO — MAPA DE RISCO PSICOSSOCIAL")

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
            req = _ur.Request(url, headers={'User-Agent': 'Mozilla/5.0 NR1Map/1.0'})
            with _ur.urlopen(req, timeout=10) as resp:
                with open(tmp.name, 'wb') as f_out:
                    f_out.write(resp.read())
        return tmp.name if _os.path.exists(tmp.name) and _os.path.getsize(tmp.name) > 0 else None
    except Exception as _e:
        print("[logo] erro: " + str(_e))
        return None

def gerar_mapa_risco(dados: dict = None, output_path=None):
    # Dados dinamicos do Firestore (injetados pelo main.py)
    _dados = dados or {}
    _empresa_nome = _dados.get('empresa_nome') or _dados.get('empresa', {}).get('nome', 'Empresa')
    _referencia   = _dados.get('referencia', datetime.datetime.now().strftime('%B de %Y'))
    _resp_tec     = _dados.get('responsavelTecnico') or {'nome': 'Dra. Lucia Kratz', 'crp': 'CRP 09/20590'}
    _num_resp     = _dados.get('respondentes', 0)

    # Monta SETORES_CBO a partir dos dados reais (porCargo do Firestore)
    por_cargo = _dados.get('porCargo') or []
    if por_cargo:
        _setores_cbo = []
        for c in por_cargo:
            _setor_nome = (c.get('unidade') or c.get('cargo') or '').strip()
            if not _setor_nome or _setor_nome.lower() in ('nao informado', 'não informado', '', '-', 'geral', 'todos'):
                _setor_nome = c.get('cargo', '').strip() or 'Empresa (Geral)'
            _setores_cbo.append({
                'setor':       _setor_nome,
                'cbo':         c.get('cbo', ''),
                'cargo':       c.get('cargo', ''),
                'n':           c.get('n', 0),
                'ibp':         c.get('ibp', 0.0),
                'qtd_perigos': 2 if c.get('ibp', 0) <= -1.5 else (1 if c.get('ibp', 0) <= 0 else 0),
            })
    else:
        # Fallback: usa por_unidade
        por_unidade = _dados.get('porUnidade') or []
        _setores_cbo = [
            {'setor': u.get('unidade','Geral'), 'cbo':'', 'cargo':'Geral',
             'n': u.get('n',0), 'ibp': u.get('ibp',0.0),
             'qtd_perigos': 2 if u.get('ibp',0)<=-1.5 else (1 if u.get('ibp',0)<=0 else 0)}
            for u in por_unidade
        ] or [{'setor':'Empresa (Geral)','cbo':'','cargo':'Todos','n':_num_resp,
                'ibp':_dados.get('ibp_geral',0.0) or 0.0,'qtd_perigos':1}]

    # Nome com periodo para diferenciar ciclos
    import re as _re2, unicodedata as _ud2
    _slug_ref = _re2.sub(r'[^a-zA-Z0-9]+', '', _ud2.normalize('NFKD', _referencia).encode('ascii','ignore').decode())
    output_path = output_path or nome_arquivo_padrao(f"MapaDeRisco_{_slug_ref}", _empresa_nome)

    def desenhar_cabecalho_rodape_local(canvas_obj, doc):
        from reportlab.lib.utils import ImageReader as _IR
        canvas_obj.saveState()
        w, h = A4
        _lp_loc = getattr(desenhar_cabecalho_rodape_local, '_logo_parc', None)
        _le_loc = getattr(desenhar_cabecalho_rodape_local, '_logo_emp', None)
        # Logo parceiro (esquerda)
        if _lp_loc:
            try: canvas_obj.drawImage(_IR(_lp_loc), 18*mm, h-28*mm, width=50*mm, height=14*mm, preserveAspectRatio=True)
            except:
                canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-24*mm, 'NR-1Map')
        else:
            canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-24*mm, 'NR-1Map')
        # Logo empresa (direita)
        if _le_loc:
            try: canvas_obj.drawImage(_IR(_le_loc), w-62*mm, h-28*mm, width=50*mm, height=14*mm, preserveAspectRatio=True)
            except: pass
        canvas_obj.setStrokeColor(VERDE_NR1)
        canvas_obj.setLineWidth(1.2)
        canvas_obj.line(18 * mm, h - 30 * mm, w - 18 * mm, h - 30 * mm)
        canvas_obj.setFont('Helvetica-Bold', 9.5)
        canvas_obj.setFillColor(VERDE_NR1)
        canvas_obj.drawCentredString(w / 2, h - 35 * mm, _empresa_nome)
        canvas_obj.setFont('Helvetica', 8.5)
        canvas_obj.setFillColor(ROXO_NR1)
        canvas_obj.drawCentredString(w / 2, h - 40 * mm, "NR-1Map")
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(AZUL_ESCURO)
        canvas_obj.drawCentredString(w / 2, h - 45 * mm, "AVALIACAO DO RISCO — MAPA DE RISCO PSICOSSOCIAL")
        canvas_obj.setStrokeColor(VERDE_NR1)
        canvas_obj.setLineWidth(1.2)
        canvas_obj.line(18 * mm, h - 48 * mm, w - 18 * mm, h - 48 * mm)
        canvas_obj.setFont('Helvetica', 7.5)
        canvas_obj.setFillColor(CINZA_TEXTO)
        canvas_obj.drawString(20 * mm, 12 * mm, "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
        canvas_obj.drawRightString(w - 20 * mm, 12 * mm, f"Pagina {doc.page}")
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=48 * mm, bottomMargin=20 * mm,
                             leftMargin=16 * mm, rightMargin=16 * mm)
    story = []

    story.append(Paragraph("Avaliacao do Risco — Mapa de Risco Psicossocial", s_h1))
    story.append(Paragraph(
        f"{_empresa_nome} · Referencia: {_referencia} · Documento para anexacao ao PGR (NR-1) — "
        f"2 instrumento do fluxo GRO (Inventario → <b>Avaliacao</b> → Plano de Acao → Acompanhamento)",
        s_sub
    ))
    story.append(Paragraph(
        "Esta Avaliação classifica, por setor, os perigos já registrados no Inventário de Riscos "
        "(instrumento 1), em conformidade com o item 1.5.4.4.2 da NR-1, que exige a classificação por "
        "Severidade e Probabilidade. A classificação segue a matriz oficial recomendada pela metodologia "
        "AIHA (Fundacentro), sempre apresentada lado a lado com a Zona Dejours (IBP) — o critério técnico "
        "próprio do NR-1 Map.",
        s_body
    ))
    story.append(Spacer(1, 4 * mm))

    # ── Matriz oficial 5×5 visual (legenda) ──
    story.append(Paragraph("Matriz de Risco Oficial (Severidade × Probabilidade — AIHA/Fundacentro)", s_h2))
    sev_labels = ["1\nLeve", "2\nMenor", "3\nModerada", "4\nMaior", "5\nExtrema"]
    matriz_rows = [[Paragraph("Probabilidade ↓ / Severidade →", s_matriz_header)] +
                   [Paragraph(l.replace("\n", "<br/>"), s_matriz_header) for l in sev_labels]]
    matriz_bg = [('BACKGROUND', (0, 0), (-1, 0), AZUL_ESCURO)]
    for r_idx, letra in enumerate(["E", "D", "C", "B", "A"], start=1):
        row = [Paragraph(f"{PROB_LABEL[letra]} ({letra})", s_matriz_cell)]
        for sev in range(1, 6):
            classif = MATRIZ_GRO[(letra, sev)]
            row.append(Paragraph(classif, s_matriz_cell))
            matriz_bg.append(('BACKGROUND', (sev, r_idx), (sev, r_idx), GRO_COR[classif]))
        matriz_rows.append(row)
        matriz_bg.append(('BACKGROUND', (0, r_idx), (0, r_idx), CINZA_CLARO))

    t_matriz = Table(matriz_rows, colWidths=[34 * mm] + [27.2 * mm] * 5)
    t_matriz.setStyle(TableStyle([
        *matriz_bg,
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_matriz)
    story.append(Spacer(1, 6 * mm))

    # ── Tabela principal: classificação por setor ──
    story.append(Paragraph("Classificação de Risco por Setor", s_h2))
    header = ["Setor", "Zona (IBP/Dejours)", "Severidade", "Probabilidade", "Classificação Oficial (GRO)"]
    rows = [header]
    row_bg = []
    # Monta setores dinamicos
    _setores_brutos = [agregar_setor(nome, _setores_cbo) for nome in dict.fromkeys(cc["setor"] for cc in _setores_cbo)]
    _SETORES = [s for s in _setores_brutos if s["n_total"] >= MIN_RESPONDENTES_SETOR]
    _SETORES_DIL = [s for s in _setores_brutos if s["n_total"] < MIN_RESPONDENTES_SETOR]
    if _SETORES_DIL:
        n_d = sum(s["n_total"] for s in _SETORES_DIL)
        ibp_d = sum(s["ibp"]*s["n_total"] for s in _SETORES_DIL)/n_d if n_d else 0
        _SETORES.append({"setor":"Demais setores (agregado)","ibp":round(ibp_d,1),"qtd_perigos":1,"n_total":n_d,"setores_origem":[s["setor"] for s in _SETORES_DIL]})
        _EMPRESA_GERAL = _SETORES[-1]
    else:
        _EMPRESA_GERAL = None
    for i, st in enumerate(_SETORES, start=1):
        zona = zona_de(st["ibp"])
        sev = zona["severidade"]
        prob_num = probabilidade_de(st["qtd_perigos"])
        prob_letra = PROB_LETRA_POR_NUM[prob_num]
        classif = MATRIZ_GRO[(prob_letra, sev)]
        rows.append([
            Paragraph(st["setor"], s_cell_bold),
            Paragraph(f"{zona['zona_dejours']}<br/>({st['ibp']:+.1f})", s_badge),
            Paragraph(f"{sev} — {sev_labels[sev-1].split(chr(10))[1]}", s_cell_center),
            Paragraph(f"{prob_letra} — {PROB_LABEL[prob_letra]}", s_cell_center),
            Paragraph(classif, s_badge),
        ])
        row_bg.append(('BACKGROUND', (1, i), (1, i), ZONA_COR_FUNDO[zona["zona_dejours"]]))
        row_bg.append(('BACKGROUND', (4, i), (4, i), GRO_COR[classif]))

    t_setores = Table(rows, colWidths=[38 * mm, 32 * mm, 26 * mm, 28 * mm, 40 * mm], repeatRows=1)
    t_setores.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.3),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        *row_bg,
    ]))
    story.append(t_setores)
    story.append(Spacer(1, 4 * mm))

    if _EMPRESA_GERAL:
        origem_txt = ", ".join(_EMPRESA_GERAL.get("setores_origem", []))
        story.append(Paragraph(
            f"<b>Nota sobre agregação por porte:</b> o(s) setor(es) {origem_txt} possuem menos de "
            f"{MIN_RESPONDENTES_SETOR} colaboradores respondentes e, por isso, não aparecem segmentados "
            f"individualmente — seus dados foram agregados à linha \"Demais setores (agregado — empresa "
            f"geral)\" para preservar o anonimato estatístico, conforme a trava de proteção por volume.",
            s_body
        ))
        story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        "<b>Sobre anonimato e atuação do RH:</b> este relatório é estatístico e coletivo — o anonimato "
        "protege a coleta de rotina (Pulso Semanal e Pesquisa Robusta) para garantir respostas honestas. "
        "Isso não impede a atuação individual do RH: o colaborador pode, a qualquer momento e por iniciativa "
        "própria, voluntariamente <b>compartilhar seu diagnóstico individual</b> com o RH (com consentimento "
        "registrado e rastro digital), ou acionar o <b>Canal de Acolhimento</b> para pedir apoio nominal. "
        "O RH atua no nível coletivo (setor/cargo) a partir deste documento, e no nível individual sempre que "
        "o próprio colaborador abrir essa porta.",
        s_body
    ))
    story.append(Spacer(1, 6 * mm))

    # ── Cruzamento por Setor × CBO (risco do cargo) ──
    story.append(Paragraph("Classificação de Risco por Setor × CBO (cargo)", s_h2))
    story.append(Paragraph(
        f"O risco psicossocial é calculado primeiro no nível individual de cada CBO (cargo), e depois "
        f"agregado ao resultado coletivo do setor (tabela anterior). Um mesmo setor pode reunir vários "
        f"cargos com exposições diferentes. Por proteção de anonimato, CBOs com menos de "
        f"{MIN_RESPONDENTES_CBO} respondentes não aparecem em linha própria — seus dados entram apenas "
        f"na média agregada do setor, sem identificação individual.",
        s_body
    ))
    story.append(Spacer(1, 2 * mm))

    header_cbo = ["Setor", "CBO / Cargo", "N", "IBP", "Zona (IBP)", "Severidade", "Prob.", "GRO"]
    rows_cbo = [header_cbo]
    row_bg_cbo = []
    span_cbo = []
    current_row = 1
    for setor_nome in dict.fromkeys(cc["setor"] for cc in _setores_cbo):
        if setor_nome in [s.get("setor") for s in _SETORES_DIL]:
            continue  # setor inteiro diluído na Empresa (geral) — não expõe linha própria
        itens_validos = [cc for cc in _setores_cbo if cc["setor"] == setor_nome and cc["n"] >= MIN_RESPONDENTES_CBO]
        if not itens_validos:
            continue
        row_start = current_row
        for c in itens_validos:
            zona = zona_de(c["ibp"])
            sev = zona["severidade"]
            prob_num = probabilidade_de(c["qtd_perigos"])
            prob_letra = PROB_LETRA_POR_NUM[prob_num]
            classif = MATRIZ_GRO[(prob_letra, sev)]
            _ibp_str = f"{c['ibp']:+.2f}" if c['ibp'] is not None else "—"
            rows_cbo.append([
                Paragraph(setor_nome, s_cell_bold),
                Paragraph(f"{c['cbo']} — {c['cargo']}" if c['cbo'] else c['cargo'], s_cell),
                Paragraph(str(c["n"]), s_cell_center),
                Paragraph(_ibp_str, s_cell_center),
                Paragraph(zona["zona_dejours"], s_badge),
                Paragraph(str(sev), s_cell_center),
                Paragraph(prob_letra, s_cell_center),
                Paragraph(classif, s_badge),
            ])
            row_idx = len(rows_cbo) - 1
            row_bg_cbo.append(('BACKGROUND', (4, row_idx), (4, row_idx), ZONA_COR_FUNDO[zona["zona_dejours"]]))
            row_bg_cbo.append(('BACKGROUND', (7, row_idx), (7, row_idx), GRO_COR[classif]))
            current_row += 1
        row_end = current_row - 1
        if row_end > row_start:
            span_cbo.append(('SPAN', (0, row_start), (0, row_end)))

    t_cbo = Table(rows_cbo, colWidths=[25*mm, 38*mm, 8*mm, 14*mm, 22*mm, 13*mm, 13*mm, 22*mm], repeatRows=1)
    t_cbo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ROXO_NR1),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6.8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, LINHA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        *row_bg_cbo,
        *span_cbo,
    ]))
    story.append(t_cbo)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph(
        "<b>Nota de coerência (item verificado pela fiscalização):</b> os setores com classificação "
        "<b>Substancial</b> ou <b>Intolerável</b> exigem obrigatoriamente ação registrada no Plano de "
        "Ação 5W2H (instrumento 3), com prazo definido, conforme item 1.5.4.4.3 da NR-1. Setores em "
        "Trivial ou Tolerável seguem em monitoramento contínuo via Pesquisa Pulso semanal.",
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

    desenhar_cabecalho_rodape._empresa_nome = _empresa_nome
    def _dl_logo(url):
        import urllib.request as _ur2, tempfile as _tf2, os as _os3, base64 as _b642
        if not url: return None
        try:
            tmp = _tf2.NamedTemporaryFile(suffix='.png', delete=False)
            if url.startswith('data:'):
                tmp.write(_b642.b64decode(url.split(',',1)[1])); tmp.close()
            else:
                tmp.close()
                req2 = _ur2.Request(url, headers={'User-Agent': 'Mozilla/5.0 NR1Map/1.0'})
                with _ur2.urlopen(req2, timeout=10) as resp2:
                    with open(tmp.name, 'wb') as f_out2:
                        f_out2.write(resp2.read())
            return tmp.name if _os3.path.exists(tmp.name) and _os3.path.getsize(tmp.name) > 0 else None
        except Exception as _e2: print("[dl_logo] " + str(_e2)); return None
    _lp_path = _dl_logo(_dados.get('logoParceiroUrl') or 'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png')
    _le_path  = _dl_logo(_dados.get('logoEmpresaUrl') or '')
    desenhar_cabecalho_rodape_local._logo_parc = _lp_path
    desenhar_cabecalho_rodape_local._logo_emp  = _le_path
    doc.build(story, onFirstPage=desenhar_cabecalho_rodape_local, onLaterPages=desenhar_cabecalho_rodape_local)
    for _tmp in [_lp_path, _le_path]:
        if _tmp and __import__('os').path.exists(_tmp):
            try: __import__('os').unlink(_tmp)
            except: pass
    print(f"Gerado: {output_path}")


if __name__ == "__main__":
    gerar_mapa_risco()
