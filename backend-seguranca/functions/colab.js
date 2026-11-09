// NR-1 MAP: colaborador que responde SEM login, só com o código.
// A tela nunca mais lê nem grava direto no banco: tudo passa por estas funções.
// A resposta da empresa é anônima (sem código, sem uid). O resultado pessoal vai para o
// histórico da conta do colaborador (nr1map_historico_usuario/{uid}), que só ele vê ao fazer login.
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const admin = require("firebase-admin");

const REGIAO = "southamerica-east1";
const SETE_DIAS = 7 * 86400000;

function validarFormatoCodigo(c) {
  const codigo = typeof c === "string" ? c.trim() : "";
  if (!/^[A-Za-z0-9_-]{4,40}$/.test(codigo)) throw new HttpsError("invalid-argument", "Código inválido.");
  return codigo;
}
async function acharToken(codigo) {
  const snap = await admin.firestore().collection("nr1map_tokens").where("codigo", "==", codigo).limit(1).get();
  return snap.empty ? null : snap.docs[0];
}
function expirou(d) {
  const fim = d.expiraEm ? new Date(d.expiraEm).getTime() : d.criadoEm ? new Date(d.criadoEm).getTime() + SETE_DIAS : 0;
  return Date.now() > fim;
}
function numeroLimitado(v, min, max) {
  const n = Number(v);
  if (!isFinite(n)) throw new HttpsError("invalid-argument", "Resposta inválida.");
  return Math.min(max, Math.max(min, n));
}

// 1) Entrar com o código: confere e devolve só o necessário para montar o questionário.
exports.colabEntrar = onCall({ region: REGIAO, cors: true }, async (req) => {
  const codigo = validarFormatoCodigo(req.data && req.data.codigo);
  const doc = await acharToken(codigo);
  if (!doc) return { estado: "invalido" };
  const t = doc.data();
  if (t.usado) return { estado: "usado" };
  if (expirou(t)) return { estado: "expirado" };
  const db = admin.firestore();
  const pesquisaId = t.pesquisaId || doc.id;
  const [sel, str] = await Promise.all([
    db.collection("nr1map_selecoes").doc(String(t.empresaId)).get(),
    db.collection("nr1map_streak").doc(`${t.empresaId}_${pesquisaId}`).get(),
  ]);
  return {
    estado: "ok",
    empresaId: t.empresaId, pesquisaId, tipo: t.tipo || "pulso",
    empresaNome: t.empresaNome || "", cargo: t.cargo || "", cbo: t.cbo || "", setor: t.setor || "",
    selecao: sel.exists ? sel.data() : null,
    streak: str.exists ? (str.data().streak || 0) : 0,
  };
});

