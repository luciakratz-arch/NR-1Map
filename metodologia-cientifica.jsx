// NR-1 Map — Metodologia Científica
// Tela standalone para preview e integração ao painel.html

import { useState } from "react";

const VERDE = "#0A6E4F";
const VERDE_CLARO = "#12A073";
const VERDE_XP = "#E4F5EF";
const ROXO = "#7B00C4";
const ROXO_XP = "#F3E8FC";
const PRETO = "#0D1210";
const CINZA_ESC = "#2A2E2C";
const CINZA_MED = "#6B7370";
const CINZA_CLR = "#EEF1F0";
const LINHA = "#D8E2DF";
const LARANJA = "#D45E2A";
const LARANJA_XP = "#FAEEE7";

// —— Componentes utilitários ——

function SecTitle({ n, title, sub }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 3 }}>
        <span style={{ fontFamily: "'Syne',sans-serif", fontSize: 11, fontWeight: 800, color: VERDE_CLARO, letterSpacing: ".14em", textTransform: "uppercase" }}>
          {String(n).padStart(2, "0")}
        </span>
        <span style={{ fontFamily: "'Syne',sans-serif", fontSize: 20, fontWeight: 700, color: PRETO }}>
          {title}
        </span>
      </div>
      {sub && <div style={{ fontSize: 12, color: CINZA_MED, paddingLeft: 26 }}>{sub}</div>}
    </div>
  );
}

function Divider() {
  return <div style={{ height: 1, background: LINHA, margin: "28px 0" }} />;
}

function Tag({ children, bg = CINZA_CLR, color = CINZA_MED }) {
  return (
    <span style={{ background: bg, color, fontSize: 10, fontWeight: 600, padding: "3px 10px", borderRadius: 20, whiteSpace: "nowrap" }}>
      {children}
    </span>
  );
}

// —— SEÇÃO 1: Pirâmide Integrada ——

function PyramidBlock({ label, sub }) {
  return (
    <div style={{ background: "rgba(255,255,255,.15)", borderRadius: 8, padding: "9px 12px" }}>
      <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 10, opacity: .8 }}>{sub}</div>
    </div>
  );
}

function ZoneCard({ title, faixa, color, bgColor, body }) {
  return (
    <div style={{ borderLeft: `3px solid ${color}`, background: bgColor, borderRadius: "0 8px 8px 0", padding: "13px 15px" }}>
      <div style={{ fontSize: 12, fontWeight: 700, color, marginBottom: 5 }}>{title} <span style={{ fontWeight: 400, fontSize: 10 }}>{faixa}</span></div>
      <div style={{ fontSize: 12, color: PRETO, lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: body }} />
    </div>
  );
}

