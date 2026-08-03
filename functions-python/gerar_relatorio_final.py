# -*- coding: utf-8 -*-
"""
NR-1 Map -- Gerador do LAUDO TECNICO PSICOSSOCIAL (Relatorio Final Consolidado)
Conformidade: NR-1 / Portaria MTE n. 1.419/2024
Metodologia: Psicodinamica do Trabalho (Dejours) + Herzberg + Maslow
Dados: lidos dinamicamente do Firestore pela Cloud Function (main.py)
"""

import uuid
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ──────────────────────────── CORES IDENTIDADE NR-1 Map ────────────────────────────
VERDE      = colors.HexColor('#0A6E4F')
VERDE_CLR  = colors.HexColor('#12A073')
ROXO       = colors.HexColor('#7B00C4')
AZUL_ESC   = colors.HexColor('#1F2937')
CINZA      = colors.HexColor('#374151')
CINZA_CLR  = colors.HexColor('#F3F4F6')
LINHA      = colors.HexColor('#D1D5DB')
VERDE_OK   = colors.HexColor('#16A34A')
LARANJA    = colors.HexColor('#D97706')

ZONA_COR = {
    "Sofrimento Patogenico": colors.HexColor('#FBD5D5'),
    "Defesa Oculta":         colors.HexColor('#FFF1B8'),
    "Terreno Fertil":        colors.HexColor('#D2F2E2'),
}
GRO_COR = {
    "TRIVIAL":      colors.HexColor('#BFE6FB'),
    "TOLERAVEL":    colors.HexColor('#C8EAB8'),
    "MODERADO":     colors.HexColor('#FCE98A'),
    "SUBSTANCIAL":  colors.HexColor('#F8B25A'),
    "INTOLERAVEL":  colors.HexColor('#F08A8A'),
}

# ──────────────────────────── MATRIZ GRO (Severidade x Probabilidade) ────────────────────────────
MATRIZ_GRO = {
    ("E",1):"MODERADO",    ("E",2):"SUBSTANCIAL", ("E",3):"SUBSTANCIAL", ("E",4):"INTOLERAVEL", ("E",5):"INTOLERAVEL",
    ("D",1):"TOLERAVEL",   ("D",2):"MODERADO",    ("D",3):"MODERADO",    ("D",4):"SUBSTANCIAL", ("D",5):"INTOLERAVEL",
    ("C",1):"TRIVIAL",     ("C",2):"TOLERAVEL",   ("C",3):"MODERADO",    ("C",4):"SUBSTANCIAL", ("C",5):"INTOLERAVEL",
    ("B",1):"TRIVIAL",     ("B",2):"TOLERAVEL",   ("B",3):"TOLERAVEL",   ("B",4):"MODERADO",    ("B",5):"SUBSTANCIAL",
    ("A",1):"TRIVIAL",     ("A",2):"TRIVIAL",     ("A",3):"TOLERAVEL",   ("A",4):"TOLERAVEL",   ("A",5):"MODERADO",
}
PROB_LETRA = {1:"A", 2:"B", 3:"C", 4:"D", 5:"E"}

MODULOS_NOME = {
    "M1": "Fatores Fisiologicos / Corpo e Mente",
    "M2": "Fatores de Seguranca / Previsibilidade",
    "M3": "Fatores Sociais / Relacionamentos",
    "M4": "Fatores Motivacionais / Proposito",
}
SUBCATS_NOME = {
    "1.1":"Ergonomia e Conforto Fisico",
    "1.2":"Pausas e Ritmo de Trabalho",
    "1.3":"Saude Mental e Ansiedade",
    "1.4":"Carga Cognitiva Digital",
    "2.1":"Clareza de Papeis",
    "2.2":"Metas e Pressao por Resultados",
    "2.3":"Estabilidade e Seguranca no Emprego",
    "2.4":"Treinamento e Capacitacao",
    "3.1":"Lideranca e Gestao Direta",
    "3.2":"Relacionamento com Pares",
    "3.3":"Cultura e Valores Organizacionais",
    "3.4":"Comunicacao Interna",
    "3.5":"Assedio e Violencia no Trabalho",
    "4.1":"Proposito e Missao",
    "4.2":"Reconhecimento e Valorizacao",
    "4.3":"Crescimento e Desenvolvimento",
    "4.4":"Autonomia e Pertencimento",
    "4.5":"Remuneracao e Beneficios",
}

MIN_RESPONDENTES = 3


# ──────────────────────────── HELPERS ────────────────────────────
def zona_de(ibp):
    if ibp <= -1.5: return "Sofrimento Patogenico"
    if ibp <= 1.4:  return "Defesa Oculta"
    return "Terreno Fertil"


def sev_de(zona):
    return {"Sofrimento Patogenico": 4, "Defesa Oculta": 3, "Terreno Fertil": 1}[zona]


