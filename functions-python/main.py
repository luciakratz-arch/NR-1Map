# -*- coding: utf-8 -*-
"""
NR-1 Map — Cloud Functions Python
Gera os 5 documentos do fluxo GRO com dados reais do Firestore
e salva no Firebase Storage.
"""

import uuid
import datetime

# Logo NR-1Map embutida como base64 — evita download bloqueado pelo GitHub Pages
LOGO_NR1MAP_BASE64 = 'data:image/png;base64,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'
import tempfile
import os
import unicodedata
import re
import json

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
    ts = datetime.datetime.now().strftime('%m%d%H%M')
    return f"{ano}_NR-1_Map_{slug(empresa)}_{tipo}_{ts}.pdf"

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

def _buscar_cargos(empresa_id):
    """Busca cargos cadastrados da empresa com hierarquia."""
    try:
        snaps = db.collection('nr1map_cargos').where('empresaId', '==', empresa_id).get()
        cargos = []
        for s in snaps:
            d = s.to_dict()
            cargos.append({
                'cargo':    d.get('cargo', ''),
                'cbo':      d.get('cbo', ''),
                'nivel':    d.get('nivel', ''),
                'reportaA': d.get('reportaA', ''),
                'colab':    d.get('numColaboradores', 0),
            })
        return cargos
    except Exception as e:
        print("erro _buscar_cargos: " + str(e))
        return []

