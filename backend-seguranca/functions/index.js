// Funções de proteção do banco antigo (projeto entrevista-inicial).
// Rodam no servidor do Google. Aqui moram as decisões de "quem é quem".
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");
admin.initializeApp();
Object.assign(exports, require("./colab"));  // NR-1 Map: colaborador sem login
Object.assign(exports, require("./aceite"));
Object.assign(exports, require("./sso"));
Object.assign(exports, require("./cadastro"));  // NR-1 Map: cadastro público de empresa sem senha padrão  // NR-1 Map: aceite de contrato pelo link

const ADMINS = ["luciakratz@gmail.com", "contato@luciakratz.com.br"];
const REGIAO = "southamerica-east1";

function souAdminEmail(email) { return ADMINS.includes(String(email || "").toLowerCase()); }
function souAdmin(token) {
  return token.email_verified === true && ADMINS.includes(String(token.email || "").toLowerCase());
}

// marcarPapel: coloca na conta de login a "etiqueta" que as regras do banco leem
// (empresaId para RH, parceiroId para parceiro).
//  - A administradora pode marcar qualquer e-mail cadastrado (passa { email }).
//  - Qualquer pessoa pode marcar a PRÓPRIA conta, desde que o e-mail dela esteja verificado
//    e exista no cadastro de empresas ou de parceiros.
exports.marcarPapel = onCall({ region: REGIAO, cors: true }, async (req) => {
  if (!req.auth) throw new HttpsError("unauthenticated", "Entre na sua conta primeiro.");
  const t = req.auth.token;
  const admin_ = souAdmin(t);
  const pedido = req.data && typeof req.data.email === "string" ? req.data.email.trim() : "";
  let emailBruto, uid;

  if (pedido) {
    emailBruto = pedido;
    try { uid = (await admin.auth().getUserByEmail(pedido.toLowerCase())).uid; }
    catch (e) { throw new HttpsError("not-found", "Não existe conta de login com esse e-mail."); }
  } else {
    if (t.email_verified !== true) throw new HttpsError("failed-precondition", "O e-mail desta conta ainda não foi verificado.");
    emailBruto = String(t.email || "");
    uid = req.auth.uid;
  }
  if (!emailBruto) throw new HttpsError("invalid-argument", "Conta sem e-mail.");

  const variantes = Array.from(new Set([emailBruto, emailBruto.toLowerCase()]));
  const db = admin.firestore();
  const [emp, par, n1emp, n1par, n1pf] = await Promise.all([
    db.collection("nself_empresas").where("email", "in", variantes).limit(1).get(),
    db.collection("nself_parceiros").where("email", "in", variantes).limit(1).get(),
    db.collection("nr1map_empresas").where("email", "in", variantes).limit(1).get(),
    db.collection("nr1map_parceiros").where("email", "in", variantes).limit(1).get(),
    db.collection("nr1map_usuarios_pf").where("email", "in", variantes).limit(1).get(),
  ]);
  // Marcar a conta de OUTRA pessoa: a administradora marca qualquer uma; o gestor da empresa marca quem é da própria empresa;
  // o parceiro marca as empresas e clientes cadastrados por ele. Nunca a própria pessoa por conta alheia.
  if (pedido && !admin_) {
    const papel = String(t.nr1Papel || ""), nivel = String(t.nr1Nivel || "");
    const empresaDoChamador = String(t.nr1EmpresaId || ""), parceiroDoChamador = String(t.nr1ParceiroId || "");
    const gestor = papel === "empresa" || (papel === "usuario" && ["rh", "gestor"].includes(nivel));
    const alvoPf = n1pf.empty ? null : n1pf.docs[0].data();
    const alvoEmpresa = n1emp.empty ? null : n1emp.docs[0].data();
    let permitido = false;
    if (gestor && empresaDoChamador && alvoPf && String(alvoPf.empresaId || "") === empresaDoChamador) permitido = true;
    if (papel === "parceiro" && parceiroDoChamador) {
      if (alvoEmpresa && String(alvoEmpresa.parceiroId || alvoEmpresa.parceiro || "") === parceiroDoChamador) permitido = true;
      if (alvoPf && String(alvoPf.parceiro || "") === parceiroDoChamador) permitido = true;
    }
    if (!permitido) throw new HttpsError("permission-denied", "Você não pode marcar essa conta.");
  }
  const ehAdmin = souAdminEmail(emailBruto);
  const achouNself = !(emp.empty && par.empty);
  const achouNr1 = !(n1emp.empty && n1par.empty && n1pf.empty);
  if (!achouNself && !achouNr1 && !ehAdmin) throw new HttpsError("permission-denied", "Este e-mail não está cadastrado como empresa ou parceiro.");

  const user = await admin.auth().getUser(uid);
  const novo = Object.assign({}, user.customClaims || {});
  // 9&Self (campos antigos, NÃO mudar de nome): empresaId, parceiroId, role
  if (achouNself) {
    delete novo.empresaId; delete novo.parceiroId;
    if (!emp.empty) novo.empresaId = emp.docs[0].id;
    if (!par.empty) novo.parceiroId = par.docs[0].id;
    novo.role = !emp.empty ? "rh" : "parceiro";
  }
  // NR-1 Map (campos com prefixo próprio, para nunca misturar com o 9&Self)
  delete novo.nr1EmpresaId; delete novo.nr1ParceiroId; delete novo.nr1Papel; delete novo.nr1Nivel;
  if (!n1emp.empty) { novo.nr1EmpresaId = n1emp.docs[0].id; novo.nr1Papel = "empresa"; novo.nr1Nivel = "gestor"; }
  else if (!n1par.empty) { novo.nr1ParceiroId = n1par.docs[0].id; novo.nr1Papel = "parceiro"; }
  else if (!n1pf.empty) {
    const u = n1pf.docs[0].data();
    novo.nr1EmpresaId = String(u.empresaId || ""); novo.nr1Papel = "usuario";
    novo.nr1Nivel = String(u.nivelAcesso || u.tipo || "colaborador").toLowerCase();   // colaborador | rh | gestor
  }
  // Administradora: marcada no servidor (e-mail verificado e na lista), nunca pelo navegador
  if (ehAdmin) novo.adminCentral = true; else delete novo.adminCentral;
  await admin.auth().setCustomUserClaims(uid, novo);
  return { ok: true, empresaId: novo.empresaId || null, parceiroId: novo.parceiroId || null,
           nr1Papel: novo.nr1Papel || null, nr1EmpresaId: novo.nr1EmpresaId || null, nr1ParceiroId: novo.nr1ParceiroId || null, admin: !!novo.adminCentral };
});

