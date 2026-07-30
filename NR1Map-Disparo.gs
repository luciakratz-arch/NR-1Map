// NR-1 Map — Google Apps Script Disparo de Pesquisas
// Recebe lista de colaboradores e dispara e-mails automaticamente via Gmail
// Retorna links de WhatsApp para abertura sequencial no frontend

function doGet(e)  { return handleDisparo(e); }
function doPost(e) { return handleDisparo(e); }

function handleDisparo(e) {
  try {
    // Suporte a GET (params) e POST (payload JSON)
    var cb = (e.parameter && e.parameter.callback) || null;
    var dados;
    if (e.postData && e.postData.contents) {
      dados = JSON.parse(e.postData.contents);
    } else {
      dados = e.parameter || {};
      if (dados.dados) dados = JSON.parse(dados.dados);
    }

    var tipo       = dados.tipo       || 'diagnostico';
    var canal      = dados.canal      || 'WhatsApp';
    var empresa    = dados.empresa    || 'sua empresa';
    var prazo      = parseInt(dados.prazo || 7, 10);
    var colaboradores = dados.colaboradores || [];

    var prazoTxt;
    if (prazo <= 1)       prazoTxt = '24 horas';
    else if (prazo < 30)  prazoTxt = prazo + ' dias';
    else if (prazo === 30) prazoTxt = '1 mês';
    else if (prazo === 60) prazoTxt = '2 meses';
    else if (prazo === 90) prazoTxt = '3 meses';
    else                   prazoTxt = prazo + ' dias';

    if (colaboradores.length === 0) {
      return resposta({ erro: 'Nenhum colaborador recebido.' }, cb);
    }

    var base = 'https://luciakratz-arch.github.io/NR-1Map/colaborador.html?token=';
    var tipotxt = tipo === 'pulso' ? 'Pesquisa Pulso' : 'Diagnóstico de Bem-Estar';

    var enviados  = [];
    var erros     = [];
    var waLinks   = [];

    colaboradores.forEach(function(c) {
      var link = base + c.token;
      var nome = c.nome || 'Colaborador';

      // ── E-MAIL ──────────────────────────────────────────────
      if (canal === 'E-mail' || canal === 'Ambos') {
        if (c.email) {
          try {
            var assunto = tipotxt + ' — ' + empresa;
            var corpo   = montarEmailHTML(nome, empresa, tipotxt, link, prazoTxt);
            GmailApp.sendEmail(c.email, assunto, '', { htmlBody: corpo, name: 'NR-1 Map — ' + empresa });
            enviados.push({ nome: nome, canal: 'email', status: 'ok' });
          } catch(err) {
            erros.push({ nome: nome, canal: 'email', erro: err.message });
          }
        } else {
          erros.push({ nome: nome, canal: 'email', erro: 'E-mail não cadastrado' });
        }
      }

      // ── WHATSAPP (link para abrir no frontend) ───────────────
      if (canal === 'WhatsApp' || canal === 'Ambos') {
        var wpp = (c.whatsapp || '').replace(/[^0-9]/g, '');
        var msgTxt = 'Olá ' + nome + '!\n\n' +
          empresa + ' está realizando uma pesquisa de bem-estar no trabalho.\n\n' +
          'Suas respostas são 100% anônimas.\n\n' +
          'Acesse pelo link abaixo e responda em poucos minutos:\n' +
          link + '\n\nO link expira em ' + prazoTxt + '.';
        waLinks.push({
          nome: nome,
          whatsapp: wpp,
          url: wpp ? 'https://wa.me/55' + wpp + '?text=' + encodeURIComponent(msgTxt) : null
        });
      }
    });

    return resposta({
      ok: true,
      enviados: enviados.length,
      erros: erros,
      waLinks: waLinks
    }, cb);

  } catch(err) {
    return resposta({ erro: err.message }, cb);
  }
}

function montarEmailHTML(nome, empresa, tipotxt, link, prazoTxt) {
  prazoTxt = prazoTxt || '7 dias';
  return '<!DOCTYPE html><html><body style="font-family:Inter,sans-serif;background:#f4f7f5;margin:0;padding:20px;">' +
    '<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">' +
    '<div style="background:#0A6E4F;padding:28px 32px;">' +
    '<div style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:#fff;">NR-1<span style="color:#12A073;">Map</span></div>' +
    '</div>' +
    '<div style="padding:32px;">' +
    '<p style="font-size:15px;color:#2A2E2C;margin-bottom:8px;">Olá, <strong>' + nome + '</strong>!</p>' +
    '<p style="font-size:14px;color:#6B7370;line-height:1.7;margin-bottom:20px;">' +
    '<strong style="color:#0A6E4F;">' + empresa + '</strong> está realizando uma ' +
    '<strong>' + tipotxt + '</strong> de bem-estar no trabalho.<br/>' +
    'Suas respostas são <strong>100% anônimas</strong> e tabuladas por cargo — ninguém terá acesso às suas respostas individuais.' +
    '</p>' +
    '<a href="' + link + '" style="display:block;background:#0A6E4F;color:#fff;text-align:center;padding:14px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;margin-bottom:20px;">Responder agora →</a>' +
    '<p style="font-size:12px;color:#9CA3AF;line-height:1.6;">O link expira em ' + prazoTxt + '. Se tiver dúvidas, entre em contato com o RH da sua empresa.</p>' +
    '</div>' +
    '<div style="background:#f4f7f5;padding:16px 32px;text-align:center;">' +
    '<p style="font-size:11px;color:#9CA3AF;margin:0;">NR-1 Map · Gestão de Riscos Psicossociais · Portaria MTE nº 1.419/2024</p>' +
    '</div>' +
    '</div></body></html>';
}

function resposta(obj, callback) {
  var json = JSON.stringify(obj);
  if (callback) {
    return ContentService
      .createTextOutput(callback + '(' + json + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService
    .createTextOutput(json)
    .setMimeType(ContentService.MimeType.JSON);
}
