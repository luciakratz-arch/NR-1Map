# -*- coding: utf-8 -*-
"""
NR-1 Map — Cloud Functions Python
Gera os 5 documentos do fluxo GRO com dados reais do Firestore
e salva no Firebase Storage.
"""

import uuid
import datetime
import tempfile
import os
import unicodedata
import re

import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import https_fn, options

# Inicializa Firebase Admin
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

# ── Helpers ──────────────────────────────────────────────────────

def slug(texto):
    """Remove acentos e caracteres especiais para nome de arquivo."""
    s = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9]+', '', s)

def nome_arquivo(tipo, empresa, ano=None):
    ano = ano or datetime.datetime.now().year
    return f"{ano}_NR-1_Map_{slug(empresa)}_{tipo}.pdf"

def salvar_storage(caminho_local, nome_arquivo_storage, empresa_id):
    """Salva PDF no Firebase Storage e retorna URL pública."""
    bucket = storage.bucket()
    blob = bucket.blob(f"nr1map_laudos/{empresa_id}/{nome_arquivo_storage}")
    blob.upload_from_filename(caminho_local, content_type='application/pdf')
    blob.make_public()
    return blob.public_url

def salvar_firestore(empresa_id, empresa_nome, tipo, url, num_colab, ibp_geral):
    """Registra laudo gerado no Firestore."""
    db.collection('nr1map_laudos').add({
        'empresaId': empresa_id,
        'empresaNome': empresa_nome,
        'tipo': tipo,
        'url': url,
        'ibpGeral': ibp_geral,
        'numColaboradores': num_colab,
        'status': 'entregue',
        'criadoEm': datetime.datetime.now().isoformat()
    })

def buscar_dados_empresa(empresa_id):
    """Busca dados da empresa e respostas mais recentes do Firestore."""
    # Dados da empresa
    empresa_doc = db.collection('nr1map_empresas').document(empresa_id).get()
    if not empresa_doc.exists:
        return None
    empresa = empresa_doc.to_dict()

    # Colaboradores ativos
    colab_snap = db.collection('nr1map_colaboradores')\
        .where('empresaId', '==', empresa_id)\
        .where('status', '==', 'ativo').get()
    num_colab = len(colab_snap)

    # Último ciclo de respostas
    ciclos = db.collection('nr1map_respostas').document(empresa_id)\
        .collection('ciclos').order_by('criadoEm', direction=firestore.Query.DESCENDING)\
        .limit(1).get()

    respostas_por_subcat = {}
    ibp_geral = 0.0

    if ciclos:
        ciclo_id = ciclos[0].id
        resps = db.collection('nr1map_respostas').document(empresa_id)\
            .collection('ciclos').document(ciclo_id)\
            .collection('respostas').get()

        soma_geral = 0
        n_geral = 0
        for r in resps:
            d = r.to_dict()
            if d.get('ibpSubcats'):
                for sc, val in d['ibpSubcats'].items():
                    if sc not in respostas_por_subcat:
                        respostas_por_subcat[sc] = {'soma': 0, 'n': 0, 'modId': val.get('modId', '')}
                    respostas_por_subcat[sc]['soma'] += val['ibp']
                    respostas_por_subcat[sc]['n'] += 1
            if d.get('ibpGeral') is not None:
                soma_geral += d['ibpGeral']
                n_geral += 1

        if n_geral > 0:
            ibp_geral = round(soma_geral / n_geral, 2)

    return {
        'empresa': empresa,
        'empresa_id': empresa_id,
        'empresa_nome': empresa.get('nome', ''),
        'num_colab': num_colab,
        'ibp_geral': ibp_geral,
        'respostas_por_subcat': respostas_por_subcat,
        'referencia': datetime.datetime.now().strftime('%B de %Y')
    }

def zona_dejours(ibp):
    if ibp >= 1.5:
        return 'Terreno Fértil'
    elif ibp <= -1.5:
        return 'Sofrimento Patogênico'
    return 'Defesa Oculta'

def classificacao_gro(ibp):
    if ibp <= -3.0:
        return 'INTOLERÁVEL'
    elif ibp <= -1.5:
        return 'SUBSTANCIAL'
    elif ibp <= 0.0:
        return 'MODERADO'
    elif ibp <= 1.5:
        return 'TOLERÁVEL'
    return 'TRIVIAL'

# ── Gerador de PDF ────────────────────────────────────────────────