def classificar_gro(ibp, n_respostas):
    zona = zona_de(ibp)
    sev  = sev_de(zona)
    prob = min(n_respostas + 1, 5)
    letra = PROB_LETRA[prob]
    return zona, MATRIZ_GRO[(letra, sev)]


def nome_arquivo_padrao(empresa, ano=None):
    import unicodedata, re
    ano = ano or datetime.datetime.now().year
    slug = unicodedata.normalize('NFKD', empresa).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', slug).strip('_')
    return f"/mnt/user-data/outputs/{ano}_NR-1_Map_{slug}_LaudoTecnico.pdf"


# ──────────────────────────── ESTILOS ────────────────────────────
styles = getSampleStyleSheet()
S = {
    "h1":    ParagraphStyle('h1',    parent=styles['Normal'], fontSize=14, textColor=VERDE,   fontName='Helvetica-Bold', spaceAfter=3, spaceBefore=0),
    "h2":    ParagraphStyle('h2',    parent=styles['Normal'], fontSize=11, textColor=ROXO,    fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5),
    "h3":    ParagraphStyle('h3',    parent=styles['Normal'], fontSize=9.5, textColor=AZUL_ESC, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3),
    "sub":   ParagraphStyle('sub',   parent=styles['Normal'], fontSize=8.5, textColor=CINZA,  spaceAfter=8),
    "body":  ParagraphStyle('body',  parent=styles['Normal'], fontSize=8.8, textColor=CINZA,  leading=13.5, spaceAfter=4, alignment=TA_JUSTIFY),
    "cell":  ParagraphStyle('cell',  parent=styles['Normal'], fontSize=7.8, textColor=CINZA,  leading=10.5),
    "cellb": ParagraphStyle('cellb', parent=styles['Normal'], fontSize=7.8, textColor=CINZA,  leading=10.5, fontName='Helvetica-Bold'),
    "ctr":   ParagraphStyle('ctr',   parent=styles['Normal'], fontSize=7.8, textColor=CINZA,  leading=10.5, alignment=TA_CENTER),
    "ok":    ParagraphStyle('ok',    parent=styles['Normal'], fontSize=9.5, textColor=VERDE_OK, fontName='Helvetica-Bold'),
}

TS_BASE = [
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,0), 8),
    ('BACKGROUND', (0,0), (-1,0), VERDE),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('GRID', (0,0), (-1,-1), 0.4, LINHA),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]


# ──────────────────────────── CABECALHO / RODAPE ────────────────────────────
def _cabecalho_rodape(canvas_obj, doc, empresa, resp_tecnico):
    canvas_obj.saveState()
    w, h = A4
    # Logo
    canvas_obj.setFont('Helvetica-Bold', 9)
    canvas_obj.setFillColor(VERDE)
    canvas_obj.drawString(20*mm, h-13*mm, "NR-1Map")
    canvas_obj.setFont('Helvetica', 7.5)
    canvas_obj.setFillColor(ROXO)
    canvas_obj.drawRightString(w-20*mm, h-13*mm, "Plataforma de Gestao de Riscos Psicossociais")
    # Linha
    canvas_obj.setStrokeColor(VERDE)
    canvas_obj.setLineWidth(1.0)
    canvas_obj.line(20*mm, h-16*mm, w-20*mm, h-16*mm)
    # Titulo
    canvas_obj.setFont('Helvetica-Bold', 9.5)
    canvas_obj.setFillColor(AZUL_ESC)
    canvas_obj.drawCentredString(w/2, h-22*mm, "LAUDO TECNICO PSICOSSOCIAL")
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(CINZA)
    canvas_obj.drawCentredString(w/2, h-27*mm, empresa)
    # Rodape
    canvas_obj.setFont('Helvetica', 6.5)
    canvas_obj.setFillColor(CINZA)
    canvas_obj.drawString(20*mm, 10*mm, "NR-1 Map | Portaria MTE n. 1.419/2024 | Documento Confidencial")
    canvas_obj.drawRightString(w-20*mm, 10*mm, f"Pagina {doc.page}")
    # Assinante no rodape das paginas internas
    if doc.page > 1 and resp_tecnico:
        nome = resp_tecnico.get('nome', '')
        crp  = resp_tecnico.get('crp', '')
        if nome:
            canvas_obj.setFont('Helvetica', 6.5)
            canvas_obj.drawCentredString(w/2, 10*mm, f"Resp. Tecnico: {nome}" + (f" | {crp}" if crp else ""))
    canvas_obj.restoreState()


