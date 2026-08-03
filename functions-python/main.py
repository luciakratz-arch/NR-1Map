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
    """Busca dados completos da empresa e ciclo mais recente do Firestore."""
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

    # Ciclo mais recente com respostas (atualizadoEm > criadoEm como fallback)
    ciclo_doc = None
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

            # Subcategorias
            if d.get('ibpSubcats'):
                for sc_id, val in d['ibpSubcats'].items():
                    if sc_id not in ibp_subcats:
                        ibp_subcats[sc_id] = {
                            'soma':  0.0, 'n': 0,
                            'modId': val.get('modId', 'M1'),
                            'nome':  val.get('nome', sc_id),
                        }
                    ibp_subcats[sc_id]['soma'] += val.get('ibp', 0.0)
                    ibp_subcats[sc_id]['n']    += 1

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

    # Acoes do plano (resumo)
    acoes = []
    try:
        acoes_snap = db.collection('nr1map_plano_acao') \
            .where('empresaId', '==', empresa_id).limit(20).get()
        for a in acoes_snap:
            d = a.to_dict()
            acoes.append({
                'descricao': d.get('acao', '') or d.get('descricao', ''),
                'status':    d.get('status', ''),
                'classif':   d.get('classif', '') or d.get('classificacao', ''),
            })
    except Exception:
        pass

    # Responsavel tecnico
    resp_tec = empresa.get('responsavelTecnico') or {}
    if not resp_tec.get('nome'):
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
        'referencia': datetime.datetime.now().strftime('%B de %Y'),
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

def gerar_pdf_por_tipo(dados, tipo):
    """Roteia para o gerador correto conforme tipo solicitado."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    tmp.close()

    if tipo in ('laudo_tecnico', 'relatorio_anual', 'diagnostico_geral', None, ''):
        from gerar_relatorio_final import gerar_relatorio_final
        payload = {
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
        "logoParceiroUrl":     dados.get("logoParceiroUrl", 'https://luciakratz-arch.github.io/NR-1Map/assets/logo-nr1map.png'),
        "logoEmpresaUrl":      dados.get("logoEmpresaUrl", ''),
        }
        gerar_relatorio_final(payload, output_path=tmp.name)

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

    else:
        # Fallback: laudo tecnico
        from gerar_relatorio_final import gerar_relatorio_final
        payload = {
            "empresa": dados.get("empresa_nome", ""),
            "responsavelTecnico": dados.get("responsavelTecnico") or {},
            "referencia": dados.get("referencia", ""),
            "colaboradoresAtivos": dados.get("num_colab", 0),
            "respondentes": dados.get("respondentes", 0),
            "ibpGeral": dados.get("ibp_geral"),
            "ibpModulos": dados.get("ibpModulos") or {},
            "ibpSubcats": dados.get("ibpSubcats") or {},
            "porUnidade": dados.get("porUnidade") or [],
            "porCargo": dados.get("porCargo") or [],
            "acoes": dados.get("acoes") or [],
        }
        gerar_relatorio_final(payload, output_path=tmp.name)

    return tmp.name


def gerar_pdf_laudo(dados):
    """Compatibilidade retroativa — gera laudo tecnico."""
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
            return https_fn.Response('{"error": "empresaId obrigatório"}',
                                     status=400, mimetype='application/json')

        # Busca dados do Firestore
        dados = buscar_dados_empresa(empresa_id)
        if not dados:
            return https_fn.Response('{"error": "Empresa não encontrada"}',
                                     status=404, mimetype='application/json')

        # Tipo de documento solicitado
        tipo = req.args.get('tipo') or (req.get_json(silent=True) or {}).get('tipo') or 'laudo_tecnico'

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
            dados['num_colab'],
            dados['ibp_geral']
        )

        os.unlink(pdf_path)

        return https_fn.Response(
            f'{{"success": true, "url": "{url}", "tipo": "{tipo}", "empresa": "{dados["empresa_nome"]}"}}',
            status=200, mimetype='application/json'
        )

    except Exception as e:
        return https_fn.Response(
            f'{{"error": "{str(e)}"}}',
            status=500, mimetype='application/json'
        )
