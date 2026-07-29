// ═══════════════════════════════════════
// NR-1 Map — app.js
// Scripts da landing page (index.html)
// ═══════════════════════════════════════

// ─── NAV MOBILE ─────────────────────────
function toggleNavMobile(){
  var m=document.getElementById('nav-mobile-menu');
  var b=document.getElementById('nav-hamburguer');
  if(!m||!b) return;
  var open=m.style.display==='flex';
  m.style.display=open?'none':'flex';
  m.style.pointerEvents=open?'none':'all';
  b.textContent=open?'☰':'✕';
}

// ─── FAQ ────────────────────────────────
function toggleFaq(btn) {
  var item = btn.parentElement;
  var isOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item.open').forEach(function(el) {
    el.classList.remove('open');
    el.querySelector('.faq-icon').textContent = '+';
  });
  if (!isOpen) {
    item.classList.add('open');
    btn.querySelector('.faq-icon').textContent = '−';
  }
}

// ─── LEADS ──────────────────────────────
var leadData = { porte: '', nivel: '', concern: '' };

function leadStep(n) {
  if (n === 2 && !document.getElementById('l-email').value) {
    alert('Por favor informe seu e-mail.');
    return;
  }
  for (var i = 1; i <= 4; i++) {
    var el = document.getElementById('lead-step-' + i);
    if (el) el.style.display = i === n ? 'block' : 'none';
  }
  document.getElementById('lead-prog').style.width = (n * 25) + '%';
}

function selPorte(el, val) {
  leadData.porte = val;
  document.querySelectorAll('#l-porte-opts > div').forEach(function(d) {
    d.style.borderColor = '#2A2E2C';
    d.querySelector('.l-radio').style.background = 'transparent';
    d.querySelector('span').style.color = '#8A9590';
  });
  el.style.borderColor = 'var(--verde-claro)';
  el.querySelector('.l-radio').style.background = 'var(--verde-claro)';
  el.querySelector('span').style.color = '#fff';
}

function selNivel(el, val) {
  leadData.nivel = val;
  document.querySelectorAll('#l-nivel-opts > div').forEach(function(d) {
    d.style.borderColor = '#2A2E2C';
    d.querySelector('div:last-child').style.color = '#8A9590';
  });
  el.style.borderColor = 'var(--verde-claro)';
  el.querySelector('div:last-child').style.color = '#fff';
}

function selConcern(el, val) {
  leadData.concern = val;
  document.querySelectorAll('#l-concern-opts > div').forEach(function(d) {
    d.style.borderColor = '#2A2E2C';
    d.querySelector('.l-radio-c').style.background = 'transparent';
    d.querySelector('span').style.color = '#8A9590';
  });
  el.style.borderColor = 'var(--verde-claro)';
  el.querySelector('.l-radio-c').style.background = 'var(--verde-claro)';
  el.querySelector('span').style.color = '#fff';
}

async function enviarLead() {
  var payload = {
    nome: document.getElementById('l-nome').value,
    cargo: document.getElementById('l-cargo').value,
    email: document.getElementById('l-email').value,
    whatsapp: document.getElementById('l-wpp').value,
    empresa: document.getElementById('l-empresa').value,
    segmento: document.getElementById('l-segmento').value,
    porte: leadData.porte,
    nivel_nr1: leadData.nivel,
    preocupacao: leadData.concern,
    data: new Date().toISOString()
  };
  try {
    await window.nr1mapDb.collection('nr1map_leads').add(payload);
  } catch(e) {
    console.log('Firestore lead error:', e);
  }
  leadStep(4);
}

// ─── DEPOIMENTOS ────────────────────────
var depIndex = 0;
function depNav(dir) {
  var cards = document.querySelectorAll('.dep-card');
  depIndex = Math.max(0, Math.min(depIndex + dir, cards.length - 3));
  cards.forEach(function(c, i) {
    c.style.opacity = (i >= depIndex && i < depIndex + 3) ? '1' : '0.4';
  });
}

function abrirFormDep() {
  document.getElementById('modal-dep').style.display = 'flex';
}
function fecharFormDep() {
  document.getElementById('modal-dep').style.display = 'none';
}

var depStars = 5;
function setStar(n) {
  depStars = n;
  document.querySelectorAll('#dep-stars span').forEach(function(s, i) {
    s.style.color = (5 - i) <= n ? 'var(--roxo)' : 'var(--linha)';
  });
}