function SecPiramide() {
  return (
    <div>
      <SecTitle n={1} title="Fundação Teórica Integrada" sub="Maslow · Herzberg · Dejours — as três correntes que sustentam as 101 perguntas" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" }}>

        {/* PIRÂMIDE */}
        <div>
          {/* TOPO */}
          <div style={{ background: `linear-gradient(135deg,${ROXO},#9B30E0)`, borderRadius: "12px 12px 0 0", padding: "18px 20px", color: "#fff", marginBottom: 2 }}>
            <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: ".14em", textTransform: "uppercase", opacity: .75, marginBottom: 10 }}>
              FATORES MOTIVACIONAIS · Herzberg &amp; Dejours
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <PyramidBlock label="Propósito" sub="Significado do trabalho" />
              <PyramidBlock label="Identidade" sub="Autorrealização profissional" />
              <PyramidBlock label="Autonomia" sub="Espaço de criação (Dejours)" />
              <PyramidBlock label="Reconhecimento" sub="Julgamento de Utilidade e Beleza" />
            </div>
            <div style={{ marginTop: 8, background: "rgba(255,255,255,.12)", borderRadius: 8, padding: "8px 12px" }}>
              <div style={{ fontSize: 10, fontWeight: 600, marginBottom: 1 }}>Relacionamentos Sociais</div>
              <div style={{ fontSize: 10, opacity: .8 }}>Espaço de Fala · Cultura · Proteção contra Assédio</div>
            </div>
          </div>

          {/* SEPARADOR IBP */}
          <div style={{ background: CINZA_ESC, padding: "7px 20px", display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ height: 1, flex: 1, background: "linear-gradient(90deg,transparent,#ef4444)" }} />
            <span style={{ fontSize: 9, fontWeight: 800, color: "#fff", letterSpacing: ".1em", whiteSpace: "nowrap" }}>
              IBP · ÍNDICE DE BALANÇA PSICODINÂMICA · −5 ←→ +5
            </span>
            <div style={{ height: 1, flex: 1, background: "linear-gradient(90deg,#10b981,transparent)" }} />
          </div>

          {/* BASE */}
          <div style={{ background: `linear-gradient(135deg,${VERDE},${VERDE_CLARO})`, borderRadius: "0 0 12px 12px", padding: "18px 20px", color: "#fff", marginTop: 2 }}>
            <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: ".14em", textTransform: "uppercase", opacity: .75, marginBottom: 10 }}>
              FATORES HIGIÊNICOS · Maslow &amp; Herzberg
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <PyramidBlock label="Infraestrutura" sub="Ergonomia · Sistemas digitais" />
              <PyramidBlock label="Proteção Física" sub="EPI · NR-1 · Direito de Recusa" />
              <PyramidBlock label="Ritmo e Pausas" sub="Cadência · Limitações biológicas" />
              <PyramidBlock label="Estabilidade" sub="Clareza de papéis · Seg. laboral" />
            </div>
          </div>
        </div>

        {/* EXPLICAÇÕES */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <ZoneCard
            title="Terreno Fértil"
            faixa="(+1,5 a +5,0)"
            color={ROXO}
            bgColor={ROXO_XP}
            body="Aqui opera a transformação do sofrimento em <b>Prazer e Emancipação</b> através do Reconhecimento — Julgamento de Estética e Utilidade (Dejours) — e do Espaço de Fala. O colaborador encontra sentido no trabalho e mobiliza sua subjetividade de forma criativa."
          />
          <ZoneCard
            title="Defesa Oculta"
            faixa="(−1,4 a +1,4)"
            color={CINZA_ESC}
            bgColor={CINZA_CLR}
            body="Aparente normalidade mantida por mecanismos de defesa coletivos: <b>cinismo viril, ativismo e banalização do sofrimento</b>. Risco de Burnout mascarado. Zona de alerta estratégico — exige Pesquisa Pulso focalizada."
          />
          <ZoneCard
            title="Sofrimento Patogênico"
            faixa="(−5,0 a −1,5)"
            color={VERDE}
            bgColor={VERDE_XP}
            body="Se esta base falhar, o sofrimento se torna <b>patogênico e há risco imediato de adoecimento com nexo causal (NR-1)</b>. Ruptura do equilíbrio psíquico. Exige intervenção obrigatória conforme GRO e registro no Plano de Ação 5W2H."
          />

          {/* Fórmula */}
          <div style={{ background: PRETO, borderRadius: 8, padding: "13px 16px" }}>
            <div style={{ fontSize: 9, fontWeight: 800, color: VERDE_CLARO, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 6 }}>
              Fórmula de Transposição
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 3 }}>
              IBP = (Média<sub style={{ fontSize: 10 }}>Likert</sub> − 3) × 2,5
            </div>
            <div style={{ fontSize: 11, color: "#6B7370" }}>Escala Likert 1–5 → Balança Psicodinâmica −5 a +5</div>
          </div>
        </div>

      </div>
    </div>
  );
}

// —— SEÇÃO 2: Engenharia das 101 questões ——

function ModRow({ emoji, mod, n }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 10px", background: CINZA_CLR, borderRadius: 7 }}>
      <span style={{ fontSize: 12, fontWeight: 600 }}>{emoji} {mod}</span>
      <span style={{ fontSize: 11, fontWeight: 700, background: ROXO, color: "#fff", padding: "2px 9px", borderRadius: 10 }}>{n}</span>
    </div>
  );
}

