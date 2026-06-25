const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();
const db = admin.firestore();

/**
 * NR-1 Map — Cloud Function
 * Recebe dados do formulário de leads da landing page
 * Salva na coleção nr1map_leads (para o painel admin)
 * Salva na coleção nr1map_emails (para o Trigger Email disparar o e-book)
 */
exports.receberLead = functions.https.onRequest(async (req, res) => {
  // Permitir CORS para a landing page
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(204).send("");
    return;
  }

  if (req.method !== "POST") {
    res.status(405).send("Method Not Allowed");
    return;
  }

  try {
    const {
      nome,
      cargo,
      email,
      whatsapp,
      empresa,
      segmento,
      porte,
      nivel_nr1,
      preocupacao,
    } = req.body;

    if (!email) {
      res.status(400).json({ error: "E-mail é obrigatório." });
      return;
    }

    const timestamp = admin.firestore.FieldValue.serverTimestamp();

    // 1. Salvar lead no painel admin
    await db.collection("nr1map_leads").add({
      nome: nome || "",
      cargo: cargo || "",
      email,
      whatsapp: whatsapp || "",
      empresa: empresa || "",
      segmento: segmento || "",
      porte: porte || "",
      nivel_nr1: nivel_nr1 || "",
      preocupacao: preocupacao || "",
      status: "novo",
      criado_em: timestamp,
    });

    // 2. Salvar na coleção de e-mails para o Trigger Email disparar
    await db.collection("nr1map_emails").add({
      to: email,
      message: {
        subject: "📥 Seu e-book NR-1 Descomplicada chegou!",
        html: `
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#F0F0F0;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F0F0F0;padding:32px 0;">
  <tr><td align="center">
  <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
    <tr><td style="background:#0D1210;border-radius:12px 12px 0 0;padding:28px 40px;text-align:center;">
      <div style="font-weight:900;font-size:22px;">
        <span style="color:#ffffff;">NR-1</span><span style="color:#12A073;">Map</span>
      </div>
      <div style="font-size:11px;color:#4A5450;text-transform:uppercase;letter-spacing:0.12em;margin-top:4px;">Gestão de Riscos Psicossociais</div>
    </td></tr>
    <tr><td style="background:#0A6E4F;padding:40px;text-align:center;">
      <div style="font-size:36px;margin-bottom:12px;">📥</div>
      <h1 style="color:#ffffff;font-size:26px;font-weight:800;margin:0 0 10px;">Seu e-book chegou!</h1>
      <p style="color:rgba(255,255,255,0.8);font-size:15px;margin:0;line-height:1.6;">
        <strong style="color:#ffffff;">NR-1 Descomplicada</strong> — o que a lei exige, como cumprir e como proteger sua empresa.
      </p>
    </td></tr>
    <tr><td style="background:#ffffff;padding:36px 40px;">
      <p style="color:#2A2E2C;font-size:15px;line-height:1.7;margin:0 0 16px;">
        Olá${nome ? ", " + nome : ""}! 👋
      </p>
      <p style="color:#2A2E2C;font-size:15px;line-height:1.7;margin:0 0 20px;">
        Obrigada pelo seu interesse no <strong>NR-1 Map</strong>. Segue em anexo o e-book <strong>"NR-1 Descomplicada"</strong>.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#E4F5EF;border-radius:10px;margin-bottom:24px;">
        <tr><td style="padding:18px 22px;">
          <div style="font-weight:700;font-size:14px;color:#0D1210;margin-bottom:3px;">📄 NR-1 Descomplicada</div>
          <div style="font-size:12px;color:#0A6E4F;">PDF · Gratuito · 18 páginas · Em anexo</div>
        </td></tr>
      </table>
      <p style="color:#2A2E2C;font-size:14px;font-weight:600;margin:0 0 8px;">O e-book cobre:</p>
      <p style="color:#2A2E2C;font-size:13px;line-height:1.9;margin:0 0 24px;">
        ✅ O que é o GRO e por que sua empresa precisa dele<br/>
        ✅ Riscos psicossociais como perigos ocupacionais (NR-1 2024)<br/>
        ✅ Dejours, Herzberg e Maslow com respaldo normativo<br/>
        ✅ Checklist do que precisa estar documentado<br/>
        ✅ Penalidades e riscos jurídicos por descumprimento
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#FAEEE7;border-left:4px solid #D45E2A;border-radius:0 8px 8px 0;margin-bottom:28px;">
        <tr><td style="padding:14px 18px;">
          <p style="margin:0;font-size:13px;color:#2A2E2C;line-height:1.6;">
            ⚠️ <strong>A fiscalização do MTE já está ativa.</strong> Empresas sem Mapa de Risco Psicossocial documentado estão sujeitas a auto de infração imediato.
          </p>
        </td></tr>
      </table>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
        <tr><td align="center">
          <a href="https://luciakratz-arch.github.io/NR-1Map" style="display:inline-block;background:#0A6E4F;color:#ffffff;text-decoration:none;font-size:15px;font-weight:700;padding:14px 36px;border-radius:8px;">
            Conhecer o NR-1 Map →
          </a>
          <p style="margin:10px 0 0;font-size:12px;color:#6B7370;">A partir de R$ 35,00/colaborador/mês</p>
        </td></tr>
      </table>
      <hr style="border:none;border-top:1px solid #EEF1F0;margin:24px 0;"/>
      <p style="margin:0;font-size:13px;color:#2A2E2C;line-height:1.6;">
        <strong>Dra. Lucia Kratz</strong><br/>
        <span style="color:#7B00C4;">Psicóloga · CRP 09/20590</span><br/>
        Criadora do NR-1 Map
      </p>
    </td></tr>
    <tr><td style="background:#0D1210;border-radius:0 0 12px 12px;padding:20px 40px;text-align:center;">
      <p style="margin:0;font-size:11px;color:#4A5450;">© 2025 NR-1 Map · Gestão de Riscos Psicossociais</p>
    </td></tr>
  </table>
  </td></tr>
</table>
</body>
</html>`,
        attachments: [
          {
            filename: "NR-1-Descomplicada.pdf",
            path: "https://luciakratz-arch.github.io/NR-1Map/nr1-descomplicada-ebook.pdf",
          },
        ],
      },
      criado_em: timestamp,
    });

    res.status(200).json({
      success: true,
      message: "Lead salvo e e-book disparado com sucesso!",
    });
  } catch (error) {
    console.error("Erro ao processar lead:", error);
    res.status(500).json({ error: "Erro interno. Tente novamente." });
  }
});

/**
 * NR-1 Map — Receber depoimento
 * Salva depoimento pendente de aprovação
 */
exports.receberDepoimento = functions.https.onRequest(async (req, res) => {
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(204).send("");
    return;
  }

  try {
    const { nome, cargo, texto, estrelas } = req.body;

    await db.collection("nr1map_depoimentos").add({
      nome: nome || "Anônimo",
      cargo: cargo || "",
      texto,
      estrelas: estrelas || 5,
      status: "pendente",
      criado_em: admin.firestore.FieldValue.serverTimestamp(),
    });

    res.status(200).json({ success: true });
  } catch (error) {
    res.status(500).json({ error: "Erro ao salvar depoimento." });
  }
});