async function enviarDep() {
  var payload = {
    nome: document.getElementById('dep-nome').value,
    cargo: document.getElementById('dep-cargo').value,
    texto: document.getElementById('dep-texto').value,
    estrelas: depStars,
    status: 'pendente',
    data: new Date().toISOString()
  };
  if (!payload.nome || !payload.texto) {
    alert('Por favor preencha ao menos o nome e o depoimento.');
    return;
  }
  try {
    await window.nr1mapDb.collection('nr1map_depoimentos').add(payload);
  } catch(e) {
    console.log('Firestore dep error:', e);
  }
  fecharFormDep();
  alert('✅ Depoimento enviado! Será publicado após aprovação.');
}

// ─── CALCULADORA / PREÇOS ────────────────
var opcaoAtiva = 'mensal';

var dados = {
  mensal: {
    titulo: 'Assinatura Mensal — Gestão Contínua',
    sub: 'Diagnóstico Inicial + Painel IA + Pesquisas Pulso semanais anônimas via WhatsApp',
    labelValor: 'Valor mensal',
    sufixo: '/mês',
    cor: 'var(--verde-claro)',
    btn: 'Assinar agora com este valor →',
    itens: '✓ Diagnóstico Inicial completo|✓ Painel dinâmico Prazer/Sofrimento|✓ Pesquisa Pulso semanal anônima|✓ Atualizações de IA contínuas',
    faixas: [
      { label: 'Até 5',       unit: 35,   ex: '5 × R$35 = R$175' },
      { label: '6 a 20',      unit: 25,   ex: '10 × R$25 = R$250' },
      { label: '21 a 50',     unit: 20,   ex: '30 × R$20 = R$600' },
      { label: '51 a 100',    unit: 16.5, ex: '60 × R$16,50 = R$990' },
      { label: '101 a 200',   unit: 13,   ex: '150 × R$13 = R$1.950' },
      { label: '201 a 500 ⭐', unit: 10,  ex: '300 × R$10 = R$3.000' }
    ]
  },
  unico: {
    titulo: 'Uso Único — Diagnóstico Pontual',
    sub: 'Laudo Técnico + Mapa de Risco + Plano 5W2H · Validade 30 dias · Pagamento único',
    labelValor: 'Valor total',
    sufixo: '',
    cor: 'var(--roxo-claro)',
    btn: 'Contratar diagnóstico pontual →',
    itens: '✓ Laudo Técnico Psicossocial|✓ Mapa de Risco por CBO|✓ Plano de Ação 5W2H|✓ Sem assinatura ou fidelidade',
    faixas: [
      { label: 'Até 5',     unit: 97, ex: '5 × R$97 = R$485' },
      { label: '6 a 20',    unit: 79, ex: '10 × R$79 = R$790' },
      { label: '21 a 50',   unit: 59, ex: '30 × R$59 = R$1.770' },
      { label: '51 a 100',  unit: 49, ex: '60 × R$49 = R$2.940' },
      { label: '101 a 200', unit: 39, ex: '150 × R$39 = R$5.850' },
      { label: '201 a 500', unit: 29, ex: '300 × R$29 = R$8.700' }
    ]
  }
};

function selectOpcao(op) {
  opcaoAtiva = op;
  var d = dados[op];

  var cardM  = document.getElementById('card-mensal');
  var cardU  = document.getElementById('card-unico');
  var radioM = document.getElementById('radio-mensal');
  var radioU = document.getElementById('radio-unico');

  if (op === 'mensal') {
    cardM.style.border      = '2.5px solid var(--verde)';
    cardM.style.background  = 'var(--verde-xp)';
    radioM.style.background = 'var(--verde)';
    radioM.style.borderColor= 'var(--verde)';
    radioM.innerHTML        = '<div style="width:8px;height:8px;border-radius:50%;background:#fff;"></div>';
    cardU.style.border      = '2px solid var(--linha)';
    cardU.style.background  = 'var(--branco)';
    radioU.style.background = 'var(--branco)';
    radioU.style.borderColor= 'var(--linha)';
    radioU.innerHTML        = '';
  } else {
    cardU.style.border      = '2.5px solid var(--roxo)';
    cardU.style.background  = 'var(--roxo-xp)';
    radioU.style.background = 'var(--roxo)';
    radioU.style.borderColor= 'var(--roxo)';
    radioU.innerHTML        = '<div style="width:8px;height:8px;border-radius:50%;background:#fff;"></div>';
    cardM.style.border      = '2px solid var(--linha)';
    cardM.style.background  = 'var(--branco)';
    radioM.style.background = 'var(--branco)';
    radioM.style.borderColor= 'var(--linha)';
    radioM.innerHTML        = '';
  }

  document.getElementById('slider-n').style.accentColor = op === 'mensal' ? '#12A073' : '#9B30E0';
  document.getElementById('calc-titulo').textContent     = d.titulo;
  document.getElementById('calc-sub').textContent        = d.sub;
  document.getElementById('calc-label-valor').textContent= d.labelValor;
  document.getElementById('calc-itens').innerHTML        = d.itens.split('|').join('<br/>');
  document.getElementById('calc-btn').textContent        = d.btn;
  document.getElementById('calc-faixa').style.color      = d.cor;

  calcValor(document.getElementById('input-n').value);
}

