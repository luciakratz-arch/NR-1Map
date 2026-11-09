// NR-1 Map — Disparo de pesquisas (VERSÃO SEGURA)
// Mudanças em relação à versão anterior:
//  1) só envia para quem está LOGADO no painel (confere o login do Firebase a cada chamada);
//  2) limite de destinatários por chamada e por usuário por dia, e respeita a cota do Gmail;
//  3) todo texto que vai dentro do e-mail é "limpo" (nome e empresa não podem injetar HTML ou links falsos);
//  4) o nome do "callback" só aceita letras, números e sublinhado;
//  5) o link da pesquisa usa o domínio oficial nr1-maps.com.br.

var FIREBASE_API_KEY = 'AIzaSyDnrgaY8R0Zetkr18uHQJAZXIUa4EwDnv4'; // chave PÚBLICA do Firebase (aparece no site; não é segredo)
var BASE_LINK = 'https://nr1-maps.com.br/colaborador.html?token=';
var MAX_POR_CHAMADA = 100;
var MAX_POR_USUARIO_DIA = 300;

function doGet(e)  { return tratar(e); }
function doPost(e) { return tratar(e); }

function tratar(e) {
  var cb = (e && e.parameter && e.parameter.callback) || null;
  if (cb && !/^[A-Za-z0-9_]{1,40}$/.test(cb)) cb = null;
  try {
    var dados = lerDados(e);
    var usuario = verificarLogin(dados.idToken);
    if (!usuario) return resposta({ erro: 'Entre no painel do NR-1 Map para enviar.' }, cb);

    var tipo = dados.tipo === 'pulso' ? 'pulso' : 'diagnostico';
    var canal = ['E-mail', 'Ambos', 'WhatsApp'].indexOf(dados.canal) >= 0 ? dados.canal : 'WhatsApp';
    var empresa = limpaTexto(dados.empresa || 'sua empresa', 80);
    var prazo = Math.max(1, Math.min(365, parseInt(dados.prazo || 7, 10) || 7));
    var lista = Array.isArray(dados.colaboradores) ? dados.colaboradores : [];
    if (!lista.length) return resposta({ erro: 'Nenhum colaborador recebido.' }, cb);
    if (lista.length > MAX_POR_CHAMADA) return resposta({ erro: 'No máximo ' + MAX_POR_CHAMADA + ' pessoas por envio. Divida em lotes.' }, cb);

    var querEmail = (canal === 'E-mail' || canal === 'Ambos');
    if (querEmail) {
      var pedidos = lista.filter(function (c) { return c && c.email; }).length;
      if (pedidos > MailApp.getRemainingDailyQuota()) return resposta({ erro: 'Cota diária de e-mails esgotada. Tente amanhã.' }, cb);
      if (!reservarCota(usuario.uid, pedidos)) return resposta({ erro: 'Limite diário de envios por e-mail atingido para este usuário.' }, cb);
    }

    var prazoTxt = prazo <= 1 ? '24 horas' : prazo === 30 ? '1 mês' : prazo === 60 ? '2 meses' : prazo === 90 ? '3 meses' : prazo + ' dias';
    var tipotxt = tipo === 'pulso' ? 'Pesquisa Pulso' : 'Diagnóstico de Bem-Estar';
    var enviados = [], erros = [], waLinks = [];

    lista.forEach(function (c) {
      c = c || {};
      var token = String(c.token || '').replace(/[^A-Za-z0-9]/g, '').slice(0, 12);
      var nome = limpaTexto(c.nome || 'Colaborador', 80);
      if (!token) { erros.push({ nome: nome, canal: 'geral', erro: 'Sem código de acesso' }); return; }
      var link = BASE_LINK + token;

      if (querEmail) {
        var email = String(c.email || '').trim();
        if (!/^[^\s@<>"']+@[^\s@<>"']+\.[^\s@<>"']+$/.test(email)) {
          erros.push({ nome: nome, canal: 'email', erro: 'E-mail inválido ou não cadastrado' });
        } else {
          try {
            GmailApp.sendEmail(email, tipotxt + ' — ' + empresa, '', { htmlBody: montarEmailHTML(nome, empresa, tipotxt, link, prazoTxt), name: 'NR-1 Map — ' + empresa });
            enviados.push({ nome: nome, canal: 'email', status: 'ok' });
          } catch (err) { erros.push({ nome: nome, canal: 'email', erro: 'Falha no envio' }); }
        }
      }
      if (canal === 'WhatsApp' || canal === 'Ambos') {
        var wpp = String(c.whatsapp || '').replace(/[^0-9]/g, '').slice(0, 13);
        var msg = 'Olá ' + nome + '!\n\n' + empresa + ' está realizando uma pesquisa de bem-estar no trabalho.\n\nSuas respostas são 100% anônimas.\n\nAcesse pelo link abaixo e responda em poucos minutos:\n' + link + '\n\nO link expira em ' + prazoTxt + '.';
        waLinks.push({ nome: nome, whatsapp: wpp, url: wpp ? 'https://wa.me/55' + wpp + '?text=' + encodeURIComponent(msg) : null });
      }
    });

    return resposta({ ok: true, enviados: enviados.length, erros: erros, waLinks: waLinks }, cb);
  } catch (err) {
    return resposta({ erro: 'Não foi possível processar o envio.' }, cb);
  }
}