function SecPerguntas() {
  return (
    <div>
      <SecTitle n={2} title="A Engenharia das 101 Questões" sub="Matriz mestre autoral e pericial · Dra. Lucia Kratz · CRP 09/20590" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 14 }}>

        {/* Matriz */}
        <div style={{ background: "#fff", border: `1px solid ${LINHA}`, borderRadius: 10, padding: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: PRETO, marginBottom: 12 }}>Arquitetura da Matriz Mestre</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
            <ModRow emoji="🧠" mod="Módulo 1 — Fisiológico" n="27 perguntas" />
            <ModRow emoji="🛡️" mod="Módulo 2 — Segurança" n="29 perguntas" />
            <ModRow emoji="🤝" mod="Módulo 3 — Relacionamentos" n="25 perguntas" />
            <ModRow emoji="🚀" mod="Módulo 4 — Motivacional" n="20 perguntas" />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 10px", background: PRETO, borderRadius: 7 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>TOTAL REGULATÓRIO</span>
              <span style={{ fontSize: 14, fontWeight: 800, color: VERDE_CLARO }}>101 perguntas</span>
            </div>
          </div>
        </div>

        {/* Trava ímpar */}
        <div style={{ background: "#fff", border: `1px solid ${LINHA}`, borderRadius: 10, padding: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: PRETO, marginBottom: 8 }}>⚙️ Trava Algorítmica — Regra da Validação Ímpar</div>
          <div style={{ fontSize: 12, color: CINZA_MED, lineHeight: 1.7, marginBottom: 10 }}>
            O sistema possui uma <b style={{ color: PRETO }}>trava de salvamento</b> que impede questionários com número <b style={{ color: LARANJA }}>par de perguntas por subcategoria ativa</b> (mínimo 3).
          </div>
          <div style={{ background: LARANJA_XP, borderRadius: 8, padding: "10px 13px", marginBottom: 10 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: LARANJA, marginBottom: 3 }}>Por que isso importa tecnicamente?</div>
            <div style={{ fontSize: 11, color: PRETO, lineHeight: 1.65 }}>
              Em escalas Likert com número <b>par</b> de itens, os respondentes tendem a se neutralizar no ponto médio (3), gerando diagnósticos "mornos" sem vetor estatístico claro. A trava ímpar <b>força a balança a apontar</b> inequivocamente para Sofrimento ou Prazer.
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 7, padding: "9px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#DC2626" }}>✗ PAR</div>
              <div style={{ fontSize: 10, color: "#DC2626" }}>2, 4, 6 perguntas</div>
              <div style={{ fontSize: 10, color: CINZA_MED, marginTop: 2 }}>Bloqueado — inválido</div>
            </div>
            <div style={{ background: "#F0FDF4", border: "1px solid #BBF7D0", borderRadius: 7, padding: "9px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#16A34A" }}>✓ ÍMPAR</div>
              <div style={{ fontSize: 10, color: "#16A34A" }}>3, 5, 7+ perguntas</div>
              <div style={{ fontSize: 10, color: CINZA_MED, marginTop: 2 }}>Aprovado — vetor claro</div>
            </div>
          </div>
        </div>
      </div>

      {/* Embaralhamento */}
      <div style={{ background: `linear-gradient(135deg,${PRETO},#1A0A2E)`, borderRadius: 10, padding: "17px 20px", display: "flex", gap: 18, alignItems: "center" }}>
        <span style={{ fontSize: 32, flexShrink: 0 }}>🎲</span>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#fff", marginBottom: 4 }}>Regime de Embaralhamento Total</div>
          <div style={{ fontSize: 12, color: "#8A9590", lineHeight: 1.65 }}>
            As 101 perguntas entram num <b style={{ color: VERDE_CLARO }}>pool único</b> e são sorteadas aleatoriamente — sem respeitar módulo ou subcategoria. Isso <b style={{ color: VERDE_CLARO }}>elimina o viés de resposta por contexto</b>: o colaborador não percebe que está sendo avaliado sobre liderança e não "prepara" as respostas. O diagnóstico capta o estado emocional real, não o performado.
          </div>
        </div>
      </div>
    </div>
  );
}

// —— SEÇÃO 3: Duas Velocidades ——

function StepDot({ n, done }) {
  const bg = done ? VERDE : ROXO;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
      <div style={{ width: 40, height: 40, borderRadius: "50%", background: bg, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, fontWeight: 800 }}>{n}</div>
      {!done && <div style={{ width: 2, background: LINHA, flex: 1, margin: "4px 0", minHeight: 18 }} />}
    </div>
  );
}