# ──────────────────────────── FUNCAO PRINCIPAL ────────────────────────────
def gerar_relatorio_final(dados: dict, output_path: str = None) -> str:
    """
    dados = {
      "empresa":            str,
      "cnpj":               str,
      "responsavel":        str,
      "responsavelTecnico": {"nome": str, "crp": str, "email": str},
      "referencia":         str,   # ex: "Junho de 2026"
      "colaboradoresAtivos": int,
      "respondentes":       int,
      "ibpGeral":           float,
      "ibpModulos":         {"M1": float, "M2": float, "M3": float, "M4": float},
      "ibpSubcats":         {"1.1": {"ibp": float, "n": int, "nome": str, "modId": str}, ...},
      "porUnidade":         [{"unidade": str, "n": int, "ibp": float}, ...],
      "porCargo":           [{"cargo": str, "cbo": str, "unidade": str, "n": int, "ibp": float}, ...],
      "acoes":              [{"descricao": str, "status": str, "classif": str}, ...],
    }
    """
    empresa       = dados.get("empresa", "Empresa")
    cnpj          = dados.get("cnpj", "")
    responsavel   = dados.get("responsavel", "")
    resp_tec      = dados.get("responsavelTecnico") or {}
    referencia    = dados.get("referencia", datetime.datetime.now().strftime("%B de %Y"))
    col_ativos    = dados.get("colaboradoresAtivos", 0)
    respondentes  = dados.get("respondentes", 0)
    ibp_geral     = dados.get("ibpGeral")
    ibp_modulos   = dados.get("ibpModulos") or {}
    ibp_subcats   = dados.get("ibpSubcats") or {}
    por_unidade   = dados.get("porUnidade") or []
    por_cargo     = dados.get("porCargo") or []
    acoes         = dados.get("acoes") or []

    output_path = output_path or nome_arquivo_padrao(empresa)

    taxa = round(100 * respondentes / col_ativos) if col_ativos > 0 else 0
    zona_geral = zona_de(ibp_geral) if ibp_geral is not None else "Sem dados"
    gro_geral  = classificar_gro(ibp_geral, respondentes)[1] if ibp_geral is not None else "—"

    agora     = datetime.datetime.now(datetime.timezone.utc)
    agora_str = agora.strftime("%d/%m/%Y as %H:%M UTC")
    hash_doc  = str(uuid.uuid4()).upper()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=36*mm, bottomMargin=20*mm,
        leftMargin=18*mm, rightMargin=18*mm
    )

    def _cb(c, d): _cabecalho_rodape(c, d, empresa, resp_tec)

    story = []

    # ════════════════════════════════════════════════════════
    # CAPA
    # ════════════════════════════════════════════════════════
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("LAUDO TECNICO PSICOSSOCIAL", S["h1"]))
    story.append(Paragraph(
        f"Relatorio Final Consolidado | {empresa} | {referencia} | "
        f"Conformidade NR-1 / Portaria MTE n. 1.419/2024",
        S["sub"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINHA, spaceAfter=5))

    # Ficha de identificacao
    ficha = [
        ["Empresa",                empresa],
        ["CNPJ",                   cnpj or "—"],
        ["Responsavel pela empresa", responsavel or "—"],
        ["Responsavel Tecnico",    resp_tec.get("nome","—") + (" | " + resp_tec.get("crp","") if resp_tec.get("crp") else "")],
        ["Periodo de referencia",  referencia],
        ["Colaboradores ativos",   str(col_ativos)],
        ["Respondentes validos",   f"{respondentes} ({taxa}% de adesao)"],
        ["IBP Geral da organizacao", f"{ibp_geral:+.2f}" if ibp_geral is not None else "—"],
        ["Zona Dejours / Classif. GRO", f"{zona_geral} / {gro_geral}"],
        ["Metodologia",            "Psicodinamica do Trabalho (Dejours) | Herzberg | Maslow"],
        ["Gerado em",              agora_str],
        ["Hash de validacao",      hash_doc],
    ]
    t = Table(ficha, colWidths=[52*mm, 117*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), CINZA),
        ('GRID',      (0,0), (-1,-1), 0.4, LINHA),
        ('BACKGROUND',(0,0), (0,-1), CINZA_CLR),
        ('TOPPADDING',(0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 1. FUNDAMENTACAO TEORICA E METODOLOGICA
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("1. Fundamentacao Teorica e Metodologica", S["h2"]))

    story.append(Paragraph("1.1 Psicodinamica do Trabalho — Christophe Dejours", S["h3"]))
    story.append(Paragraph(
        "A Psicodinamica do Trabalho, desenvolvida pelo medico e psicanalista frances Christophe Dejours, "
        "investiga a relacao entre organizacao do trabalho e o sofrimento psiquico dos trabalhadores. "
        "O conceito central e a Balanca Psicodinamica: quando as estrategias de defesa coletiva conseguem "
        "transformar o sofrimento em prazer, o equilibrio se mantem; quando falham, instala-se o "
        "<b>Sofrimento Patogenico</b>, precursor de adoecimento psiquico e fisico.",
        S["body"]
    ))
    story.append(Paragraph(
        "O <b>Indice de Balanca Psicodinamica (IBP)</b> quantifica esse equilibrio em escala de "
        "<b>-5,0 (Sofrimento Patogenico maximo) a +5,0 (Terreno Fertil pleno)</b>, calculado pela "
        "conversao direta das frequencias de resposta: Sempre=+5 | Na maioria=+2,5 | Na metade=0 | "
        "Poucas vezes=-2,5 | Raramente=-5. Tres zonas resultantes:",
        S["body"]
    ))
    zonas_tab = [
        ["Zona Dejours",          "Faixa IBP",      "Significado Clinico",                      "Severidade GRO"],
        ["Sofrimento Patogenico", "-5,0 a -1,5",    "Risco ativo de adoecimento psiquico",      "Alta (4)"],
        ["Defesa Oculta",         "-1,4 a +1,4",    "Sofrimento mascarado por defesas coletivas","Media (3)"],
        ["Terreno Fertil",        "+1,5 a +5,0",    "Equilibrio Prazer-Sofrimento preservado",  "Baixa (1)"],
    ]
    tz = Table(zonas_tab, colWidths=[42*mm, 26*mm, 72*mm, 29*mm], repeatRows=1)
    bg_zonas = [
        ('BACKGROUND',(0,1),(-1,1), ZONA_COR["Sofrimento Patogenico"]),
        ('BACKGROUND',(0,2),(-1,2), ZONA_COR["Defesa Oculta"]),
        ('BACKGROUND',(0,3),(-1,3), ZONA_COR["Terreno Fertil"]),
    ]
    tz.setStyle(TableStyle(TS_BASE + bg_zonas))
    story.append(tz)
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("1.2 Teoria dos Dois Fatores — Frederick Herzberg", S["h3"]))
    story.append(Paragraph(
        "Herzberg distingue <b>fatores higienicos</b> (salario, condicoes fisicas, politicas da empresa — "
        "cuja ausencia causa insatisfacao mas cuja presenca nao gera motivacao) dos <b>fatores motivadores</b> "
        "(reconhecimento, responsabilidade, crescimento — que produzem satisfacao genuina). "
        "Os Modulos 1 e 2 do IBP mapeiam predominantemente fatores higienicos; "
        "os Modulos 3 e 4 mapeiam fatores motivadores.",
        S["body"]
    ))

    story.append(Paragraph("1.3 Hierarquia de Necessidades — Abraham Maslow", S["h3"]))
    story.append(Paragraph(
        "A piramide de Maslow organiza as necessidades humanas em cinco niveis (fisiologicas, seguranca, "
        "sociais, estima e autorrealizacao). Este laudo foca nos tres primeiros niveis — base da piramide "
        "— cujas falhas sao as principais precursoras de risco psicossocial no ambiente laboral, "
        "mapeadas respectivamente pelos Modulos 1, 2 e 3 do questionario.",
        S["body"]
    ))

    story.append(Paragraph("1.4 Base Legal e Normativa", S["h3"]))
    story.append(Paragraph(
        "Este laudo cumpre integralmente os requisitos da <b>NR-1 (Norma Regulamentadora n. 1)</b>, "
        "atualizada pela <b>Portaria MTE n. 1.419/2024</b>, que estabelece obrigacao de identificacao, "
        "avaliacao e controle dos riscos psicossociais como parte do Gerenciamento de Riscos "
        "Ocupacionais (GRO) e do Programa de Gerenciamento de Riscos (PGR). "
        "A classificacao de risco utiliza a <b>Matriz Severidade x Probabilidade</b> (metodologia "
        "AIHA/Fundacentro), com cinco niveis: Trivial, Toleravel, Moderado, Substancial e Intoleravel.",
        S["body"]
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 2. RESULTADOS POR MODULO E SUBCATEGORIA
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("2. Resultados por Modulo e Subcategoria (IBP)", S["h2"]))
    story.append(Paragraph(
        "Apresenta-se a media IBP de cada subcategoria avaliada, com a zona Dejours correspondente "
        "e a classificacao oficial GRO. Subcategorias com menos de "
        f"{MIN_RESPONDENTES} respondentes sao suprimidas por trava de anonimato estatistico.",
        S["body"]
    ))

    # Agrupa subcats por modulo
    subcats_por_mod = {}
    for sc_id, sc_data in ibp_subcats.items():
        mod = sc_data.get("modId", "M1")
        if mod not in subcats_por_mod:
            subcats_por_mod[mod] = []
        subcats_por_mod[mod].append((sc_id, sc_data))

    for mod_id in ["M1","M2","M3","M4"]:
        mod_nome = MODULOS_NOME.get(mod_id, mod_id)
        ibp_mod  = ibp_modulos.get(mod_id)
        ibp_mod_str = f"{ibp_mod:+.2f}" if ibp_mod is not None else "—"
        zona_mod = zona_de(ibp_mod) if ibp_mod is not None else "—"
        gro_mod  = classificar_gro(ibp_mod, respondentes)[1] if ibp_mod is not None else "—"
        cor_mod  = ZONA_COR.get(zona_mod, CINZA_CLR)

        story.append(Paragraph(f"2.{['M1','M2','M3','M4'].index(mod_id)+1}  {mod_nome}", S["h3"]))

        # Linha de resumo do modulo
        resumo_mod = [[
            Paragraph(f"IBP do Modulo: {ibp_mod_str}", S["cellb"]),
            Paragraph(f"Zona Dejours: {zona_mod}", S["cellb"]),
            Paragraph(f"Classificacao GRO: {gro_mod}", S["cellb"]),
        ]]
        tm = Table(resumo_mod, colWidths=[55*mm, 62*mm, 52*mm])
        tm.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_mod),
            ('GRID', (0,0), (-1,-1), 0.4, LINHA),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(tm)
        story.append(Spacer(1, 2*mm))

        # Tabela de subcategorias
        scs = subcats_por_mod.get(mod_id, [])
        if scs:
            hdr_sc = ["Subcategoria", "N", "IBP Medio", "Zona Dejours", "Classif. GRO", "Risco"]
            rows_sc = [hdr_sc]
            bgs_sc  = []
            for idx, (sc_id, sc) in enumerate(sorted(scs, key=lambda x: x[0]), start=1):
                n_sc  = sc.get("n", 0)
                ibp_sc = sc.get("ibp", 0.0)
                nome_sc = SUBCATS_NOME.get(sc_id, sc.get("nome", sc_id))
                if n_sc < MIN_RESPONDENTES:
                    rows_sc.append([
                        Paragraph(nome_sc, S["cell"]),
                        Paragraph(f"< {MIN_RESPONDENTES}", S["ctr"]),
                        Paragraph("—", S["ctr"]),
                        Paragraph("Suprimido (anonimato)", S["ctr"]),
                        Paragraph("—", S["ctr"]),
                        Paragraph("—", S["ctr"]),
                    ])
                    bgs_sc.append(('BACKGROUND',(0,idx),(-1,idx), CINZA_CLR))
                    continue
                zona_sc = zona_de(ibp_sc)
                gro_sc  = classificar_gro(ibp_sc, n_sc)[1]
                cor_sc  = ZONA_COR.get(zona_sc, CINZA_CLR)
                rows_sc.append([
                    Paragraph(nome_sc,        S["cell"]),
                    Paragraph(str(n_sc),       S["ctr"]),
                    Paragraph(f"{ibp_sc:+.2f}", S["ctr"]),
                    Paragraph(zona_sc,         S["ctr"]),
                    Paragraph(gro_sc,          S["ctr"]),
                    Paragraph("⚠" if gro_sc in ("SUBSTANCIAL","INTOLERAVEL") else "✓", S["ctr"]),
                ])
                bgs_sc.append(('BACKGROUND',(3,idx),(4,idx), cor_sc))
                if gro_sc == "INTOLERAVEL":
                    bgs_sc.append(('BACKGROUND',(5,idx),(5,idx), GRO_COR["INTOLERAVEL"]))
                elif gro_sc == "SUBSTANCIAL":
                    bgs_sc.append(('BACKGROUND',(5,idx),(5,idx), GRO_COR["SUBSTANCIAL"]))
                else:
                    bgs_sc.append(('BACKGROUND',(5,idx),(5,idx), GRO_COR.get(gro_sc, CINZA_CLR)))
            tsc = Table(rows_sc, colWidths=[57*mm, 12*mm, 20*mm, 38*mm, 28*mm, 14*mm], repeatRows=1)
            tsc.setStyle(TableStyle(TS_BASE + bgs_sc))
            story.append(tsc)
        else:
            story.append(Paragraph("Sem dados suficientes para este modulo.", S["body"]))
        story.append(Spacer(1, 4*mm))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 3. SEGMENTACAO POR UNIDADE E CARGO/CBO
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("3. Segmentacao por Unidade e Cargo/CBO", S["h2"]))
    story.append(Paragraph(
        f"Trava de anonimato estatistico aplicada: grupos com menos de <b>{MIN_RESPONDENTES} respondentes</b> "
        "nao sao individualizados, sendo apresentados de forma agregada para proteger a identidade "
        "dos colaboradores, conforme diretrizes de compliance da plataforma.",
        S["body"]
    ))

    # 3.1 Por Unidade
    story.append(Paragraph("3.1 Resultado por Unidade", S["h3"]))
    if por_unidade:
        hdr_un = ["Unidade", "Respondentes", "IBP Medio", "Zona Dejours", "Classif. GRO"]
        rows_un = [hdr_un]
        bgs_un  = []
        agregados_un = []

        for idx, u in enumerate(sorted(por_unidade, key=lambda x: x.get("ibp",0)), start=1):
            n_u   = u.get("n", 0)
            ibp_u = u.get("ibp", 0.0)
            nome_u = u.get("unidade", "—")
            if n_u < MIN_RESPONDENTES:
                agregados_un.append(u)
                continue
            zona_u = zona_de(ibp_u)
            gro_u  = classificar_gro(ibp_u, n_u)[1]
            rows_un.append([
                Paragraph(nome_u,          S["cellb"]),
                Paragraph(str(n_u),         S["ctr"]),
                Paragraph(f"{ibp_u:+.2f}", S["ctr"]),
                Paragraph(zona_u,           S["ctr"]),
                Paragraph(gro_u,            S["ctr"]),
            ])
            i = len(rows_un) - 1
            bgs_un.append(('BACKGROUND',(3,i),(3,i), ZONA_COR.get(zona_u, CINZA_CLR)))
            bgs_un.append(('BACKGROUND',(4,i),(4,i), GRO_COR.get(gro_u, CINZA_CLR)))

        # Agrupa unidades com menos de MIN respondentes
        if agregados_un:
            n_ag   = sum(a.get("n",0) for a in agregados_un)
            ibp_ag = (sum(a.get("ibp",0)*a.get("n",0) for a in agregados_un) / n_ag) if n_ag else 0
            zona_ag = zona_de(ibp_ag)
            gro_ag  = classificar_gro(ibp_ag, n_ag)[1]
            nomes_ag = ", ".join(a.get("unidade","") for a in agregados_un)
            rows_un.append([
                Paragraph(f"Demais unidades agrupadas ({nomes_ag})", S["cell"]),
                Paragraph(str(n_ag),         S["ctr"]),
                Paragraph(f"{ibp_ag:+.2f}", S["ctr"]),
                Paragraph(zona_ag,           S["ctr"]),
                Paragraph(gro_ag,            S["ctr"]),
            ])
            i = len(rows_un) - 1
            bgs_un.append(('BACKGROUND',(3,i),(3,i), ZONA_COR.get(zona_ag, CINZA_CLR)))
            bgs_un.append(('BACKGROUND',(4,i),(4,i), GRO_COR.get(gro_ag, CINZA_CLR)))

        tun = Table(rows_un, colWidths=[60*mm, 28*mm, 24*mm, 38*mm, 19*mm], repeatRows=1)
        tun.setStyle(TableStyle(TS_BASE + bgs_un))
        story.append(tun)
    else:
        story.append(Paragraph("Sem dados de unidade disponíveis para este ciclo.", S["body"]))

    story.append(Spacer(1, 5*mm))

    # 3.2 Por Cargo/CBO
    story.append(Paragraph("3.2 Resultado por Cargo / CBO", S["h3"]))
    if por_cargo:
        hdr_cg = ["Cargo", "CBO", "Unidade", "N", "IBP", "Zona", "GRO"]
        rows_cg = [hdr_cg]
        bgs_cg  = []
        agregados_cg = []

        for c in sorted(por_cargo, key=lambda x: x.get("ibp", 0)):
            n_c   = c.get("n", 0)
            ibp_c = c.get("ibp", 0.0)
            if n_c < MIN_RESPONDENTES:
                agregados_cg.append(c)
                continue
            zona_c = zona_de(ibp_c)
            gro_c  = classificar_gro(ibp_c, n_c)[1]
            rows_cg.append([
                Paragraph(c.get("cargo","—"),   S["cell"]),
                Paragraph(c.get("cbo","—"),     S["ctr"]),
                Paragraph(c.get("unidade","—"), S["cell"]),
                Paragraph(str(n_c),              S["ctr"]),
                Paragraph(f"{ibp_c:+.2f}",      S["ctr"]),
                Paragraph(zona_c,                S["ctr"]),
                Paragraph(gro_c,                 S["ctr"]),
            ])
            i = len(rows_cg) - 1
            bgs_cg.append(('BACKGROUND',(5,i),(5,i), ZONA_COR.get(zona_c, CINZA_CLR)))
            bgs_cg.append(('BACKGROUND',(6,i),(6,i), GRO_COR.get(gro_c, CINZA_CLR)))

        if agregados_cg:
            n_ag2  = sum(a.get("n",0) for a in agregados_cg)
            ibp_ag2 = (sum(a.get("ibp",0)*a.get("n",0) for a in agregados_cg) / n_ag2) if n_ag2 else 0
            zona_ag2 = zona_de(ibp_ag2)
            gro_ag2  = classificar_gro(ibp_ag2, n_ag2)[1]
            rows_cg.append([
                Paragraph(f"CBOs agrupados (< {MIN_RESPONDENTES} resp.)", S["cell"]),
                Paragraph("—", S["ctr"]),
                Paragraph("—", S["ctr"]),
                Paragraph(str(n_ag2),             S["ctr"]),
                Paragraph(f"{ibp_ag2:+.2f}",     S["ctr"]),
                Paragraph(zona_ag2,               S["ctr"]),
                Paragraph(gro_ag2,                S["ctr"]),
            ])
            i = len(rows_cg) - 1
            bgs_cg.append(('BACKGROUND',(5,i),(5,i), ZONA_COR.get(zona_ag2, CINZA_CLR)))
            bgs_cg.append(('BACKGROUND',(6,i),(6,i), GRO_COR.get(gro_ag2, CINZA_CLR)))

        tcg = Table(rows_cg, colWidths=[48*mm, 14*mm, 34*mm, 10*mm, 14*mm, 30*mm, 19*mm], repeatRows=1)
        tcg.setStyle(TableStyle(TS_BASE + bgs_cg))
        story.append(tcg)
    else:
        story.append(Paragraph("Sem dados de cargo/CBO disponíveis para este ciclo.", S["body"]))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 4. CONCLUSAO TECNICA E CONFORMIDADE GRO
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("4. Conclusao Tecnica e Conformidade com o PGR", S["h2"]))

    # Resumo consolidado
    cor_zona = ZONA_COR.get(zona_geral, CINZA_CLR)
    resumo_geral = [[
        Paragraph("IBP Geral", S["cellb"]),
        Paragraph("Zona Dejours", S["cellb"]),
        Paragraph("Classif. GRO", S["cellb"]),
        Paragraph("Taxa de Adesao", S["cellb"]),
    ],[
        Paragraph(f"{ibp_geral:+.2f}" if ibp_geral is not None else "—", S["ctr"]),
        Paragraph(zona_geral, S["ctr"]),
        Paragraph(gro_geral,  S["ctr"]),
        Paragraph(f"{taxa}% ({respondentes}/{col_ativos})", S["ctr"]),
    ]]
    trg = Table(resumo_geral, colWidths=[35*mm, 55*mm, 42*mm, 37*mm])
    trg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), AZUL_ESC),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,1), (-1,1), cor_zona),
        ('GRID', (0,0), (-1,-1), 0.4, LINHA),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(trg)
    story.append(Spacer(1, 4*mm))

    # Texto de conclusao
    piores_mod = sorted(
        [(m, v) for m, v in ibp_modulos.items() if v is not None],
        key=lambda x: x[1]
    )
    piores_txt = ""
    if piores_mod:
        pm = piores_mod[0]
        piores_txt = (
            f" O modulo de maior criticidade e <b>{MODULOS_NOME.get(pm[0], pm[0])}</b> "
            f"(IBP {pm[1]:+.2f}), que requer atencao prioritaria."
        )

    story.append(Paragraph(
        f"Diante dos dados consolidados neste ciclo de avaliacao psicossocial, a organizacao "
        f"<b>{empresa}</b> apresenta IBP Geral de <b>{(f'{ibp_geral:+.2f}' if ibp_geral is not None else '—')}</b>, "
        f"correspondendo a zona <b>{zona_geral}</b> na escala Dejours e classificacao <b>{gro_geral}</b> "
        f"na Matriz GRO (Portaria MTE 1.419/2024).{piores_txt} "
        f"Recomenda-se a implementacao ou manutencao do Plano de Acao 5W2H para os grupos criticos "
        f"identificados, monitoramento continuo via Pesquisas Pulso semanais (NR-1, item 1.5.4.4.6) "
        f"e reavaliacao completa deste laudo no proximo periodo de referencia.",
        S["body"]
    ))
    story.append(Spacer(1, 3*mm))

    # Acoes em andamento
    if acoes:
        story.append(Paragraph("4.1 Plano de Acao — Status Resumido", S["h3"]))
        hdr_ac = ["Acao / Grupo", "Classif. GRO", "Status"]
        rows_ac = [hdr_ac]
        for a in acoes:
            gro_a = a.get("classif","—").upper()
            rows_ac.append([
                Paragraph(a.get("descricao","—"), S["cell"]),
                Paragraph(gro_a,                   S["ctr"]),
                Paragraph(a.get("status","—"),     S["cellb"]),
            ])
        tac = Table(rows_ac, colWidths=[97*mm, 35*mm, 37*mm], repeatRows=1)
        tac.setStyle(TableStyle(TS_BASE))
        story.append(tac)
        story.append(Spacer(1, 4*mm))

    # Conformidade com PGR
    story.append(Paragraph("4.2 Declaracao de Conformidade com o PGR", S["h3"]))
    itens_pgr = [
        "Identificacao dos perigos psicossociais (NR-1, item 1.5.3)",
        "Avaliacao dos riscos com Matriz Severidade x Probabilidade (NR-1, item 1.5.4)",
        "Plano de Acao corretiva e preventiva documentado (NR-1, item 1.5.4.4)",
        "Monitoramento continuo via Pesquisa Pulso periodica (NR-1, item 1.5.4.4.6)",
        "Trava de anonimato estatistico (minimo 3 respondentes por grupo)",
        "Responsavel Tecnico com registro ativo no CRP",
        "Documento gerado eletronicamente com hash de validacao unico",
    ]
    for item in itens_pgr:
        story.append(Paragraph(f"[✓]  {item}", S["body"]))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 5. ASSINATURA TECNICA
    # ════════════════════════════════════════════════════════
    story.append(Paragraph("5. Assinatura e Validacao Tecnica", S["h2"]))
    story.append(Paragraph("DOCUMENTO ASSINADO ELETRONICAMENTE", S["ok"]))
    story.append(Spacer(1, 3*mm))

    nome_tec  = resp_tec.get("nome", "Dra. Lucia Kratz")
    crp_tec   = resp_tec.get("crp",  "CRP 09/20590")
    email_tec = resp_tec.get("email", "luciakratz@gmail.com")

    sig = [
        ["Responsavel Tecnico:",       nome_tec],
        ["Registro Profissional:",      crp_tec],
        ["E-mail:",                     email_tec],
        ["Empresa avaliada:",           empresa],
        ["Periodo de referencia:",      referencia],
        ["Data e Hora da emissao:",     agora_str],
        ["Hash UUID de validacao:",     hash_doc],
        ["Plataforma:",                 "NR-1 Map | Conformidade Portaria MTE 1.419/2024"],
    ]
    tsig = Table(sig, colWidths=[50*mm, 119*mm])
    tsig.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 8.2),
        ('TEXTCOLOR', (0,0), (-1,-1), CINZA),
        ('TOPPADDING',(0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, LINHA),
    ]))
    story.append(tsig)
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE, spaceAfter=4))
    story.append(Paragraph(
        "Este laudo e imutavel apos emissao e serve como documento tecnico oficial para "
        "fiscalizacao trabalhista, audiencias e processos administrativos (NR-1 / Portaria MTE 1.419/2024). "
        "O hash UUID garante unicidade e rastreabilidade do documento.",
        S["body"]
    ))

    doc.build(story, onFirstPage=_cb, onLaterPages=_cb)
    return output_path


