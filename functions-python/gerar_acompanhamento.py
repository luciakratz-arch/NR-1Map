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
# EMPRESA e REFERENCIA agora vêm do parâmetro dados (injetado pelo main.py)


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


import urllib.request as _urllib_req_ac
import tempfile as _tempfile_ac

def _baixar_logo_ac(url):
    if not url:
        return None
    try:
        tmp = _tempfile_ac.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.close()
        if url.startswith('data:'):
            import base64 as _b64ac
            with open(tmp.name, 'wb') as f_out:
                f_out.write(_b64ac.b64decode(url.split(',', 1)[1]))
        else:
            req = _urllib_req_ac.Request(url, headers={'User-Agent': 'Mozilla/5.0 NR1Map/1.0'})
            with _urllib_req_ac.urlopen(req, timeout=10) as resp:
                with open(tmp.name, 'wb') as f_out:
                    f_out.write(resp.read())
        import os as _osac
        return tmp.name if _osac.path.exists(tmp.name) and _osac.path.getsize(tmp.name) > 0 else None
    except Exception:
        return None

def desenhar_cabecalho_rodape(canvas_obj, doc):
    """Cabecalho com logos reais (atributos injetados por gerar_acompanhamento)."""
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

def gerar_acompanhamento(dados: dict = None, output_path=None):
    _dados = dados or {}
    _empresa_nome = _dados.get('empresa_nome') or _dados.get('empresa', {}).get('nome', 'Empresa')
    _referencia   = _dados.get('referencia') or __import__('datetime').datetime.now().strftime('%d/%m/%Y')
    _resp_tec     = _dados.get('responsavelTecnico') or {'nome': 'Dra. Lucia Kratz', 'crp': 'CRP 09/20590'}
    _acoes        = _dados.get('acoes') or []

    # Gera lista de acompanhamento a partir das acoes do Firestore
    _acompanhamento = []
    por_cargo = _dados.get('porCargo') or _dados.get('porUnidade') or []
    ibp_subcats = _dados.get('ibpSubcats') or {}

    for a in _acoes:
        setor = a.get('setor', '')
        descricao = (a.get('descricao', '') or a.get('acao', '')).replace('[IA] ', '').replace('[IA]', '')
        responsavel = a.get('responsavel', '')
        prazo = a.get('prazo', '')
        status = a.get('status', 'Pendente')
        # Tentar encontrar IBP do setor/cargo correspondente
        ibp_antes = 0.0
        for cc in por_cargo:
            cargo_cc = (cc.get('cargo') or '').lower()
            unidade_cc = (cc.get('unidade') or '').lower()
            setor_lower = setor.lower()
            if setor_lower in cargo_cc or setor_lower in unidade_cc or cargo_cc in setor_lower:
                ibp_antes = cc.get('ibp', 0.0)
                break
        # Fallback: buscar em ibpSubcats pelo nome do setor
        if ibp_antes == 0.0 and setor:
            for k, v in ibp_subcats.items():
                if setor.lower() in k.lower():
                    ibp_antes = round(v.get('soma', 0) / max(v.get('n', 1), 1), 2) if isinstance(v, dict) else 0.0
                    break

        # Historico de status — data de criacao + data de ultima atualizacao se houver
        hist = []
        if a.get('criadoEm'):
            try:
                import datetime as _dt
                dt_criado = _dt.datetime.fromisoformat(a['criadoEm'].replace('Z',''))
                hist.append((dt_criado.strftime('%d/%m/%Y'), responsavel or 'Sistema', 'Acao criada'))
            except Exception:
                hist.append((__import__('datetime').datetime.now().strftime('%d/%m/%Y'), responsavel or 'Sistema', 'Acao criada'))
        else:
            hist.append((__import__('datetime').datetime.now().strftime('%d/%m/%Y'), responsavel or 'Sistema', 'Acao registrada'))

        if status and status.lower() != 'pendente':
            hist.append((__import__('datetime').datetime.now().strftime('%d/%m/%Y'), responsavel or 'RH', f'Status atualizado para: {status}'))

        _acompanhamento.append({
            'nivel': setor or descricao[:60] or 'Geral',
            'descricao': descricao,
            'responsavel': responsavel,
            'prazo': prazo,
            'classif_origem': a.get('classif') or a.get('risco') or '',
            'status_atual': status,
            'ibp_antes': ibp_antes,
            'ibp_depois': None,
            'data_remedicao': None,
            'historico': hist,
        })
    if not _acompanhamento:
        _acompanhamento = ACOMPANHAMENTO  # fallback para dados de exemplo

    # Logos para cabecalho
    _lp_path_ac = _baixar_logo_ac(_dados.get('logoParceiroUrl') or
                  'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png')
    _le_path_ac = _baixar_logo_ac(_dados.get('logoEmpresaUrl') or '')

    def desenhar_cabecalho_rodape_local(canvas_obj, doc):
        from reportlab.lib.utils import ImageReader
        canvas_obj.saveState()
        w, h = A4
        if _lp_path_ac:
            try:
                canvas_obj.drawImage(ImageReader(_lp_path_ac), 18*mm, h-28*mm,
                                      width=50*mm, height=14*mm,
                                      preserveAspectRatio=True, mask='auto')
            except Exception:
                canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-24*mm, 'NR-1Map')
        else:
            canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE_NR1); canvas_obj.drawString(18*mm, h-24*mm, 'NR-1Map')
        if _le_path_ac:
            try:
                canvas_obj.drawImage(ImageReader(_le_path_ac), w-62*mm, h-28*mm,
                                      width=50*mm, height=14*mm,
                                      preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        canvas_obj.setFont('Helvetica-Bold', 11)
        canvas_obj.setFillColor(VERDE_NR1)
        canvas_obj.drawCentredString(w / 2, h - 31 * mm, _empresa_nome)
        canvas_obj.setFont('Helvetica', 8.5)
        canvas_obj.setFillColor(ROXO_NR1)
        canvas_obj.drawCentredString(w / 2, h - 36 * mm, "NR-1Map")
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(AZUL_ESCURO)
        canvas_obj.drawCentredString(w / 2, h - 41 * mm, "ACOMPANHAMENTO — EVIDENCIAS DE GESTAO CONTINUA")
        canvas_obj.setStrokeColor(VERDE_NR1)
        canvas_obj.setLineWidth(1.2)
        canvas_obj.line(18 * mm, h - 44 * mm, w - 18 * mm, h - 44 * mm)
        canvas_obj.setFont('Helvetica', 7.5)
        canvas_obj.setFillColor(CINZA_TEXTO)
        canvas_obj.drawString(20 * mm, 12 * mm, "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
        canvas_obj.drawRightString(w - 20 * mm, 12 * mm, f"Pagina {doc.page}")
        canvas_obj.restoreState()

    output_path = output_path or nome_arquivo_padrao("Acompanhamento", _empresa_nome)
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=48 * mm, bottomMargin=20 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph("Acompanhamento — Evidencias de Gestao Continua", s_h1))
    story.append(Paragraph(
        f"{_empresa_nome} · {_referencia} · Documento para anexacao ao PGR (NR-1) — "
        f"4 instrumento do fluxo GRO (Inventario → Avaliacao → Plano de Acao → <b>Acompanhamento</b>)",
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

    # -- Grafico de Progresso (Gantt simplificado) --
    import datetime as _dt_gantt
    STATUS_GANTT_COR = {
        'Concluida': '#065F46', 'Concluída': '#065F46',
        'Em andamento': '#92400E',
        'Pendente': '#374151',
    }
    TOTAL_ACOES = len(_acompanhamento)
    concluidas  = sum(1 for x in _acompanhamento if 'onclu' in x['status_atual'])
    andamento   = sum(1 for x in _acompanhamento if 'andamento' in x['status_atual'].lower())
    pendentes   = TOTAL_ACOES - concluidas - andamento

    # Cabecalho do resumo
    story.append(Paragraph("Resumo do Plano de Acao", s_h2))
    resumo_rows = [
        [Paragraph("<b>Total de Acoes</b>", s_cell),
         Paragraph("<b>Concluidas</b>", s_cell),
         Paragraph("<b>Em Andamento</b>", s_cell),
         Paragraph("<b>Pendentes</b>", s_cell)],
        [Paragraph(str(TOTAL_ACOES), s_cell),
         Paragraph(str(concluidas), s_cell),
         Paragraph(str(andamento), s_cell),
         Paragraph(str(pendentes), s_cell)],
    ]
    t_resumo = Table(resumo_rows, colWidths=[43*mm, 43*mm, 43*mm, 43*mm])
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#D1FAE5')),
        ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#FEF3C7')),
        ('BACKGROUND', (3, 1), (3, 1), colors.HexColor('#F3F4F6')),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('GRID',       (0, 0), (-1, -1), 0.5, LINHA),
    ]))
    story.append(t_resumo)
    story.append(Spacer(1, 5 * mm))

    # Gantt -- barra de progresso por acao
    story.append(Paragraph("Progresso por Acao", s_h2))
    gantt_header = [
        Paragraph("<b>Acao</b>", s_cell),
        Paragraph("<b>Responsavel</b>", s_cell),
        Paragraph("<b>Prazo</b>", s_cell),
        Paragraph("<b>Status</b>", s_cell),
    ]
    gantt_rows = [gantt_header]
    for gi, gitem in enumerate(_acompanhamento, 1):
        st = gitem['status_atual']
        cor_st = colors.HexColor(STATUS_GANTT_COR.get(st, '#374151'))
        gantt_rows.append([
            Paragraph(f"{gi}. {gitem['nivel'][:45]}", s_cell),
            Paragraph(gitem.get('responsavel', '') or '', s_cell),
            Paragraph(gitem.get('prazo', '') or '', s_cell),
            Paragraph(f"<b>{st}</b>", ParagraphStyle('gs', parent=s_badge,
                textColor=cor_st, fontSize=8)),
        ])
    t_gantt = Table(gantt_rows, colWidths=[75*mm, 42*mm, 28*mm, 29*mm])
    t_gantt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_NR1),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 8),
        ('GRID',       (0, 0), (-1, -1), 0.5, LINHA),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
    ]))
    story.append(t_gantt)
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Detalhamento por Acao", s_h2))
    story.append(Spacer(1, 3 * mm))

    for i, item in enumerate(_acompanhamento, start=1):
        story.append(Paragraph(f"Acao {i} -- {item['nivel']}", s_h3))

        delta, msg_eficacia = eficacia(item["ibp_antes"], item["ibp_depois"])
        depois_txt = f"{item['ibp_depois']:+.1f}" if item["ibp_depois"] is not None else "--"
        delta_txt = f"{delta:+.1f}" if delta is not None else "--"

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

    doc.build(story, onFirstPage=desenhar_cabecalho_rodape_local, onLaterPages=desenhar_cabecalho_rodape_local)
    print(f"Gerado: {output_path}")


if __name__ == "__main__":
    gerar_acompanhamento()