function lerDados(e) {
  var dados = {};
  if (e && e.postData && e.postData.contents) dados = JSON.parse(e.postData.contents);
  else if (e && e.parameter) dados = e.parameter.dados ? JSON.parse(e.parameter.dados) : e.parameter;
  return dados || {};
}

// Confere o login do Firebase. Devolve { uid, email } ou null.
function verificarLogin(idToken) {
  if (!idToken || typeof idToken !== 'string' || idToken.length < 100) return null;
  try {
    var r = UrlFetchApp.fetch('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=' + FIREBASE_API_KEY, {
      method: 'post', contentType: 'application/json', muteHttpExceptions: true,
      headers: { Referer: 'https://nr1-maps.com.br/' },
      payload: JSON.stringify({ idToken: idToken })
    });
    if (r.getResponseCode() !== 200) return null;
    var u = (JSON.parse(r.getContentText()).users || [])[0];
    return u && u.localId ? { uid: u.localId, email: u.email || '' } : null;
  } catch (err) { return null; }
}

// Limite diário por usuário (evita uso abusivo mesmo com login válido)
function reservarCota(uid, qtd) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var p = PropertiesService.getScriptProperties();
    var hoje = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyyMMdd');
    var chave = 'q_' + uid + '_' + hoje;
    var usado = parseInt(p.getProperty(chave) || '0', 10);
    if (usado + qtd > MAX_POR_USUARIO_DIA) return false;
    p.setProperty(chave, String(usado + qtd));
    return true;
  } finally { lock.releaseLock(); }
}

function esc(v) {
  return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
}
function limpaTexto(v, max) { return String(v == null ? '' : v).replace(/[\r\n\t]+/g, ' ').replace(/[<>]/g, '').trim().slice(0, max); }

function montarEmailHTML(nome, empresa, tipotxt, link, prazoTxt) {
  nome = esc(nome); empresa = esc(empresa); tipotxt = esc(tipotxt); prazoTxt = esc(prazoTxt || '7 dias');
  return '<!DOCTYPE html><html><body style="font-family:Inter,sans-serif;background:#f4f7f5;margin:0;padding:20px;">' +
    '<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">' +
    '<div style="background:#0A6E4F;padding:28px 32px;"><div style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:#fff;">NR-1<span style="color:#12A073;">Map</span></div></div>' +
    '<div style="padding:32px;">' +
    '<p style="font-size:15px;color:#2A2E2C;margin-bottom:8px;">Olá, <strong>' + nome + '</strong>!</p>' +
    '<p style="font-size:14px;color:#6B7370;line-height:1.7;margin-bottom:20px;"><strong style="color:#0A6E4F;">' + empresa + '</strong> está realizando uma <strong>' + tipotxt + '</strong> de bem-estar no trabalho.<br/>' +
    'Suas respostas são <strong>100% anônimas</strong> e tabuladas por cargo — ninguém terá acesso às suas respostas individuais.</p>' +
    '<a href="' + esc(link) + '" style="display:block;background:#0A6E4F;color:#fff;text-align:center;padding:14px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;margin-bottom:20px;">Responder agora →</a>' +
    '<p style="font-size:12px;color:#9CA3AF;line-height:1.6;">O link expira em ' + prazoTxt + '. Se tiver dúvidas, entre em contato com o RH da sua empresa.</p></div>' +
    '<div style="background:#f4f7f5;padding:16px 32px;text-align:center;"><p style="font-size:11px;color:#9CA3AF;margin:0;">NR-1 Map · Gestão de Riscos Psicossociais · Portaria MTE nº 1.419/2024</p></div>' +
    '</div></body></html>';
}

function resposta(obj, callback) {
  var json = JSON.stringify(obj);
  if (callback) return ContentService.createTextOutput(callback + '(' + json + ')').setMimeType(ContentService.MimeType.JAVASCRIPT);
  return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
}

// Rode UMA vez no editor (botão Executar) para o Google pedir as permissões novas.
function autorizar() {
  UrlFetchApp.fetch('https://www.google.com', { muteHttpExceptions: true });
  Logger.log('Autorizado. Pode implantar a nova versão.');
}
