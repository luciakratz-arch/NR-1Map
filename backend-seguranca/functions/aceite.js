// NR-1 MAP: aceite do contrato pelo link (sem login). A tela não lê nem grava direto no banco:
// o servidor acha o contrato pelo código do link (tokenAceite), registra o aceite e cria a empresa.
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");

const REGIAO = "southamerica-east1";

function validarToken(t) {
  const token = typeof t === "string" ? t.trim() : "";
  if (!/^[A-Za-z0-9_-]{6,80}$/.test(token)) throw new HttpsError("invalid-argument", "Link inválido.");
  return token;
}
async function acharContrato(token) {
  const snap = await admin.firestore().collection("nr1map_contratos").where("tokenAceite", "==", token).limit(1).get();
  return snap.empty ? null : snap.docs[0];
}
// Timestamps do Firestore viram texto (o navegador não sabe lê-los vindos de função)
function limpar(v) {
  if (v && typeof v.toDate === "function") return v.toDate().toISOString();
  if (Array.isArray(v)) return v.map(limpar);
  if (v && typeof v === "object") { const o = {}; for (const k of Object.keys(v)) o[k] = limpar(v[k]); return o; }
  return v;
}
function texto(v, max) { return String(v == null ? "" : v).trim().slice(0, max); }

// 1) Carregar o contrato pelo link.
exports.aceiteCarregar = onCall({ region: REGIAO, cors: true }, async (req) => {
  const token = validarToken(req.data && req.data.token);
  const doc = await acharContrato(token);
  if (!doc) return { estado: "invalido" };
  const c = limpar(doc.data());
  if (c.status === "assinado") return { estado: "assinado", hashAceite: c.hashAceite || token };
  return { estado: "ok", contratoId: doc.id, contrato: c };
});

// 2) Registrar o aceite e cadastrar a empresa.
exports.aceiteAssinar = onCall({ region: REGIAO, cors: true }, async (req) => {
  const token = validarToken(req.data && req.data.token);
  const d = req.data || {};
  const cli = d.cliente && typeof d.cliente === "object" ? d.cliente : {};
  const dadosCliente = {
    nome: texto(cli.nome, 160), cnpj: texto(cli.cnpj, 30), setor: texto(cli.setor, 80), cidade: texto(cli.cidade, 80),
    endereco: texto(cli.endereco, 200), cep: texto(cli.cep, 12), responsavel: texto(cli.responsavel, 120),
    cargo: texto(cli.cargo, 80), email: texto(cli.email, 160), whatsapp: texto(cli.whatsapp, 30),
  };
  if (!dadosCliente.nome || !dadosCliente.cnpj || !dadosCliente.email) throw new HttpsError("invalid-argument", "Preencha nome, CNPJ e e-mail.");
  const pacote = ["6m", "12m"].includes(d.pacote) ? d.pacote : "";

  const db = admin.firestore();
  const doc = await acharContrato(token);
  if (!doc) throw new HttpsError("not-found", "Contrato não encontrado.");
  const agora = new Date().toISOString();
  const hash = "ACE-" + Date.now().toString(36).toUpperCase() + "-" + Math.random().toString(36).substr(2, 8).toUpperCase();

  await db.runTransaction(async (tx) => {
    const atual = await tx.get(doc.ref);
    const ct = atual.data();
    if (ct.status === "assinado") throw new HttpsError("failed-precondition", "Este contrato já foi assinado.");
    const c = ct.comercial || {};
    const unitBase = c.valorUnit || 0, nColab = c.nColab || 0;
    const desc = pacote === "6m" ? 0.05 : pacote === "12m" ? 0.08 : 0;
    const meses = pacote === "6m" ? 6 : pacote === "12m" ? 12 : 0;
    const valorFinal = nColab * unitBase * (1 - desc) * (meses || 1);   // calculado aqui, nunca confiado ao navegador
    tx.update(doc.ref, { status: "assinado", assinadoEm: agora, hashAceite: hash, cliente: dadosCliente, pacote, desconto: desc, meses, valorFinal, ipAceite: "registrado via servidor" });
    tx.set(db.collection("nr1map_empresas").doc(), {
      nome: dadosCliente.nome, cnpj: dadosCliente.cnpj, setor: dadosCliente.setor, cidade: dadosCliente.cidade, endereco: dadosCliente.endereco,
      responsavel: dadosCliente.responsavel, email: dadosCliente.email, whatsapp: dadosCliente.whatsapp,
      numColab: c.nColab || 0, tipo: c.modalidade === "mensal" ? "mensal" : "uso-unico", faixa: c.faixaLabel || "",
      status: "ativo", contratoId: doc.id, contratoTipo: "enterprise", hashContrato: hash, criadoEm: agora, criadoPor: "aceite-automatico",
    });
  });
  return { ok: true, hash };
});
