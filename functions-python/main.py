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
    logo_parceiro_url = 'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png'
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
        'referencia': (lambda d: d.strftime('%d/%m/%Y'))(
            datetime.datetime.fromisoformat(ciclo_data.get('criadoEm', datetime.datetime.now().isoformat()).replace('Z',''))
            if ciclo_data.get('criadoEm') else datetime.datetime.now()
        ),
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
        'logoParceiroUrl':  'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png',
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
                                   "https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png",
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
                                   "https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png",
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
        if not dados.get('logoParceiroUrl'):
            dados['logoParceiroUrl'] = 'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png'

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
