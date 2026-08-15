# -*- coding: utf-8 -*-
"""
NR-1 Map - Relatorio Anual Consolidado
Evolucao historica dos ciclos + analise quanti e qualitativa + resumo de acoes
"""
import datetime
import uuid
import tempfile as _tmpmod
import os as _os
import urllib.request as _urllib_req

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

# Cores
VERDE     = colors.HexColor('#0A6E4F')
VERDE_CL  = colors.HexColor('#12A073')
VERDE_XP  = colors.HexColor('#F0FDF4')
ROXO      = colors.HexColor('#7B00C4')
ROXO_XP   = colors.HexColor('#F5F0FF')
AMARELO   = colors.HexColor('#F59E0B')
AMARELO_XP= colors.HexColor('#FFFBEB')
VERMELHO  = colors.HexColor('#DC2626')
AZUL      = colors.HexColor('#1E40AF')
CINZA     = colors.HexColor('#6B7280')
CINZA_CL  = colors.HexColor('#F3F4F6')
LINHA     = colors.HexColor('#E5E7EB')
PRETO     = colors.HexColor('#111827')

ZONA_COR = {
    'Terreno Fertil':      VERDE,
    'Defesa Oculta':       AMARELO,
    'Sofrimento Patogenico': VERMELHO,
}
ZONA_FUNDO = {
    'Terreno Fertil':      VERDE_XP,
    'Defesa Oculta':       AMARELO_XP,
    'Sofrimento Patogenico': colors.HexColor('#FEF2F2'),
}
STATUS_COR = {
    'Concluida': VERDE, 'Concluída': VERDE,
    'Em andamento': AMARELO,
    'Pendente': CINZA,
}

def zona_de(ibp):
    if ibp is None: return 'Sem dados'
    if ibp >= 1.5:  return 'Terreno Fertil'
    if ibp >= -1.4: return 'Defesa Oculta'
    return 'Sofrimento Patogenico'

def _baixar_logo(url):
    if not url: return None
    try:
        if url.startswith('data:'):
            import base64
            data = url.split(',', 1)[1]
            tmp = _tmpmod.NamedTemporaryFile(suffix='.png', delete=False)
            tmp.write(base64.b64decode(data))
            tmp.close()
            return tmp.name
        tmp = _tmpmod.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.close()
        req = _urllib_req.Request(url, headers={'User-Agent': 'Mozilla/5.0 NR1Map/1.0'})
        with _urllib_req.urlopen(req, timeout=10) as resp:
            with open(tmp.name, 'wb') as f_out:
                f_out.write(resp.read())
        import os as _os_ra
        return tmp.name if _os_ra.path.exists(tmp.name) and _os_ra.path.getsize(tmp.name) > 0 else None
    except Exception:
        return None