// 2) Enviar respostas: grava a resposta anônima, atualiza o ciclo, guarda o resultado pessoal e usa o código.
exports.colabEnviar = onCall({ region: REGIAO, cors: true }, async (req) => {
  const codigo = validarFormatoCodigo(req.data && req.data.codigo);
  const entrada = req.data || {};
  const respostasIn = entrada.respostas && typeof entrada.respostas === "object" ? entrada.respostas : null;
  if (!respostasIn || Object.keys(respostasIn).length === 0 || Object.keys(respostasIn).length > 300) throw new HttpsError("invalid-argument", "Respostas inválidas.");
  const respostas = {};
  for (const k of Object.keys(respostasIn)) {
    if (!/^[A-Za-z0-9_-]{1,40}$/.test(k)) throw new HttpsError("invalid-argument", "Resposta inválida.");
    respostas[k] = numeroLimitado(respostasIn[k], -5, 5);
  }
  const subIn = entrada.ibpSubcats && typeof entrada.ibpSubcats === "object" ? entrada.ibpSubcats : {};
  const ibpSubcats = {};
  for (const k of Object.keys(subIn).slice(0, 100)) {
    if (!/^[A-Za-z0-9_.-]{1,40}$/.test(k)) continue;   // as áreas têm ponto no nome: "1.1", "2.3"
    ibpSubcats[k] = { ibp: numeroLimitado(subIn[k] && subIn[k].ibp, -5, 5), modId: String((subIn[k] && subIn[k].modId) || "").slice(0, 40) };
  }
  const ibpGeral = Math.round(numeroLimitado(entrada.ibpGeral, -5, 5) * 100) / 100;
  const zona = String(entrada.zona || "").slice(0, 60);

  const db = admin.firestore();
  const doc = await acharToken(codigo);
  if (!doc) throw new HttpsError("not-found", "Código não encontrado.");
  const agora = new Date();
  const dataStr = agora.toLocaleDateString("pt-BR", { month: "long", year: "numeric", timeZone: "America/Sao_Paulo" });

  await db.runTransaction(async (tx) => {
    const tdoc = await tx.get(doc.ref);
    const t = tdoc.data();
    if (t.usado) throw new HttpsError("failed-precondition", "Este código já foi usado.");
    if (expirou(t)) throw new HttpsError("failed-precondition", "Este código expirou.");
    const pesquisaId = t.pesquisaId || doc.id;
    const empresaId = String(t.empresaId);
    const refCiclo = db.collection("nr1map_respostas").doc(empresaId).collection("ciclos").doc(pesquisaId);
    const refResp = refCiclo.collection("respostas").doc();
    const refColab = db.collection("nr1map_respostas_colab").doc(`${empresaId}_${pesquisaId}`);
    const refHist = db.collection("nr1map_historico_usuario").doc(t.colaboradorId ? String(t.colaboradorId) : "token_" + codigo);
    const [ciclo, colab] = await Promise.all([tx.get(refCiclo), tx.get(refColab)]);

    const totalAnterior = ciclo.exists ? (ciclo.data().totalRespostas || 0) : 0;
    const ibpAnterior = ciclo.exists ? (ciclo.data().ibpGeral || 0) : 0;
    const novoTotal = totalAnterior + 1;
    const novoIbp = Math.round(((ibpAnterior * totalAnterior + ibpGeral) / novoTotal) * 100) / 100;

    // resposta da empresa: sem código e sem uid (anônima)
    tx.set(refResp, { empresaId, pesquisaId, tipo: t.tipo || "pulso", cargo: t.cargo || "", cbo: t.cbo || "", setor: t.setor || "",
      respostas, ibpSubcats, ibpGeral, zona, respondidoEm: agora.toISOString() });
    tx.set(refCiclo, { tipo: t.tipo === "diagnostico" ? "geral" : "pulso", empresaId, ibpGeral: novoIbp, totalRespostas: novoTotal,
      criadoEm: ciclo.exists ? ciclo.data().criadoEm : agora.toISOString(), atualizadoEm: agora.toISOString() }, { merge: true });
    tx.set(refColab, { historico: admin.firestore.FieldValue.arrayUnion({ ibp: ibpGeral, data: dataStr }),
      streak: ((colab.exists ? colab.data().streak : 0) || 0) + 1 }, { merge: true });
    // resultado pessoal: só o dono da conta lê, ao entrar com login
    const subcats = {};
    for (const k of Object.keys(ibpSubcats)) subcats[k.replace(/\./g, "_")] = ibpSubcats[k].ibp;   // "1.1" vira "1_1"
    tx.set(refHist, { historico: admin.firestore.FieldValue.arrayUnion({ ibp: ibpGeral, data: dataStr, subcats }), ultimaResposta: agora.toISOString() }, { merge: true });
    tx.update(doc.ref, { usado: true, usadoEm: agora.toISOString() });
  });
  return { ok: true };
});

// 3) Sugestão anônima (precisa de um código existente).
exports.colabSugestao = onCall({ region: REGIAO, cors: true }, async (req) => {
  const codigo = validarFormatoCodigo(req.data && req.data.codigo);
  const texto = String((req.data && req.data.texto) || "").trim().slice(0, 500);
  const categoria = String((req.data && req.data.categoria) || "").slice(0, 60);
  if (!texto) throw new HttpsError("invalid-argument", "Escreva sua sugestão.");
  const doc = await acharToken(codigo);
  if (!doc) throw new HttpsError("not-found", "Código não encontrado.");
  await admin.firestore().collection("nr1map_sugestoes").add({ empresaId: String(doc.data().empresaId), categoria, texto, criadoEm: new Date().toISOString() });
  return { ok: true };
});

// 4) Canal de acolhimento anônimo (precisa de um código existente). Devolve o protocolo.
exports.colabChamado = onCall({ region: REGIAO, cors: true }, async (req) => {
  const codigo = validarFormatoCodigo(req.data && req.data.codigo);
  const tipo = String((req.data && req.data.tipo) || "");
  if (!["apoio", "assedio", "emergencia"].includes(tipo)) throw new HttpsError("invalid-argument", "Tipo inválido.");
  const texto = String((req.data && req.data.texto) || "").trim().slice(0, 1000) || "(sem descrição)";
  const doc = await acharToken(codigo);
  if (!doc) throw new HttpsError("not-found", "Código não encontrado.");
  const protocolo = "OUV-" + new Date().getFullYear() + "-" + String(Date.now()).slice(-6);
  await admin.firestore().collection("nr1map_chamados").add({ empresaId: String(doc.data().empresaId), tipo, identificacao: "Anônimo", texto, protocolo, criadoEm: new Date().toISOString() });
  return { ok: true, protocolo };
});
