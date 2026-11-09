// NR-1 MAP: cadastro público de empresa (pelo link do site). Antes criava uma conta com uma SENHA PADRÃO igual para todas.
// Agora só registra o pedido como "pendente"; a administradora aprova e a empresa recebe um link para criar a própria senha.
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");

const REGIAO = "southamerica-east1";
const t = (v, max) => String(v == null ? "" : v).trim().slice(0, max);

exports.nr1CadastroEmpresa = onCall({ region: REGIAO, cors: true }, async (req) => {
  const d = req.data || {};
  if (t(d.site, 100)) return { ok: true };                       // campo-armadilha para robôs: finge que deu certo
  const nome = t(d.nome, 160), responsavel = t(d.responsavel, 120), email = t(d.email, 160).toLowerCase();
  const cnpj = t(d.cnpj, 30).replace(/\D/g, ""), whatsapp = t(d.whatsapp, 30);
  const numColaboradores = Math.max(0, Math.min(100000, parseInt(d.numColaboradores, 10) || 0));
  if (!nome || !responsavel || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || cnpj.length !== 14 || !whatsapp) {
    throw new HttpsError("invalid-argument", "Preencha nome, responsável, CNPJ, e-mail e WhatsApp.");
  }
  const db = admin.firestore();
  const ja = await db.collection("nr1map_empresas").where("cnpj", "in", [cnpj, t(d.cnpj, 30)]).limit(1).get();
  if (ja.empty) {
    await db.collection("nr1map_empresas").add({
      nome, responsavel, cnpj: t(d.cnpj, 30), email, whatsapp, numColaboradores,
      setor: t(d.setor, 80), segmento: t(d.setor, 80), origem: t(d.origem, 80),
      status: "pendente", tipo: "pj", criadoPor: "auto-cadastro", primeiroAcesso: true,
      criadoEm: new Date().toISOString(),
    });
  }
  return { ok: true };            // mesma resposta, exista ou não, para não revelar quem já é cliente
});