function VelocityCard({ border, bg, tag, title, desc, badge, badgeBg }) {
  return (
    <div style={{ border: `1.5px solid ${border}`, borderRadius: 8, padding: 14, background: bg }}>
      <div style={{ fontSize: 9, fontWeight: 800, color: border, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 5 }}>{tag}</div>
      <div style={{ fontSize: 13, fontWeight: 700, color: PRETO, marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 11, color: CINZA_MED, lineHeight: 1.65, marginBottom: 8 }}>{desc}</div>
      <span style={{ background: badgeBg, color: "#fff", borderRadius: 6, padding: "5px 10px", fontSize: 11, fontWeight: 600 }}>{badge}</span>
    </div>
  );
}

function SecDuasVelocidades() {
  return (
    <div>
      <SecTitle n={3} title="Agendamento e Coleta em Duas Velocidades" sub="O gestor opera a ferramenta em 3 passos, com dois motores de escuta independentes e simultâneos" />

      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>

        {/* Passo 1 */}
        <div style={{ display: "flex", gap: 16 }}>
          <StepDot n="1" />
          <div style={{ background: "#fff", border: `1px solid ${LINHA}`, borderRadius: 10, padding: "15px 17px", marginBottom: 10, flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: PRETO, marginBottom: 5 }}>Setup do Projeto</div>
            <div style={{ fontSize: 12, color: CINZA_MED, lineHeight: 1.7 }}>
              O gestor ativa ou desativa subcategorias inteiras por CBO ou setor, edita os textos das perguntas para moldar a pesquisa à cultura interna da empresa <b style={{ color: PRETO }}>(override por cliente — sem afetar o banco global)</b> e valida a trava ímpar antes de prosseguir. A IA sugere automaticamente as subcategorias com pior histórico de IBP como prioridade inicial.
            </div>
          </div>
        </div>

        {/* Passo 2 */}
        <div style={{ display: "flex", gap: 16 }}>
          <StepDot n="2" />
          <div style={{ flex: 1, marginBottom: 10 }}>
            <div style={{ background: "#fff", border: `1px solid ${LINHA}`, borderRadius: 10, padding: "15px 17px" }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: PRETO, marginBottom: 10 }}>Definição do Ciclo — Dois Motores Simultâneos</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <VelocityCard
                  border={ROXO} bg={ROXO_XP}
                  tag="⚡ Velocidade 1 — Motor Pesquisa Pulso"
                  title="Disparos Rotativos Configuráveis"
                  desc="Envios automáticos via WhatsApp com token efêmero. Frequência e quantidade de perguntas configuráveis pelo gestor. Sistema prioriza as subcategorias com piores IBPs."
                  badge="🕐 Token expira em 48h"
                  badgeBg={ROXO}
                />
                <VelocityCard
                  border={VERDE} bg={VERDE_XP}
                  tag="🏛 Velocidade 2 — Pesquisa Robusta"
                  title="Questionário Profundo para Auditoria"
                  desc="Ciclos consolidados bimestral, semestral ou anual. O sistema seleciona automaticamente o ciclo com base nos resultados acumulados do IBP."
                  badge="🕐 Janela de 7 dias úteis"
                  badgeBg={VERDE}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Passo 3 */}
        <div style={{ display: "flex", gap: 16 }}>
          <StepDot n="3" done />
          <div style={{ background: "#fff", border: `1px solid ${LINHA}`, borderRadius: 10, padding: "15px 17px", flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: PRETO, marginBottom: 6 }}>Coleta, Anonimização e Cálculo do IBP</div>
            <div style={{ fontSize: 12, color: CINZA_MED, lineHeight: 1.7, marginBottom: 12 }}>
              O colaborador responde de forma <b style={{ color: PRETO }}>100% anônima via Magic Link/OTP</b> enviado ao WhatsApp — sem cadastro, sem senhas. A trava de anonimato por CBO exige mínimo de 3 respondentes por agrupamento antes de exibir dados segmentados.
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
              {[
                { icon: "📱", label: "Magic Link OTP", sub: "Sem senhas · Sem cadastro" },
                { icon: "🧮", label: "Likert → IBP", sub: "(Média − 3) × 2,5" },
                { icon: "🛡️", label: "Cascata de Anonimato", sub: "CBO → Setor → Empresa" },
              ].map(({ icon, label, sub }) => (
                <div key={label} style={{ background: CINZA_CLR, borderRadius: 8, padding: 12, textAlign: "center" }}>
                  <div style={{ fontSize: 20, marginBottom: 4 }}>{icon}</div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: PRETO }}>{label}</div>
                  <div style={{ fontSize: 10, color: CINZA_MED, marginTop: 2 }}>{sub}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// —— SEÇÃO 4: Versões de Diagnóstico ——

function VersaoCard({ emoji, titulo, perguntas, blocos, tempo, ideal, cor, bg, alerta, itens }) {
  return (
    <div style={{ border: `1.5px solid ${cor}`, borderRadius: 10, padding: 16, background: bg }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 24 }}>{emoji}</span>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: PRETO }}>{titulo}</div>
          <div style={{ fontSize: 11, color: cor, fontWeight: 600 }}>{perguntas} perguntas · {blocos} blocos · ~{tempo}</div>
        </div>
      </div>
      <div style={{ fontSize: 11, color: CINZA_MED, lineHeight: 1.7, marginBottom: 10 }}>
        <b style={{ color: PRETO }}>Ideal para:</b> {ideal}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
        {itens.map(function(item, i) {
          return (
            <div key={i} style={{ display: "flex", gap: 7, fontSize: 11, color: CINZA_MED, lineHeight: 1.5 }}>
              <span style={{ color: cor, flexShrink: 0 }}>✓</span>
              <span>{item}</span>
            </div>
          );
        })}
      </div>
      {alerta && (
        <div style={{ background: "rgba(212,94,42,.08)", border: "1px solid rgba(212,94,42,.2)", borderRadius: 7, padding: "8px 10px", fontSize: 11, color: LARANJA, lineHeight: 1.6 }}>
          ⚠️ {alerta}
        </div>
      )}
    </div>
  );
}