// ─────────────────────────────────────────────────────────────
//  LEMBRETES DOS CÓDIGOS "AGUARDANDO" (e-mail aos 7 e aos 14 dias)
//  Janela de 3 dias para cada lembrete, para não disparar para códigos antigos
//  e para cobrir um dia em que a função não rodou. Cada lembrete sai uma vez só.
// ─────────────────────────────────────────────────────────────
const { onSchedule } = require("firebase-functions/v2/scheduler");
const DIA = 86400000;
const SITE_9SELF = "https://luciakratz-arch.github.io/9-Self/index.html";
const ASSINATURA = "Dra. Lucia Kratz<br>Gestora do 9&amp;Self";
const ESTADOS_AGUARDANDO = ["disponivel", "Pendente", "pendente"];
const LEMBRETES = [
  { chave: "lembreteAuto7Em", de: 7, ate: 10, assunto: "Seu teste 9&Self está esperando por você" },
  { chave: "lembreteAuto14Em", de: 14, ate: 17, assunto: "Lembrete: seu teste 9&Self ainda não foi feito" },
];

function esc(s) { return String(s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

function montarEmail(v, assunto) {
  const nome = esc(String(v.nomeDestinatario || v.nome || "").trim().split(" ")[0]) || "tudo bem";
  const link = SITE_9SELF + "?code=" + encodeURIComponent(v.codigo);
  return {
    subject: assunto,
    html: `<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#2c1810;line-height:1.6;max-width:560px">
<p>Olá, ${nome}!</p>
<p>Passando para lembrar do seu teste 9&amp;Self, que ainda não foi feito. Ele leva poucos minutos.</p>
<p><b>Seu código:</b> ${esc(v.codigo)}<br><b>Acesse:</b> <a href="${link}">${link}</a></p>
<p>Se você já concluiu o teste, pode desconsiderar este e-mail. Qualquer dúvida, é só responder esta mensagem.</p>
<p style="margin-top:24px">${ASSINATURA}</p></div>`,
  };
}

// Calcula quem receberia lembrete agora. Não envia nada.
async function calcularLembretes(agora) {
  const db = admin.firestore();
  const snap = await db.collection("nself_codigos").where("status", "in", ESTADOS_AGUARDANDO).get();
  const alvos = [];
  snap.forEach((d) => {
    const v = d.data();
    const email = String(v.email || "").trim();
    if (!email || !v.codigo || !v.criadoEm) return;
    const dias = (agora - v.criadoEm.toMillis()) / DIA;
    for (const l of LEMBRETES) {
      if (dias >= l.de && dias < l.ate && !v[l.chave]) { alvos.push({ id: d.id, ref: d.ref, v, lembrete: l, dias: Math.floor(dias) }); break; }
    }
  });
  return alvos;
}

// Simulação para a administradora: mostra quantos e quais lembretes sairiam agora (sem enviar).
exports.simularLembretes = onCall({ region: REGIAO, cors: true }, async (req) => {
  if (!req.auth || !souAdmin(req.auth.token)) throw new HttpsError("permission-denied", "Só a administradora.");
  const alvos = await calcularLembretes(Date.now());
  return { total: alvos.length, itens: alvos.map((a) => ({ codigo: a.v.codigo, dias: a.dias, lembrete: a.lembrete.de, para: String(a.v.email).replace(/^(.).*(@.*)$/, "$1***$2") })) };
});

// Roda todo dia às 10h (horário de Brasília) e envia os lembretes.
exports.lembrarCodigosAguardando = onSchedule({ region: REGIAO, schedule: "0 10 * * *", timeZone: "America/Sao_Paulo" }, async () => {
  const alvos = await calcularLembretes(Date.now());
  const db = admin.firestore();
  let enviados = 0;
  for (const a of alvos) {
    try {
      await db.collection("nr1map_emails").add({ to: String(a.v.email).trim(), message: montarEmail(a.v, a.lembrete.assunto) });
      await a.ref.update({ [a.lembrete.chave]: admin.firestore.FieldValue.serverTimestamp() });
      enviados++;
    } catch (e) { console.error("lembrete falhou", a.id, e.message); }
  }
  console.log("lembretes enviados:", enviados, "de", alvos.length);
});