def buscar_dados_empresa(empresa_id, ciclo_id_fixo=None):
    """Busca dados completos da empresa. Se ciclo_id_fixo informado, usa esse ciclo."""
    # Empresa
    empresa_doc = db.collection('nr1map_empresas').document(empresa_id).get()
    if not empresa_doc.exists:
        return None
    empresa = empresa_doc.to_dict()

    # Colaboradores ativos
    colab_snap = db.collection('nr1map_colaboradores') \
        .where('empresaId', '==', empresa_id) \
        .where('status', '==', 'ativo').get()
    num_colab = len(colab_snap)

    # Monta dicionario cargo/unidade por colaborador para segmentacao
    cargo_por_colab = {}
    for c in colab_snap:
        d = c.to_dict()
        cargo_por_colab[c.id] = {
            'cargo':   d.get('cargo', ''),
            'cbo':     d.get('cbo', ''),
            'unidade': d.get('unidade', '') or d.get('departamento', ''),
        }

    # Ciclo: usa ciclo_id_fixo se fornecido, senao busca o mais recente
    ciclo_doc = None
    if ciclo_id_fixo:
        try:
            ciclo_doc = db.collection('nr1map_respostas').document(empresa_id) \
                .collection('ciclos').document(ciclo_id_fixo).get()
            if not ciclo_doc.exists:
                ciclo_doc = None
        except Exception:
            ciclo_doc = None

    if not ciclo_doc:
        try:
            ciclos = db.collection('nr1map_respostas').document(empresa_id) \
                .collection('ciclos') \
                .order_by('atualizadoEm', direction=firestore.Query.DESCENDING) \
                .limit(1).get()
            if ciclos:
                ciclo_doc = ciclos[0]
        except Exception:
            pass

    if not ciclo_doc:
        try:
            ciclos = db.collection('nr1map_respostas').document(empresa_id) \
                .collection('ciclos') \
                .order_by('criadoEm', direction=firestore.Query.DESCENDING) \
                .limit(1).get()
            if ciclos:
                ciclo_doc = ciclos[0]
        except Exception:
            pass

    # Agregar respostas do ciclo
    ibp_subcats   = {}   # {sc_id: {ibp, n, modId, nome}}
    ibp_modulos   = {}   # {M1..M4: ibp_medio}
    por_colab_id  = {}   # {colaboradorId: {ibp, cargo, cbo, unidade}}
    soma_geral    = 0.0
    n_geral       = 0

    ciclo_data = {}  # fallback — definido antes do if para uso posterior
    if ciclo_doc:
        ciclo_id = ciclo_doc.id
        # Prioriza totalRespostas/ibpGeral do cicloDoc se existirem
        ciclo_data = ciclo_doc.to_dict()
        if ciclo_data.get('totalRespostas', 0) > 0 and ciclo_data.get('ibpGeral') is not None:
            soma_geral = ciclo_data['ibpGeral'] * ciclo_data['totalRespostas']
            n_geral    = ciclo_data['totalRespostas']

        resps = db.collection('nr1map_respostas').document(empresa_id) \
            .collection('ciclos').document(ciclo_id) \
            .collection('respostas').get()

        for r in resps:
            d = r.to_dict()
            colab_id = d.get('colaboradorId', '')
            ibp_r    = d.get('ibpGeral')

            if ibp_r is not None and n_geral == 0:
                soma_geral += ibp_r
                n_geral    += 1

            # Subcategorias — suporta tanto dict {ibp, modId, nome} quanto float direto
            if d.get('ibpSubcats'):
                for sc_id, val in d['ibpSubcats'].items():
                    # Derivar modId do prefixo da subcat (ex: '2.1' -> 'M2')
                    if isinstance(val, dict):
                        ibp_val = float(val.get('ibp') or val.get('valor') or 0.0)
                        mod_id  = val.get('modId') or ('M' + sc_id.split('.')[0]) if '.' in sc_id else 'M1'
                        nome    = val.get('nome') or sc_id
                    else:
                        # val e um numero direto
                        ibp_val = float(val or 0.0)
                        mod_id  = ('M' + sc_id.split('.')[0]) if '.' in sc_id else 'M1'
                        nome    = sc_id
                    if sc_id not in ibp_subcats:
                        ibp_subcats[sc_id] = {
                            'soma':  0.0, 'n': 0,
                            'modId': mod_id,
                            'nome':  nome,
                        }
                    ibp_subcats[sc_id]['soma']  += ibp_val
                    ibp_subcats[sc_id]['n']     += 1
                    # Atualizar modId se vier mais completo
                    if mod_id and mod_id != 'M1':
                        ibp_subcats[sc_id]['modId'] = mod_id

            # Por colaborador (para segmentacao cargo/unidade)
            info_c = cargo_por_colab.get(colab_id, {})
            chave  = colab_id or r.id
            if chave not in por_colab_id:
                por_colab_id[chave] = {
                    'ibp_soma': 0.0, 'n': 0,
                    'cargo':   d.get('cargo', '')   or info_c.get('cargo', ''),
                    'cbo':     d.get('cbo', '')     or info_c.get('cbo', ''),
                    'unidade': d.get('setor', '')   or info_c.get('unidade', ''),
                }
            por_colab_id[chave]['ibp_soma'] += (ibp_r or 0.0)
            por_colab_id[chave]['n']        += 1

    # IBP geral
    ibp_geral = round(soma_geral / n_geral, 2) if n_geral > 0 else None

    # IBP medio por subcategoria
    ibp_subcats_final = {}
    for sc_id, sc in ibp_subcats.items():
        ibp_subcats_final[sc_id] = {
            'ibp':   round(sc['soma'] / sc['n'], 2) if sc['n'] > 0 else 0.0,
            'n':     sc['n'],
            'modId': sc['modId'],
            'nome':  sc['nome'],
        }

    # IBP por modulo
    mod_acum = {}
    for sc in ibp_subcats_final.values():
        m = sc['modId']
        if m not in mod_acum:
            mod_acum[m] = {'soma': 0.0, 'n': 0}
        mod_acum[m]['soma'] += sc['ibp']
        mod_acum[m]['n']    += 1
    ibp_modulos = {m: round(v['soma']/v['n'], 2) for m, v in mod_acum.items() if v['n'] > 0}

    # Segmentacao por unidade
    unidade_acum = {}
    for c in por_colab_id.values():
        u = c.get('unidade') or 'Nao informado'
        if u not in unidade_acum:
            unidade_acum[u] = {'soma': 0.0, 'n': 0}
        unidade_acum[u]['soma'] += (c['ibp_soma'] / c['n'] if c['n'] > 0 else 0.0)
        unidade_acum[u]['n']    += 1
    por_unidade = [
        {'unidade': u, 'n': v['n'], 'ibp': round(v['soma']/v['n'], 2)}
        for u, v in unidade_acum.items()
    ]

    # Segmentacao por cargo/CBO
    cargo_acum = {}
    for c in por_colab_id.values():
        chave_c = (c.get('cargo') or 'Nao informado', c.get('cbo') or '', c.get('unidade') or '')
        if chave_c not in cargo_acum:
            cargo_acum[chave_c] = {'soma': 0.0, 'n': 0}
        cargo_acum[chave_c]['soma'] += (c['ibp_soma'] / c['n'] if c['n'] > 0 else 0.0)
        cargo_acum[chave_c]['n']    += 1
    por_cargo = [
        {'cargo': k[0], 'cbo': k[1], 'unidade': k[2], 'n': v['n'], 'ibp': round(v['soma']/v['n'], 2)}
        for k, v in cargo_acum.items()
    ]

    # Acoes do plano — filtra por cicloId quando disponivel
    acoes = []
    ciclo_id_para_acoes = ciclo_id_fixo or (ciclo_doc.id if ciclo_doc else None)
    try:
        # Busca TODAS as acoes da empresa e filtra no Python
        # (evita problema com documentos que nao tem o campo cicloId)
        todos_snap = db.collection('nr1map_plano_acao') \
            .where('empresaId', '==', empresa_id).limit(200).get()

        # Verificar se o ciclo tem acoes proprias
        tem_acoes_proprias = any(
            a.to_dict().get('cicloId') == ciclo_id_para_acoes
            for a in todos_snap
        ) if ciclo_id_para_acoes else False

        for a in todos_snap:
            d = a.to_dict()
            ciclo_doc_id = d.get('cicloId') or ''
            if ciclo_id_para_acoes:
                if ciclo_doc_id == ciclo_id_para_acoes:
                    pass  # acao propria do ciclo — inclui
                elif not ciclo_doc_id and not tem_acoes_proprias:
                    pass  # acao legada sem cicloId — inclui se ciclo nao tem acoes proprias
                else:
                    continue  # acao de outro ciclo — pula
            acoes.append({
                'descricao':   d.get('acao', '') or d.get('descricao', ''),
                'status':      d.get('status', ''),
                'classif':     d.get('classif', '') or d.get('classificacao', ''),
                'setor':       d.get('setor', ''),
                'responsavel': d.get('responsavel', ''),
                'prazo':       d.get('prazo', ''),
                'cicloId':     ciclo_doc_id,
            })
    except Exception as e:
        print(f"[buscar_dados_empresa] erro acoes: {e}")

    # Responsavel tecnico da metodologia — sempre fixo como Dra. Lucia Kratz
    # O campo responsavelTecnico do Firestore refere-se ao responsavel da empresa (campo separado)
    # Os PDFs sempre exibem DUAS assinaturas: (1) responsavel da empresa e (2) Dra. Lucia Kratz
    resp_tec = {'nome': 'Dra. Lucia Kratz', 'crp': 'CRP 09/20590', 'email': 'luciakratz@gmail.com'}

    # Logo do parceiro — fallback para logo NR-1 Map se nao houver parceiro
    logo_parceiro_url = LOGO_NR1MAP_BASE64
    parceiro_id = empresa.get('parceiroId')
    if parceiro_id:
        try:
            parc_doc = db.collection('nr1map_parceiros').document(parceiro_id).get()
            if parc_doc.exists and parc_doc.to_dict().get('logo_url'):
                logo_parceiro_url = parc_doc.to_dict()['logo_url']
        except Exception:
            pass  # fallback NR-1 Map ja definido acima

    return {
        # campos legados (outros geradores usam esses)
        'empresa':              empresa,
        'empresa_id':           empresa_id,
        'empresa_nome':         empresa.get('nome', ''),
        'num_colab':            num_colab,
        'ibp_geral':            ibp_geral,
        'respostas_por_subcat': {
            sc: {'soma': v['ibp'] * v['n'], 'n': v['n'], 'modId': v['modId']}
            for sc, v in ibp_subcats_final.items()
        },
        'referencia': (lambda _cr: (
            (datetime.datetime.utcfromtimestamp(_cr.seconds) + datetime.timedelta(hours=-3)).strftime('%d/%m/%Y')
            if hasattr(_cr, 'seconds') else
            (datetime.datetime.fromisoformat(_cr.replace('Z','')) + datetime.timedelta(hours=-3)).strftime('%d/%m/%Y')
            if isinstance(_cr, str) and _cr.endswith('Z') else
            datetime.datetime.fromisoformat(_cr.replace('Z','')).strftime('%d/%m/%Y')
            if isinstance(_cr, str) else
            datetime.datetime.now().strftime('%d/%m/%Y')
        ))(ciclo_data.get('criadoEm')) if ciclo_data.get('criadoEm') else datetime.datetime.now().strftime('%d/%m/%Y'),
        # campos novos para gerar_relatorio_final
        'empresa_cnpj':         empresa.get('cnpj', ''),
        'responsavel':          empresa.get('responsavel', ''),
        'responsavelTecnico':   resp_tec,
        'respondentes':         n_geral,
        'ibpModulos':           ibp_modulos,
        'ibpSubcats':           ibp_subcats_final,
        'porUnidade':           por_unidade,
        'porCargo':             por_cargo,
        'acoes':                acoes,
        'logoParceiroUrl':      logo_parceiro_url,
        'logoEmpresaUrl':       empresa.get('logo_url', ''),
        # Contexto institucional para o Laudo Tecnico
        'contextoEmpresa':      empresa.get('contextoEmpresa') or {},
        'orgogramaUrl':         empresa.get('orgogramaUrl', ''),
        # Cargos cadastrados com hierarquia
        'cargos':               _buscar_cargos(empresa_id),
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

def buscar_todos_ciclos(empresa_id):
    """Busca todos os ciclos da empresa para o Relatorio Anual."""
    empresa_doc = db.collection('nr1map_empresas').document(empresa_id).get()
    if not empresa_doc.exists:
        return None
    empresa = empresa_doc.to_dict()

    # Buscar todos os ciclos
    try:
        ciclos_snap = db.collection('nr1map_respostas').document(empresa_id)             .collection('ciclos').get()
    except Exception:
        ciclos_snap = []

    ciclos = []
    for doc in ciclos_snap:
        d = doc.to_dict()
        if not d:
            continue
        ibp = d.get('ibpGeral')
        if ibp is None:
            continue
        ciclos.append({
            'id':          doc.id,
            'criadoEm':    d.get('criadoEm', ''),
            'ibpGeral':    ibp,
            'totalRespostas': d.get('totalRespostas', 0),
            'ibpModulos':  d.get('ibpModulos') or {},
            'laudoUrl':    d.get('laudoUrl', ''),
            'planoUrl':    d.get('planoUrl', ''),
        })

    # Ordenar cronologicamente
    ciclos.sort(key=lambda x: x.get('criadoEm', ''))

    # Buscar acoes do plano
    acoes = []
    try:
        acoes_snap = db.collection('nr1map_plano_acao')             .where('empresaId', '==', empresa_id).limit(200).get()
        for a in acoes_snap:
            d = a.to_dict()
            acoes.append({
                'setor':       d.get('setor', ''),
                'descricao':   (d.get('acao') or d.get('descricao', '')).replace('[IA] ', '').replace('[IA]', ''),
                'responsavel': d.get('responsavel', ''),
                'prazo':       d.get('prazo', ''),
                'status':      d.get('status', 'Pendente'),
                'cicloId':     d.get('cicloId', ''),
            })
    except Exception:
        pass

    # Responsavel tecnico fixo
    resp_tec = {'nome': 'Dra. Lucia Kratz', 'crp': 'CRP 09/20590', 'email': 'luciakratz@gmail.com'}

    # IBP do ciclo mais recente para salvar_firestore
    ibp_ultimo = ciclos[-1]['ibpGeral'] if ciclos else None

    return {
        'empresa_nome':     empresa.get('nome', ''),
        'empresa_cnpj':     empresa.get('cnpj', ''),
        'responsavel':      empresa.get('responsavel', ''),
        'responsavelTecnico': resp_tec,
        'ciclos':           ciclos,
        'acoes':            acoes,
        'num_colab':        empresa.get('numColaboradores', 0),
        'ibp_geral':        ibp_ultimo,
        'logoEmpresaUrl':   empresa.get('logo_url', ''),
        'logoParceiroUrl':  LOGO_NR1MAP_BASE64,
        'contextoEmpresa':  empresa.get('contextoEmpresa') or {},
        'orgogramaUrl':     empresa.get('orgogramaUrl', ''),
        'cargos':           _buscar_cargos(empresa_id),
    }


def gerar_pdf_por_tipo(dados, tipo):
    """Roteia para o gerador correto. laudo_tecnico usa SEMPRE gerar_relatorio_final completo."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    tmp.close()

    if tipo == 'laudo_tecnico':
        # ROTA EXPLÍCITA — nunca pode cair no else ou em outro gerador
        print(f"[gerarLaudo] ROTA laudo_tecnico → gerar_relatorio_final")
        from gerar_relatorio_final import gerar_relatorio_final
        payload_laudo = {
            "empresa":             dados.get("empresa_nome", ""),
            "cnpj":                dados.get("empresa_cnpj", ""),
            "responsavel":         dados.get("responsavel", ""),
            "responsavelTecnico":  dados.get("responsavelTecnico") or {},
            "referencia":          dados.get("referencia", ""),
            "colaboradoresAtivos": dados.get("num_colab", 0),
            "respondentes":        dados.get("respondentes", 0),
            "ibpGeral":            dados.get("ibp_geral"),
            "ibpModulos":          dados.get("ibpModulos") or {},
            "ibpSubcats":          dados.get("ibpSubcats") or {},
            "porUnidade":          dados.get("porUnidade") or [],
            "porCargo":            dados.get("porCargo") or [],
            "acoes":               dados.get("acoes") or [],
            "logoParceiroUrl":     dados.get("logoParceiroUrl") or
                                   "https://luciakratz-arch.github.io/NR-1Map/nr-1maps%20logo.png",
            "logoEmpresaUrl":      dados.get("logoEmpresaUrl", ""),
        }
        gerar_relatorio_final(payload_laudo, output_path=tmp.name)

    elif tipo == 'mapa_risco':
        from gerar_mapa_risco import gerar_mapa_risco
        gerar_mapa_risco(dados=dados, output_path=tmp.name)

    elif tipo == 'inventario':
        from gerar_inventario_riscos import gerar_inventario
        gerar_inventario(dados=dados, output_path=tmp.name)

    elif tipo == 'plano_5w2h':
        from gerar_plano_5w2h import gerar_5w2h
        gerar_5w2h(dados=dados, output_path=tmp.name)

    elif tipo == 'acompanhamento':
        from gerar_acompanhamento import gerar_acompanhamento
        gerar_acompanhamento(dados=dados, output_path=tmp.name)

    elif tipo == 'relatorio_anual':
        from gerar_relatorio_anual import gerar_relatorio_anual
        gerar_relatorio_anual(dados=dados, output_path=tmp.name)

    else:
        # Tipo nao reconhecido
        print(f"[gerarLaudo] tipo='{tipo}' nao mapeado — usando gerar_relatorio_final como fallback seguro")
        from gerar_relatorio_final import gerar_relatorio_final
        payload_fallback = {
            "empresa":             dados.get("empresa_nome", ""),
            "cnpj":                dados.get("empresa_cnpj", ""),
            "responsavel":         dados.get("responsavel", ""),
            "responsavelTecnico":  dados.get("responsavelTecnico") or {},
            "referencia":          dados.get("referencia", ""),
            "colaboradoresAtivos": dados.get("num_colab", 0),
            "respondentes":        dados.get("respondentes", 0),
            "ibpGeral":            dados.get("ibp_geral"),
            "ibpModulos":          dados.get("ibpModulos") or {},
            "ibpSubcats":          dados.get("ibpSubcats") or {},
            "porUnidade":          dados.get("porUnidade") or [],
            "porCargo":            dados.get("porCargo") or [],
            "acoes":               dados.get("acoes") or [],
            "logoParceiroUrl":     dados.get("logoParceiroUrl") or
                                   "https://luciakratz-arch.github.io/NR-1Map/nr-1maps%20logo.png",
            "logoEmpresaUrl":      dados.get("logoEmpresaUrl", ""),
        }
        gerar_relatorio_final(payload_fallback, output_path=tmp.name)

    return tmp.name


def gerar_pdf_laudo(dados):
    """Compatibilidade retroativa."""""
    return gerar_pdf_por_tipo(dados, 'laudo_tecnico')


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
            return https_fn.Response(json.dumps({"error": "empresaId obrigatorio"}),
                                     status=400, mimetype='application/json')

        # Tipo definido PRIMEIRO — usado antes de qualquer outra logica
        body_json = req.get_json(silent=True) or {}
        tipo = req.args.get('tipo') or body_json.get('tipo') or 'laudo_tecnico'

        # Extrai cicloId
        ciclo_id_req = req.args.get('cicloId') or body_json.get('cicloId') or None

        # Relatorio anual busca TODOS os ciclos
        if tipo == 'relatorio_anual':
            dados = buscar_todos_ciclos(empresa_id)
        else:
            dados = buscar_dados_empresa(empresa_id, ciclo_id_fixo=ciclo_id_req)
        if not dados:
            return https_fn.Response(json.dumps({"error": "Empresa nao encontrada"}),
                                     status=404, mimetype='application/json')

        # FIX: logos do body JS sobrescrevem as do Firestore (garante que chegam ao PDF)
        if body_json.get('logoEmpresaUrl'):
            dados['logoEmpresaUrl'] = body_json['logoEmpresaUrl']
        if body_json.get('logoParceiroUrl'):
            dados['logoParceiroUrl'] = body_json['logoParceiroUrl']

        # Garante fallback de logo parceiro nunca vazio
        if not dados.get('logoParceiroUrl') or not dados['logoParceiroUrl'].startswith('data:'):
            dados['logoParceiroUrl'] = LOGO_NR1MAP_BASE64

        # Gera PDF
        pdf_path = gerar_pdf_por_tipo(dados, tipo)

        # Nome do arquivo por tipo
        nomes_tipo = {
            'laudo_tecnico':    'LaudoTecnicoFinal',
            'relatorio_anual':  'LaudoTecnicoFinal',
            'mapa_risco':       'MapaDeRisco',
            'inventario':       'InventarioDeRiscos',
            'plano_5w2h':       'Plano5W2H',
            'acompanhamento':   'Acompanhamento',
        }
        nome_tipo_str = nomes_tipo.get(tipo, 'LaudoTecnicoFinal')
        nome = nome_arquivo(nome_tipo_str, dados['empresa_nome'])
        url  = salvar_storage(pdf_path, nome, empresa_id)

        # Registra no Firestore
        salvar_firestore(
            empresa_id,
            dados['empresa_nome'],
            tipo,
            url,
            dados.get('num_colab', 0),
            dados.get('ibp_geral')
        )

        os.unlink(pdf_path)

        return https_fn.Response(
            json.dumps({"success": True, "url": url, "tipo": tipo, "empresa": dados["empresa_nome"]}),
            status=200, mimetype='application/json'
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500, mimetype='application/json'
        )