function SecVersoesdiagnostico() {
  return (
    <div>
      <SecTitle n={4} title="Três Versões de Diagnóstico" sub="O RH escolhe a profundidade — o sistema garante a validade estatística em todas" />

      <div style={{ background: "#fff", border: `1px solid ${LINHA}`, borderRadius: 10, padding: "15px 17px", marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: CINZA_MED, lineHeight: 1.75 }}>
          A seleção de versão é feita na aba <b style={{ color: PRETO }}>"Módulos e Perguntas"</b> do painel RH.
          Ao escolher uma versão, os checkboxes de perguntas são pré-marcados automaticamente.
          O RH pode personalizar a seleção depois — adicionando perguntas próprias ou desmarcando individualmente
          (com alerta de impacto no histórico). <b style={{ color: PRETO }}>A trava ímpar é validada em todas as versões</b> antes do disparo.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 16 }}>
        <VersaoCard
          emoji="⚡"
          titulo="Versão Rápida"
          perguntas={21}
          blocos={3}
          tempo="10 min"
          cor={ROXO}
          bg={ROXO_XP}
          ideal="Pesquisa Pulso semanal, primeiro contato, empresas com baixa adesão histórica"
          itens={[
            "1 pergunta por subcategoria (a mais representativa de cada dimensão)",
            "3 blocos de 7 — curto o suficiente para responder no intervalo",
            "Mantém a trava ímpar: 1 pergunta/subcat = sempre ímpar",
            "Resultado gera IBP por módulo mas não por subcategoria individual",
          ]}
          alerta="Diagnóstico menos granular — não recomendado para laudo técnico GRO/PGR. Use para monitoramento de tendência."
        />
        <VersaoCard
          emoji="⭐"
          titulo="Versão Padrão"
          perguntas={54}
          blocos={8}
          tempo="25 min"
          cor={VERDE}
          bg={VERDE_XP}
          ideal="Diagnóstico regular, ciclo bimestral/semestral, GRO/PGR padrão NR-1"
          itens={[
            "3 perguntas por subcategoria — mínimo estatisticamente válido",
            "8 blocos de 7 — ritmo equilibrado, taxa de abandono baixa",
            "IBP calculado por subcategoria, módulo e geral",
            "Compatível com laudo técnico e Plano de Ação 5W2H",
          ]}
          alerta={null}
        />
        <VersaoCard
          emoji="📋"
          titulo="Versão Completa"
          perguntas={101}
          blocos={15}
          tempo="45 min"
          cor={CINZA_ESC}
          bg={CINZA_CLR}
          ideal="Diagnóstico aprofundado, laudo técnico completo, defesa em fiscalização MTE"
          itens={[
            "Todas as 101 perguntas do banco — máxima cobertura diagnóstica",
            "15 blocos de 7 — recomendado dividir em duas sessões",
            "IBP com máxima granularidade por subcategoria",
            "Gera Relatório de Evidências completo para processos trabalhistas",
          ]}
          alerta="Taxa de abandono mais alta. Recomendado para empresas com cultura de pesquisa estabelecida ou situação de risco elevado."
        />
      </div>

      {/* Comparativo */}
      <div style={{ background: PRETO, borderRadius: 10, padding: "15px 18px" }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "#fff", marginBottom: 12 }}>Comparativo de Validade e Uso</div>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 0 }}>
          {["Critério", "⚡ Rápida", "⭐ Padrão", "📋 Completa"].map(function(h, i) {
            return <div key={i} style={{ fontSize: 10, fontWeight: 700, color: VERDE_CLARO, padding: "4px 8px", borderBottom: "1px solid #1E2A28" }}>{h}</div>;
          })}
          {[
            ["IBP por subcategoria", "❌", "✅", "✅"],
            ["IBP por módulo", "✅", "✅", "✅"],
            ["Laudo técnico GRO", "❌", "✅", "✅"],
            ["Relatório de Evidências", "❌", "✅ parcial", "✅ completo"],
            ["Trava ímpar garantida", "✅", "✅", "✅"],
            ["Comparabilidade histórica", "⚠️ limitada", "✅", "✅"],
          ].map(function(row, ri) {
            return row.map(function(cell, ci) {
              return (
                <div key={ri+"-"+ci} style={{
                  fontSize: 11, color: ci === 0 ? "#C8D4D0" : "#8A9590",
                  padding: "6px 8px", borderBottom: "1px solid #1E2A28",
                  background: ri % 2 === 0 ? "rgba(255,255,255,.02)" : "transparent"
                }}>{cell}</div>
              );
            });
          })}
        </div>
      </div>
    </div>
  );
}