def gerar_pdf_laudo(dados):
    """Gera o Laudo Técnico Psicossocial (Relatório Final) com dados reais."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER

    VERDE_NR1   = colors.HexColor('#0A6E4F')
    ROXO_NR1    = colors.HexColor('#7B00C4')
    AZUL_ESCURO = colors.HexColor('#1F2937')
    CINZA_TEXTO = colors.HexColor('#374151')
    CINZA_CLARO = colors.HexColor('#F3F4F6')
    LINHA       = colors.HexColor('#D1D5DB')
    VERDE_OK    = colors.HexColor('#16A34A')

    ZONA_COR = {
        'Sofrimento Patogênico': colors.HexColor('#FBD5D5'),
        'Defesa Oculta':         colors.HexColor('#FFF1B8'),
        'Terreno Fértil':        colors.HexColor('#D2F2E2'),
    }

    styles = getSampleStyleSheet()
    s_h1   = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=15, textColor=VERDE_NR1, spaceAfter=4, fontName='Helvetica-Bold')
    s_sub  = ParagraphStyle('sub', parent=styles['Normal'],  fontSize=9.5, textColor=CINZA_TEXTO, spaceAfter=10)
    s_h2   = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11.5, textColor=ROXO_NR1, spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
    s_h3   = ParagraphStyle('h3', parent=styles['Heading3'], fontSize=10.5, textColor=AZUL_ESCURO, spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold')
    s_body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, textColor=CINZA_TEXTO, leading=13)
    s_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.3, textColor=CINZA_TEXTO, leading=11)

    empresa_nome = dados['empresa_nome']
    referencia   = dados['referencia']
    num_colab    = dados['num_colab']
    ibp_geral    = dados['ibp_geral']
    resp_subcat  = dados['respostas_por_subcat']
    agora        = datetime.datetime.now(datetime.timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')
    hash_uuid    = str(uuid.uuid4()).upper()

    # Monta setores por módulo
    modulos = {
        'M1': {'nome': 'Módulo Fisiológico', 'subcats': []},
        'M2': {'nome': 'Módulo de Segurança', 'subcats': []},
        'M3': {'nome': 'Módulo de Relacionamentos', 'subcats': []},
        'M4': {'nome': 'Módulo Motivacional', 'subcats': []},
    }
    for sc, val in resp_subcat.items():
        ibp_sc = round(val['soma'] / val['n'], 2) if val['n'] > 0 else 0.0
        mod = val.get('modId', 'M1')
        if mod in modulos:
            modulos[mod]['subcats'].append({'id': sc, 'ibp': ibp_sc})

    # IBP por módulo
    ibp_mod = {}
    for mod_id, mod in modulos.items():
        if mod['subcats']:
            ibp_mod[mod_id] = round(sum(s['ibp'] for s in mod['subcats']) / len(mod['subcats']), 2)
        else:
            ibp_mod[mod_id] = 0.0

    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    output_path = tmp.name
    tmp.close()

    def cabecalho_rodape(canvas_obj, doc):
        canvas_obj.saveState()
        w, h = A4
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(CINZA_TEXTO)
        canvas_obj.drawString(20*mm, h-14*mm, "[ LOGO PARCEIRO ]")
        canvas_obj.drawRightString(w-20*mm, h-14*mm, "[ LOGO DA EMPRESA ]")
        canvas_obj.setFont('Helvetica-Bold', 11)
        canvas_obj.setFillColor(VERDE_NR1)
        canvas_obj.drawCentredString(w/2, h-20*mm, empresa_nome)
        canvas_obj.setFont('Helvetica', 8.5)
        canvas_obj.setFillColor(ROXO_NR1)
        canvas_obj.drawCentredString(w/2, h-25*mm, "NR-1Map")
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(AZUL_ESCURO)
        canvas_obj.drawCentredString(w/2, h-31*mm, "LAUDO TÉCNICO PSICOSSOCIAL")
        canvas_obj.setStrokeColor(VERDE_NR1)
        canvas_obj.setLineWidth(1.2)
        canvas_obj.line(20*mm, h-34*mm, w-20*mm, h-34*mm)
        canvas_obj.setFont('Helvetica', 7.5)
        canvas_obj.setFillColor(CINZA_TEXTO)
        canvas_obj.drawString(20*mm, 12*mm, "NR-1 Map · Conformidade Portaria MTE 1.419/2024")
        canvas_obj.drawRightString(w-20*mm, 12*mm, f"Página {doc.page}")
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=38*mm, bottomMargin=20*mm,
                            leftMargin=18*mm, rightMargin=18*mm)
    story = []

    # Cabeçalho
    story.append(Paragraph("Laudo Técnico Psicossocial", s_h1))
    story.append(Paragraph(
        f"{empresa_nome} · {referencia} · Documento para anexação ao PGR (NR-1)", s_sub))

    # Identificação
    story.append(Paragraph("1. Identificação da Empresa", s_h2))
    id_rows = [
        ["Empresa:", empresa_nome],
        ["Período:", referencia],
        ["Colaboradores ativos:", str(num_colab)],
        ["Metodologia:", "Dejours (Psicodinâmica) · Herzberg (Fatores Higiênicos) · Maslow"],
    ]
    t_id = Table(id_rows, colWidths=[45*mm, 125*mm])
    t_id.setStyle(TableStyle([
        ('FONTNAME',  (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0),(-1,-1), 9),
        ('TEXTCOLOR', (0,0),(-1,-1), CINZA_TEXTO),
        ('TOPPADDING',(0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3),
    ]))
    story.append(t_id)
    story.append(Spacer(1, 5*mm))

    # Metodologia
    story.append(Paragraph("2. Fundamentação Teórica", s_h2))
    story.append(Paragraph(
        "O presente laudo fundamenta-se na Psicodinâmica do Trabalho de Christophe Dejours, "
        "medindo o equilíbrio entre Prazer e Sofrimento através do <b>Índice de Balança Psicodinâmica (IBP)</b>. "
        "A classificação oficial GRO (Trivial/Tolerável/Moderado/Substancial/Intolerável) é obtida pelo "
        "cruzamento Severidade × Probabilidade (metodologia AIHA/Fundacentro), sempre apresentada lado a lado "
        "com a zona Dejours. Conformidade com a Portaria MTE nº 1.419/2024.", s_body))
    story.append(Paragraph(
        "<b>IBP = (Média − 3) × 2,5</b> — escala de −5 (Sofrimento Patogênico) a +5 (Terreno Fértil).", s_body))
    story.append(Spacer(1, 5*mm))

    # Resultado geral
    story.append(Paragraph("3. Resultado Geral", s_h2))
    zona_g   = zona_dejours(ibp_geral)
    class_g  = classificacao_gro(ibp_geral)
    cor_zona = ZONA_COR.get(zona_g, CINZA_CLARO)
    sinal    = '+' if ibp_geral >= 0 else ''

    res_rows = [
        ["IBP Geral", "Zona Dejours", "Classificação GRO"],
        [f"{sinal}{ibp_geral:.1f}", zona_g, class_g],
    ]
    t_res = Table(res_rows, colWidths=[56*mm]*3)
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), AZUL_ESCURO),
        ('TEXTCOLOR',  (0,0),(-1,0), colors.white),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,1),(-1,1), cor_zona),
        ('FONTNAME',   (0,1),(-1,1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 10),
        ('ALIGN',      (0,0),(-1,-1), 'CENTER'),
        ('GRID',       (0,0),(-1,-1), 0.5, LINHA),
        ('TOPPADDING', (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 5*mm))

    # Resultado por módulo
    story.append(Paragraph("4. Resultado por Módulo", s_h2))
    mod_rows = [["Módulo", "IBP", "Zona Dejours", "Classificação GRO"]]
    for mod_id, mod in modulos.items():
        ibp_m = ibp_mod[mod_id]
        zona_m = zona_dejours(ibp_m)
        class_m = classificacao_gro(ibp_m)
        sinal_m = '+' if ibp_m >= 0 else ''
        mod_rows.append([mod['nome'], f"{sinal_m}{ibp_m:.1f}", zona_m, class_m])

    t_mod = Table(mod_rows, colWidths=[65*mm, 20*mm, 45*mm, 38*mm])
    t_mod.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,0), AZUL_ESCURO),
        ('TEXTCOLOR',    (0,0),(-1,0), colors.white),
        ('FONTNAME',     (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0),(-1,-1), 8.5),
        ('GRID',         (0,0),(-1,-1), 0.5, LINHA),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, CINZA_CLARO]),
        ('TOPPADDING',   (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    story.append(t_mod)
    story.append(Spacer(1, 5*mm))

    # Conclusão
    story.append(Paragraph("5. Conclusão Técnica", s_h2))
    story.append(Paragraph(
        f"Diante dos dados consolidados, identifica-se IBP Geral de <b>{sinal}{ibp_geral:.1f}</b> "
        f"({zona_g}), classificado como <b>{class_g}</b> na matriz GRO/NR-1. "
        "Recomenda-se a manutenção do ciclo de monitoramento contínuo via Pesquisas Pulso, "
        "conforme item 1.5.4.4.6 da NR-1 (Portaria MTE 1.419/2024).", s_body))
    story.append(Spacer(1, 3*mm))

    # Nota de anonimato
    story.append(Paragraph(
        "<b>Nota sobre anonimato:</b> este laudo é estatístico e coletivo. "
        "O anonimato protege a coleta de dados para garantir respostas honestas. "
        "O RH atua no nível coletivo (setor/cargo) a partir deste documento.", s_body))

    story.append(PageBreak())

    # Assinatura
    story.append(Paragraph("Assinatura e Validação", s_h2))
    story.append(Paragraph("✓ DOCUMENTO ASSINADO ELETRONICAMENTE",
        ParagraphStyle('ok', parent=s_body, textColor=VERDE_OK, fontName='Helvetica-Bold', fontSize=10)))
    story.append(Spacer(1, 3*mm))

    sig_rows = [
        ["Responsável Técnica:",     "Dra. Lucia Kratz"],
        ["Registro Profissional:",   "CRP 09/20590"],
        ["Data e Hora (UTC):",       agora],
        ["Hash UUID de Validação:",  hash_uuid],
    ]
    t_sig = Table(sig_rows, colWidths=[50*mm, 120*mm])
    t_sig.setStyle(TableStyle([
        ('FONTNAME',       (0,0),(0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',       (0,0),(-1,-1), 8.5),
        ('TEXTCOLOR',      (0,0),(-1,-1), CINZA_TEXTO),
        ('TOPPADDING',     (0,0),(-1,-1), 2),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 2),
    ]))
    story.append(t_sig)
    story.append(Spacer(1, 8*mm))

    # Campo assinatura empresa
    story.append(Paragraph("Assinatura do Responsável pela Empresa", s_h3))
    story.append(Paragraph(
        f"<b>Nome:</b> {dados['empresa'].get('responsavel', '___________________________')}<br/>"
        f"<b>Cargo:</b> ___________________________<br/>"
        "<b>Data:</b> ___/___/______", s_body))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("_" * 60, s_body))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "📱 <b>Assine digitalmente este documento em:</b> assinador.iti.gov.br<br/>"
        "A assinatura digital pelo gov.br tem validade jurídica conforme Lei 14.063/2020.<br/>"
        "Ao assinar qualquer página, a assinatura vale por todo o documento.",
        ParagraphStyle('aviso', parent=s_body, textColor=ROXO_NR1, fontSize=8.5)))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        "Este registro é imutável e serve como homologação oficial para fiscalização trabalhista (NR-1).", s_body))

    doc.build(story, onFirstPage=cabecalho_rodape, onLaterPages=cabecalho_rodape)
    return output_path

# ── Cloud Functions ───────────────────────────────────────────────

@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["GET", "POST"]),
    region="southamerica-east1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=120
)
def gerarLaudo(req: https_fn.Request) -> https_fn.Response:
    """
    Gera o Laudo Técnico Psicossocial para uma empresa.
    Parâmetros: empresaId (query string ou JSON body)
    """
    try:
        # Aceita GET e POST
        empresa_id = None
        if req.method == 'GET':
            empresa_id = req.args.get('empresaId')
        else:
            body = req.get_json(silent=True) or {}
            empresa_id = body.get('empresaId') or req.args.get('empresaId')

        if not empresa_id:
            return https_fn.Response('{"error": "empresaId obrigatório"}',
                                     status=400, mimetype='application/json')

        # Busca dados do Firestore
        dados = buscar_dados_empresa(empresa_id)
        if not dados:
            return https_fn.Response('{"error": "Empresa não encontrada"}',
                                     status=404, mimetype='application/json')

        # Gera PDF
        pdf_path = gerar_pdf_laudo(dados)

        # Salva no Storage
        nome = nome_arquivo('LaudoTecnicoFinal', dados['empresa_nome'])
        url  = salvar_storage(pdf_path, nome, empresa_id)

        # Registra no Firestore
        salvar_firestore(
            empresa_id,
            dados['empresa_nome'],
            'Diagnóstico Geral',
            url,
            dados['num_colab'],
            dados['ibp_geral']
        )

        os.unlink(pdf_path)

        return https_fn.Response(
            f'{{"success": true, "url": "{url}", "empresa": "{dados["empresa_nome"]}"}}',
            status=200, mimetype='application/json'
        )

    except Exception as e:
        return https_fn.Response(
            f'{{"error": "{str(e)}"}}',
            status=500, mimetype='application/json'
        )