function calcValor(n) {
  n = Math.min(500, Math.max(1, parseInt(n) || 1));
  document.getElementById('slider-n').value = n;
  document.getElementById('input-n').value  = n;

  var d      = dados[opcaoAtiva];
  var faixas = d.faixas;
  var fi     = n <= 5 ? 0 : n <= 20 ? 1 : n <= 50 ? 2 : n <= 100 ? 3 : n <= 200 ? 4 : 5;
  var unit   = faixas[fi].unit;
  var total  = n * unit;

  // PISO ANTIDECRÉSCIMO
  if (fi === 1) { var piso = 5   * faixas[0].unit; if (total < piso) total = piso; }
  if (fi === 2) { var piso = 20  * faixas[1].unit; if (total < piso) total = piso; }
  if (fi === 3) { var piso = 50  * faixas[2].unit; if (total < piso) total = piso; }
  if (fi === 4) { var piso = 100 * faixas[3].unit; if (total < piso) total = piso; }
  if (fi === 5) { var piso = 200 * faixas[4].unit; if (total < piso) total = piso; }

  document.getElementById('calc-faixa').textContent  = 'Faixa ' + (fi+1) + ' — ' + faixas[fi].label + ' colaboradores';
  document.getElementById('calc-total').textContent  = 'R$ ' + total.toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2});
  document.getElementById('calc-detalhe').textContent= n + ' × R$ ' + unit.toFixed(2).replace('.', ',') + (d.sufixo ? ' / colaborador/mês' : ' / colaborador · pagamento único');

  var cor = opcaoAtiva === 'mensal' ? '#12A073' : '#9B30E0';
  faixas.forEach(function(f, i) {
    var row   = document.getElementById('tf-row-' + (i+1));
    var ativo = i === fi;
    row.style.background = ativo ? (opcaoAtiva === 'mensal' ? 'rgba(18,160,115,0.12)' : 'rgba(123,0,196,0.12)') : 'transparent';
    row.innerHTML =
      '<span style="font-weight:' + (ativo?'700':'400') + ';color:' + (ativo?'#fff':'#8A9590') + ';">' + f.label + '</span>' +
      '<span style="text-align:center;color:' + (ativo?cor:'#4A5450') + ';font-weight:' + (ativo?'700':'400') + ';">R$ ' + f.unit.toFixed(2).replace('.', ',') + '</span>' +
      '<span style="text-align:right;color:#4A5450;font-size:11px;">' + f.ex + '</span>';
  });
}

// ─── CHECKOUT ───────────────────────────
var NR1MAP_CHECKOUT_URL = "https://script.google.com/macros/s/AKfycbwDh6ZydEUKFWzYUqYPe9VbulmN7MRbRbs9PoLK7DAbo4VkTqFdacfPLRodtQ2x_0_qXA/exec";

async function irParaCheckout(qtd, tipo, nome, email, empresa) {
  qtd  = qtd  || 1;
  tipo = tipo || 'mensal';
  var btn = document.getElementById('btn-checkout-' + tipo);
  if (btn) { btn.textContent = 'Aguarde...'; btn.disabled = true; }
  try {
    var url  = NR1MAP_CHECKOUT_URL + '?qtd=' + qtd + '&tipo=' + tipo + '&nome=' + encodeURIComponent(nome||'') + '&email=' + encodeURIComponent(email||'') + '&empresa=' + encodeURIComponent(empresa||'');
    var resp = await fetch(url);
    var data = await resp.json();
    if (data.url) {
      window.location.href = data.url;
    } else {
      alert('Erro ao processar pagamento. Tente novamente.');
      if (btn) { btn.textContent = 'Assinar agora com este valor →'; btn.disabled = false; }
    }
  } catch(e) {
    alert('Erro de conexão. Tente novamente.');
    if (btn) { btn.textContent = 'Assinar agora com este valor →'; btn.disabled = false; }
  }
}

function assinarAgora() {
  var qtd  = parseInt(document.getElementById('input-n') ? document.getElementById('input-n').value : 10);
  var tipo = window.opcaoAtiva || 'mensal';
  irParaCheckout(qtd, tipo);
}

// ─── INIT ───────────────────────────────
// Executado após todas as seções externas estarem no DOM
selectOpcao('mensal');

// ─── SERVICE WORKER ──────────────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/NR-1Map/sw.js')
      .then(function(reg) { console.log('[NR-1 Map] SW registrado:', reg.scope); })
      .catch(function(err) { console.log('[NR-1 Map] SW falhou:', err); });
  });
}