// —— ROOT ——

export default function MetodologiaCientifica() {
  return (
    <div style={{ fontFamily: "'Inter',sans-serif", background: CINZA_CLR, minHeight: "100vh", WebkitFontSmoothing: "antialiased" }}>
      {/* Topbar */}
      <div style={{ background: "#fff", borderBottom: `1px solid ${LINHA}`, padding: "0 28px", height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 10 }}>
        <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 14, fontWeight: 700, color: PRETO }}>
          🔬 Metodologia Científica
        </div>
        <div style={{ fontSize: 11, color: CINZA_MED, background: CINZA_CLR, padding: "4px 12px", borderRadius: 20 }}>
          Dra. Lucia Kratz · CRP 09/20590
        </div>
      </div>

      {/* Conteúdo */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "28px 28px 48px" }}>
        <SecPiramide />
        <Divider />
        <SecPerguntas />
        <Divider />
        <SecDuasVelocidades />
        <Divider />
        <SecVersoesdiagnostico />

        {/* Rodapé autoridade */}
        <div style={{ marginTop: 28, background: PRETO, borderRadius: 12, padding: "18px 22px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 14 }}>
          <div>
            <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 14, fontWeight: 700, color: "#fff", marginBottom: 2 }}>Dra. Lucia Kratz</div>
            <div style={{ fontSize: 11, color: "#8A9590" }}>Psicóloga · Administradora · Professora Universitária · CRP 09/20590</div>
            <div style={{ fontSize: 11, color: VERDE_CLARO, marginTop: 4 }}>Criadora do IBP (Índice de Balança Psicodinâmica) e do NR-1 Map</div>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <Tag bg="rgba(255,255,255,.08)" color="#C8D4D0">Psicodinâmica · Dejours</Tag>
            <Tag bg="rgba(255,255,255,.08)" color="#C8D4D0">Fatores Higiênicos · Herzberg</Tag>
            <Tag bg="rgba(255,255,255,.08)" color="#C8D4D0">Hierarquia · Maslow</Tag>
            <Tag bg="rgba(255,255,255,.08)" color="#C8D4D0">Portaria MTE 1.419/2024</Tag>
          </div>
        </div>
      </div>
    </div>
  );
}