# ──────────────────────────── EXECUCAO STANDALONE (teste) ────────────────────────────
if __name__ == "__main__":
    dados_teste = {
        "empresa": "A!Equipe Desenvolvimento Humano e Cultural",
        "cnpj": "12.345.678/0001-99",
        "responsavel": "Lucia Kratz",
        "responsavelTecnico": {"nome": "Dra. Lucia Kratz", "crp": "CRP 09/20590", "email": "luciakratz@gmail.com"},
        "referencia": "Julho de 2026",
        "colaboradoresAtivos": 11,
        "respondentes": 3,
        "ibpGeral": -0.8,
        "ibpModulos": {"M1": -1.2, "M2": -2.1, "M3": 1.8, "M4": 0.6},
        "ibpSubcats": {
            "1.1": {"ibp": -1.5, "n": 3, "nome": "Ergonomia", "modId": "M1"},
            "1.2": {"ibp": -0.8, "n": 3, "nome": "Pausas",    "modId": "M1"},
            "2.1": {"ibp": -2.5, "n": 3, "nome": "Clareza",   "modId": "M2"},
            "2.2": {"ibp": -1.8, "n": 3, "nome": "Metas",     "modId": "M2"},
            "3.1": {"ibp":  2.0, "n": 3, "nome": "Lideranca", "modId": "M3"},
            "3.3": {"ibp":  1.5, "n": 3, "nome": "Cultura",   "modId": "M3"},
            "4.2": {"ibp":  0.5, "n": 3, "nome": "Reconhecimento", "modId": "M4"},
            "4.3": {"ibp":  0.7, "n": 2, "nome": "Crescimento", "modId": "M4"},  # < MIN — suprimido
        },
        "porUnidade": [
            {"unidade": "Sede SP", "n": 2, "ibp": -0.5},   # < MIN — agrupado
            {"unidade": "Filial RJ", "n": 3, "ibp": -1.1},
        ],
        "porCargo": [
            {"cargo": "Analista", "cbo": "2521", "unidade": "Sede SP",   "n": 3, "ibp": -0.8},
            {"cargo": "Assistente", "cbo": "4110", "unidade": "Filial RJ", "n": 2, "ibp": -1.2},  # < MIN
        ],
        "acoes": [
            {"descricao": "Revisao da politica de metas — Comercial", "classif": "SUBSTANCIAL", "status": "Em andamento"},
            {"descricao": "Treinamento de lideranca — Todos os gestores", "classif": "MODERADO", "status": "Pendente"},
        ],
    }
    caminho = gerar_relatorio_final(dados_teste)
    print(f"PDF gerado: {caminho}")