def gerar_relatorio_anual(dados=None, output_path=None):
    _dados       = dados or {}
    empresa_nome = _dados.get('empresa_nome', 'Empresa')
    empresa_cnpj = _dados.get('empresa_cnpj', '')
    responsavel  = _dados.get('responsavel', '')
    resp_tec     = _dados.get('responsavelTecnico') or {'nome': 'Dra. Lucia Kratz', 'crp': 'CRP 09/20590'}
    ciclos       = _dados.get('ciclos') or []
    acoes        = _dados.get('acoes') or []
    ano_atual    = datetime.datetime.now().year
    agora        = datetime.datetime.now(datetime.timezone.utc).strftime('%d/%m/%Y as %H:%M UTC')
    hash_uuid    = str(uuid.uuid4()).upper()

    lp_path = _baixar_logo(_dados.get('logoParceiroUrl'))
    le_path = _baixar_logo(_dados.get('logoEmpresaUrl'))
    ctx           = _dados.get('contextoEmpresa') or {}
    organograma_url = _dados.get('orgogramaUrl', '')
    cargos_lista  = _dados.get('cargos') or []

    styles = getSampleStyleSheet()
    s_h1   = ParagraphStyle('h1', fontSize=16, fontName='Helvetica-Bold', textColor=VERDE,
                             spaceAfter=4, leading=20)
    s_h2   = ParagraphStyle('h2', fontSize=12, fontName='Helvetica-Bold', textColor=ROXO,
                             spaceBefore=10, spaceAfter=4, leading=16)
    s_h3   = ParagraphStyle('h3', fontSize=10, fontName='Helvetica-Bold', textColor=AZUL,
                             spaceBefore=8, spaceAfter=3, leading=13)
    s_body = ParagraphStyle('body', fontSize=9, fontName='Helvetica', textColor=PRETO,
                             leading=13, spaceAfter=4)
    s_sub  = ParagraphStyle('sub', fontSize=8.5, fontName='Helvetica', textColor=CINZA,
                             leading=12, spaceAfter=6)
    s_cell = ParagraphStyle('cell', fontSize=8.3, fontName='Helvetica', textColor=PRETO, leading=11)
    s_badge= ParagraphStyle('badge', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white,
                             backColor=VERDE, borderPadding=3)

    def cabecalho_rodape(canvas_obj, doc):
        from reportlab.lib.utils import ImageReader
        canvas_obj.saveState()
        w, h = A4
        if lp_path:
            try:
                canvas_obj.drawImage(ImageReader(lp_path), 18*mm, h-28*mm,
                                      width=50*mm, height=14*mm, preserveAspectRatio=True)
            except Exception:
                canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE); canvas_obj.drawString(18*mm, h-24*mm, 'NR-1Map')
        else:
            canvas_obj.setFont('Helvetica-Bold', 8); canvas_obj.setFillColor(VERDE); canvas_obj.drawString(18*mm, h-24*mm, 'NR-1Map')
        if le_path:
            try:
                canvas_obj.drawImage(ImageReader(le_path), w-62*mm, h-28*mm,
                                      width=50*mm, height=14*mm, preserveAspectRatio=True)
            except Exception: pass
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(VERDE)
        canvas_obj.drawCentredString(w/2, h-32*mm, empresa_nome)
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(ROXO)
        canvas_obj.drawCentredString(w/2, h-37*mm, 'NR-1Map')
        canvas_obj.setFont('Helvetica-Bold', 9.5)
        canvas_obj.setFillColor(AZUL)
        canvas_obj.drawCentredString(w/2, h-42*mm, 'RELATORIO ANUAL CONSOLIDADO')
        canvas_obj.setStrokeColor(VERDE)
        canvas_obj.setLineWidth(1.2)
        canvas_obj.line(18*mm, h-45*mm, w-18*mm, h-45*mm)
        canvas_obj.setFont('Helvetica', 7.5)
        canvas_obj.setFillColor(CINZA)
        canvas_obj.drawString(20*mm, 12*mm, 'NR-1 Map | Portaria MTE 1.419/2024 | Documento Confidencial')
        canvas_obj.drawRightString(w-20*mm, 12*mm, f'Pagina {doc.page}')
        canvas_obj.restoreState()

    if not output_path:
        tmp = _tmpmod.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp.close()
        output_path = tmp.name

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=50*mm, bottomMargin=20*mm,
                             leftMargin=18*mm, rightMargin=18*mm)
    story = []

    # -- Capa / Identificacao --
    story.append(Paragraph(f'Relatorio Anual Consolidado {ano_atual}', s_h1))
    story.append(Paragraph(
        f'{empresa_nome} | Gestao de Riscos Psicossociais | '
        f'NR-1 / Portaria MTE 1.419/2024', s_sub))
    story.append(Spacer(1, 4*mm))

    id_rows = [
        ['Empresa', empresa_nome],
        ['CNPJ', empresa_cnpj],
        ['Responsavel', responsavel],
        ['Responsavel Tecnico', f"{resp_tec.get('nome','')} | {resp_tec.get('crp','')}"],
        ['Total de ciclos avaliados', str(len(ciclos))],
        ['Gerado em', agora],
        ['Hash de validacao', hash_uuid],
    ]
    t_id = Table([[Paragraph(r[0], ParagraphStyle('lb', fontSize=8.5, fontName='Helvetica-Bold', textColor=PRETO)),
                   Paragraph(r[1], s_cell)] for r in id_rows],
                  colWidths=[55*mm, 117*mm])
    t_id.setStyle(TableStyle([
        ('GRID',          (0,0),(-1,-1), 0.5, LINHA),
        ('BACKGROUND',    (0,0),(0,-1),  CINZA_CL),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(t_id)
    story.append(PageBreak())

    # -- Contexto Institucional --
    _ctx_items = [
        ('Setor de atuacao', ctx.get('setor', '')),
        ('Fundacao',         ctx.get('fundacao', '')),
        ('Missao / Proposito', ctx.get('missao', '')),
    ]
    _ctx_textos = [
        ('Historico e contexto organizacional', ctx.get('historico', '')),
        ('Contexto do diagnostico',             ctx.get('diagnostico', '')),
    ]
    _tem_ctx = any(v for _, v in _ctx_items) or any(v for _, v in _ctx_textos)
    if _tem_ctx:
        story.append(Paragraph('Contexto Institucional da Organizacao', s_h2))
        _tab_ctx = [[k, v] for k, v in _ctx_items if v]
        if _tab_ctx:
            _tc = Table(
                [[Paragraph(r[0], ParagraphStyle('lb', fontSize=8.5, fontName='Helvetica-Bold', textColor=PRETO)),
                  Paragraph(r[1], s_cell)] for r in _tab_ctx],
                colWidths=[55*mm, 117*mm])
            _tc.setStyle(TableStyle([
                ('GRID',       (0,0), (-1,-1), 0.5, LINHA),
                ('BACKGROUND', (0,0), (0,-1),  CINZA_CL),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(_tc)
            story.append(Spacer(1, 4*mm))
        for _label, _texto in _ctx_textos:
            if _texto:
                story.append(Paragraph(_label, s_h3))
                story.append(Paragraph(_texto, s_body))
                story.append(Spacer(1, 3*mm))
        story.append(Spacer(1, 4*mm))

    # Organograma
    if organograma_url:
        _org_path = _baixar_logo(organograma_url)
        if _org_path:
            story.append(Paragraph('Organograma da Empresa', s_h2))
            try:
                from reportlab.platypus import Image as RLImage
                story.append(RLImage(_org_path, width=169*mm, height=80*mm, kind='proportional'))
            except Exception as _e:
                print('[organograma] erro: ' + str(_e))
            story.append(Spacer(1, 4*mm))

    # Estrutura de cargos
    if cargos_lista:
        story.append(Paragraph('Estrutura Organizacional — Cargos e Hierarquia', s_h2))
        _hdr = ['Cargo', 'CBO', 'Nivel Hierarquico', 'Reporta a']
        _rows = [_hdr] + [
            [c.get('cargo',''), c.get('cbo',''), c.get('nivel',''), c.get('reportaA','')]
            for c in cargos_lista
        ]
        _tc2 = Table(_rows, colWidths=[55*mm, 22*mm, 42*mm, 50*mm], repeatRows=1)
        _tc2.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), VERDE),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',      (0,0), (-1,-1), 8),
            ('GRID',          (0,0), (-1,-1), 0.4, LINHA),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, CINZA_CL]),
            ('TOPPADDING',    (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(_tc2)
        story.append(Spacer(1, 4*mm))

    # -- 1. Evolucao Historica dos Ciclos --
    story.append(Paragraph('1. Evolucao Historica dos Ciclos', s_h2))
    story.append(Spacer(1, 2*mm))

    if not ciclos:
        story.append(Paragraph('Nenhum ciclo encontrado para esta empresa.', s_body))
    else:
        meses = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
        # Tabela comparativa
        header = [Paragraph('<b>Ciclo / Data</b>', s_cell),
                  Paragraph('<b>IBP Geral</b>', s_cell),
                  Paragraph('<b>Zona Dejours</b>', s_cell),
                  Paragraph('<b>Respondentes</b>', s_cell),
                  Paragraph('<b>Variacao</b>', s_cell)]
        rows = [header]
        ibp_anterior = None
        for cl in ciclos:
            try:
                dt = datetime.datetime.fromisoformat(cl['criadoEm'].replace('Z',''))
                dt_str = f"{dt.day}/{meses[dt.month-1]}/{dt.year}"
            except Exception:
                dt_str = cl.get('id','')[:10]
            ibp   = cl.get('ibpGeral')
            zona  = zona_de(ibp)
            cor   = ZONA_COR.get(zona, CINZA)
            ibp_str = f'{ibp:+.2f}' if ibp is not None else '--'
            n     = cl.get('totalRespostas', 0)
            if ibp_anterior is not None and ibp is not None:
                delta = ibp - ibp_anterior
                var_str = f'{delta:+.2f}'
                var_cor = VERDE if delta > 0 else (VERMELHO if delta < 0 else CINZA)
            else:
                var_str = '--'
                var_cor = CINZA
            ibp_anterior = ibp
            rows.append([
                Paragraph(dt_str, s_cell),
                Paragraph(f'<b>{ibp_str}</b>',
                          ParagraphStyle('ibp', parent=s_cell, textColor=cor, fontName='Helvetica-Bold')),
                Paragraph(zona, ParagraphStyle('zona', parent=s_cell, textColor=cor)),
                Paragraph(str(n), s_cell),
                Paragraph(var_str, ParagraphStyle('var', parent=s_cell, textColor=var_cor, fontName='Helvetica-Bold')),
            ])
        t_ciclos = Table(rows, colWidths=[35*mm, 28*mm, 60*mm, 30*mm, 19*mm])
        t_ciclos.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0),  VERDE),
            ('TEXTCOLOR',     (0,0),(-1,0),  colors.white),
            ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
            ('GRID',          (0,0),(-1,-1), 0.5, LINHA),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, CINZA_CL]),
        ]))
        story.append(t_ciclos)
        story.append(Spacer(1, 5*mm))

        # Grafico de barras horizontais (IBP por ciclo)
        story.append(Paragraph('Grafico de Evolucao do IBP Geral', s_h3))
        story.append(Spacer(1, 2*mm))
        bar_w = 140*mm
        bar_h = max(12*mm * len(ciclos), 30*mm)
        d = Drawing(bar_w, bar_h)
        centro = bar_w / 2
        escala = (bar_w/2 - 20*mm) / 5.0  # 5 = max IBP
        row_h  = bar_h / len(ciclos)
        for ci, cl in enumerate(ciclos):
            ibp = cl.get('ibpGeral', 0) or 0
            zona = zona_de(ibp)
            cor_rgb = ZONA_COR.get(zona, CINZA)
            try:
                dt = datetime.datetime.fromisoformat(cl['criadoEm'].replace('Z',''))
                lbl = f"{dt.day}/{meses[dt.month-1]}/{dt.year}"
            except Exception:
                lbl = cl.get('id','')[:8]
            y = bar_h - (ci + 1) * row_h + row_h*0.2
            bw = abs(ibp) * escala
            bx = centro if ibp >= 0 else centro - bw
            # Barra
            r = Rect(bx, y, bw, row_h*0.6,
                     fillColor=cor_rgb, strokeColor=None)
            d.add(r)
            # Label esquerda (data)
            d.add(String(centro - 2*mm, y + row_h*0.2,
                         lbl, fontSize=7, textAnchor='end', fillColor=PRETO))
            # Valor
            d.add(String(bx + bw + 2*mm if ibp >= 0 else bx - 2*mm,
                         y + row_h*0.2,
                         f'{ibp:+.2f}',
                         fontSize=7.5, fontName='Helvetica-Bold',
                         textAnchor='start' if ibp >= 0 else 'end',
                         fillColor=cor_rgb))
        # Linha central (IBP = 0)
        d.add(Line(centro, 0, centro, bar_h, strokeColor=CINZA, strokeWidth=0.5))
        story.append(d)

    story.append(Spacer(1, 6*mm))

    # -- 2. Analise Quantitativa --
    story.append(Paragraph('2. Analise Quantitativa', s_h2))
    if ciclos:
        ibps = [c['ibpGeral'] for c in ciclos if c.get('ibpGeral') is not None]
        if ibps:
            media  = sum(ibps) / len(ibps)
            maximo = max(ibps)
            minimo = min(ibps)
            total_resp = sum(c.get('totalRespostas', 0) for c in ciclos)
            variacao = ibps[-1] - ibps[0] if len(ibps) > 1 else 0
            tendencia = 'Melhora' if variacao > 0.1 else ('Piora' if variacao < -0.1 else 'Estavel')
            t_cor = VERDE if variacao > 0.1 else (VERMELHO if variacao < -0.1 else AMARELO)

            quant_rows = [
                [Paragraph('<b>Indicador</b>', s_cell), Paragraph('<b>Valor</b>', s_cell)],
                ['Media IBP no periodo', f'{media:+.2f} ({zona_de(media)})'],
                ['IBP mais alto registrado', f'{maximo:+.2f}'],
                ['IBP mais baixo registrado', f'{minimo:+.2f}'],
                ['Total de respondentes (acumulado)', str(total_resp)],
                ['Numero de ciclos avaliados', str(len(ciclos))],
                ['Variacao total (1 ciclo ao ultimo)', f'{variacao:+.2f}'],
                ['Tendencia geral', tendencia],
            ]
            t_quant = Table(
                [[Paragraph(r[0] if isinstance(r[0], str) else '', s_cell),
                  Paragraph(str(r[1]), ParagraphStyle('qv', parent=s_cell,
                    textColor=t_cor if r[1] == tendencia else PRETO,
                    fontName='Helvetica-Bold' if r[1] == tendencia else 'Helvetica'))]
                 if not isinstance(r[0], Paragraph) else r
                 for r in quant_rows],
                colWidths=[95*mm, 77*mm])
            t_quant.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,0),  VERDE),
                ('TEXTCOLOR',     (0,0),(-1,0),  colors.white),
                ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
                ('BACKGROUND',    (0,1),(0,-1),  CINZA_CL),
                ('GRID',          (0,0),(-1,-1), 0.5, LINHA),
                ('TOPPADDING',    (0,0),(-1,-1), 5),
                ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ]))
            story.append(t_quant)
    story.append(Spacer(1, 6*mm))

    # -- 3. Analise Qualitativa --
    story.append(Paragraph('3. Analise Qualitativa', s_h2))
    if ciclos and ibps:
        zona_atual = zona_de(ibps[-1])
        zona_fundo = ZONA_FUNDO.get(zona_atual, CINZA_CL)
        narrativas = {
            'Terreno Fertil': (
                'A organizacao apresenta equilibrio psicodinamico favoravel ao longo do periodo analisado. '
                'Os indices IBP indicam que as estrategias de defesa coletiva estao convertendo o sofrimento '
                'em prazer no trabalho (Dejours), com fatores motivacionais preservados (Herzberg) e necessidades '
                'basicas atendidas (Maslow). Recomenda-se manutencao das praticas de gestao e continuidade do '
                'monitoramento via Pesquisa Pulso para prevencao de retrocessos.'
            ),
            'Defesa Oculta': (
                'A organizacao apresenta sofrimento psicossocial mascarado por defesas coletivas. O IBP na zona '
                'de Defesa Oculta indica que os trabalhadores desenvolveram estrategias adaptativas para lidar com '
                'o sofrimento, porem sem resolve-lo estruturalmente. Ha risco de deterioracao caso os fatores '
                'higienicos (Herzberg) se agravem. O Plano de Acao 5W2H deve ser implementado com urgencia nas '
                'subcategorias criticas identificadas nos ciclos.'
            ),
            'Sofrimento Patogenico': (
                'ATENCAO: A organizacao apresenta indices de sofrimento psicossocial patogenico. O IBP nesta zona '
                'indica falha das estrategias de defesa coletiva, com risco ativo de adoecimento psiquico e fisico '
                'dos trabalhadores. Intervencao imediata e obrigatoria conforme NR-1 item 1.5.4.4.3. O Plano de '
                'Acao deve priorizar as subcategorias com maior criticidade e o acompanhamento deve ser semanal.'
            ),
        }
        story.append(Paragraph(
            f'Zona atual (ultimo ciclo): <b>{zona_atual}</b> | IBP: <b>{ibps[-1]:+.2f}</b>',
            ParagraphStyle('zona_txt', parent=s_body, textColor=ZONA_COR.get(zona_atual, CINZA))
        ))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(narrativas.get(zona_atual, ''), s_body))

        # Evolucao narrativa
        if len(ibps) > 1:
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph('Evolucao no periodo:', s_h3))
            for i in range(1, len(ciclos)):
                cl_ant = ciclos[i-1]
                cl_at  = ciclos[i]
                delta  = (cl_at.get('ibpGeral') or 0) - (cl_ant.get('ibpGeral') or 0)
                sinal  = 'melhora de' if delta > 0 else ('piora de' if delta < 0 else 'estabilidade em')
                try:
                    dt = datetime.datetime.fromisoformat(cl_at['criadoEm'].replace('Z',''))
                    dt_str = f"{dt.day}/{meses[dt.month-1]}/{dt.year}"
                except Exception:
                    dt_str = f'Ciclo {i+1}'
                story.append(Paragraph(
                    f'[{dt_str}] {sinal} {abs(delta):.2f} pontos IBP -- '
                    f'Zona: {zona_de(cl_at.get("ibpGeral"))}',
                    ParagraphStyle('evo', parent=s_body, leftIndent=10,
                                   textColor=VERDE if delta > 0 else (VERMELHO if delta < 0 else CINZA))
                ))
    story.append(Spacer(1, 6*mm))

    # -- 4. Resumo das Acoes --
    story.append(Paragraph('4. Resumo do Plano de Acao', s_h2))
    if acoes:
        total  = len(acoes)
        concl  = sum(1 for a in acoes if 'onclu' in a.get('status',''))
        andm   = sum(1 for a in acoes if 'andamento' in a.get('status','').lower())
        pend   = total - concl - andm
        perc   = round(concl / total * 100) if total else 0

        story.append(Paragraph(
            f'Total de acoes cadastradas: <b>{total}</b> | '
            f'Concluidas: <b>{concl}</b> ({perc}%) | '
            f'Em andamento: <b>{andm}</b> | Pendentes: <b>{pend}</b>',
            s_body))
        story.append(Spacer(1, 3*mm))

        # Tabela de acoes
        ac_header = [Paragraph('<b>Setor / CBO</b>', s_cell),
                     Paragraph('<b>Acao</b>', s_cell),
                     Paragraph('<b>Responsavel</b>', s_cell),
                     Paragraph('<b>Prazo</b>', s_cell),
                     Paragraph('<b>Status</b>', s_cell)]
        ac_rows = [ac_header]
        for a in acoes:
            st = a.get('status', 'Pendente')
            cor_st = STATUS_COR.get(st, CINZA)
            ac_rows.append([
                Paragraph(a.get('setor',''), s_cell),
                Paragraph((a.get('descricao',''))[:80], s_cell),
                Paragraph(a.get('responsavel',''), s_cell),
                Paragraph(a.get('prazo',''), s_cell),
                Paragraph(f'<b>{st}</b>',
                          ParagraphStyle('st', parent=s_cell, textColor=cor_st, fontName='Helvetica-Bold')),
            ])
        t_ac = Table(ac_rows, colWidths=[38*mm, 65*mm, 30*mm, 22*mm, 17*mm])
        t_ac.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0),  VERDE),
            ('TEXTCOLOR',     (0,0),(-1,0),  colors.white),
            ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
            ('GRID',          (0,0),(-1,-1), 0.5, LINHA),
            ('TOPPADDING',    (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, CINZA_CL]),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ]))
        story.append(t_ac)
    else:
        story.append(Paragraph('Nenhuma acao cadastrada no plano.', s_body))

    story.append(PageBreak())

    # -- 5. Assinatura --
    story.append(Paragraph('5. Assinatura e Validacao', s_h2))
    story.append(Paragraph('DOCUMENTO ASSINADO ELETRONICAMENTE',
                            ParagraphStyle('ass', parent=s_body, textColor=VERDE,
                                           fontName='Helvetica-Bold', fontSize=10)))
    story.append(Spacer(1, 3*mm))
    sig_rows = [
        ['Responsavel Tecnico:', resp_tec.get('nome', 'Dra. Lucia Kratz')],
        ['Registro Profissional:', resp_tec.get('crp', 'CRP 09/20590')],
        ['E-mail:', resp_tec.get('email', 'luciakratz@gmail.com')],
        ['Empresa avaliada:', empresa_nome],
        ['Periodo de referencia:', f'{ano_atual}'],
        ['Data e Hora da emissao:', agora],
        ['Hash UUID de validacao:', hash_uuid],
        ['Plataforma:', 'NR-1 Map | Conformidade Portaria MTE 1.419/2024'],
    ]
    t_sig = Table(
        [[Paragraph(r[0], ParagraphStyle('sl', parent=s_cell, fontName='Helvetica-Bold')),
          Paragraph(r[1], s_cell)] for r in sig_rows],
        colWidths=[55*mm, 117*mm])
    t_sig.setStyle(TableStyle([
        ('GRID',          (0,0),(-1,-1), 0.5, LINHA),
        ('BACKGROUND',    (0,0),(0,-1),  CINZA_CL),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(t_sig)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph('Responsavel pela Metodologia IBP e Plataforma NR-1 Map', s_h2))
    story.append(Paragraph('VALIDADO PELA RESPONSAVEL TECNICA DA METODOLOGIA',
                            ParagraphStyle('v2', parent=s_body, textColor=ROXO,
                                           fontName='Helvetica-Bold', fontSize=9)))
    story.append(Spacer(1, 3*mm))
    met_rows = [
        ['Responsavel pela Metodologia:', 'Dra. Lucia Kratz'],
        ['Registro Profissional:', 'CRP 09/20590'],
        ['Titulacao:', 'Doutora em Administracao | Psicologa Organizacional'],
        ['Metodologia:', 'IBP -- Indice de Balanca Psicodinamica (Dejours + Herzberg + Maslow)'],
        ['Plataforma:', 'NR-1 Map | Conformidade Portaria MTE 1.419/2024'],
    ]
    t_met = Table(
        [[Paragraph(r[0], ParagraphStyle('ml', parent=s_cell, fontName='Helvetica-Bold')),
          Paragraph(r[1], s_cell)] for r in met_rows],
        colWidths=[55*mm, 117*mm])
    t_met.setStyle(TableStyle([
        ('GRID',          (0,0),(-1,-1), 0.5, LINHA),
        ('BACKGROUND',    (0,0),(0,-1),  CINZA_CL),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(t_met)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        'Este relatorio e imutavel apos emissao e serve como documento tecnico oficial '
        'para fiscalizacao trabalhista, audiencias e processos administrativos '
        '(NR-1 / Portaria MTE 1.419/2024). O hash UUID garante unicidade e rastreabilidade.',
        s_sub))

    doc.build(story, onFirstPage=cabecalho_rodape, onLaterPages=cabecalho_rodape)
    return output_path
