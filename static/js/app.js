/**
 * NutriBot — Frontend Application Logic
 * IBM Granite · Nutrition Agentic AI · Agentic Conversation Controller
 */

'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
const App = {
  sessionId:   null,
  isTyping:    false,
  planText:    '',
  stepMap: {
    collect_name:     'name',
    collect_age:      'age',
    collect_diet:     'diet',
    collect_medical:  'medical',
    collect_location: 'location',
    generate_plan:    'plan',
    chat:             'plan',
  },
};

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const chatWindow    = document.getElementById('chatWindow');
const userInput     = document.getElementById('userInput');
const sendBtn       = document.getElementById('sendBtn');
const sendIcon      = document.getElementById('sendIcon');
const sendSpinner   = document.getElementById('sendSpinner');
const resetBtn      = document.getElementById('resetBtn');
const statusDot     = document.getElementById('statusDot');
const profilePanel  = document.getElementById('profileContent');
const quickSugg     = document.getElementById('quickSuggestions');
const planModal     = document.getElementById('planModal');
const modalBody     = document.getElementById('modalBody');
const sessionInfo   = document.getElementById('sessionInfo');

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', startSession);

async function startSession() {
  clearChat();
  showLoading(true);
  try {
    const res  = await api('/api/session', 'POST', {});
    App.sessionId = res.session_id;
    sessionInfo.textContent = `Session: ${App.sessionId.slice(0, 8)}…`;
    showLoading(false);
    appendBotMessage(res.message);
    advanceStepper(res.state);
    sendBtn.disabled = false;
  } catch (err) {
    showLoading(false);
    statusDot.classList.add('offline');
    appendBotMessage(`⚠️ **Connection error.** Could not reach NutriBot.\n\n_${err.message}_\n\nPlease refresh the page or check that the server is running.`);
  }
}

// ─── Send message ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || App.isTyping) return;

  appendUserMessage(text);
  userInput.value = '';
  autoResizeInput();
  setLoading(true);

  try {
    const res = await api('/api/chat', 'POST', {
      session_id: App.sessionId,
      message:    text,
    });
    handleResponse(res);
  } catch (err) {
    appendBotMessage(`⚠️ Something went wrong: _${err.message}_. Please try again.`);
  } finally {
    setLoading(false);
  }
}

function handleResponse(res) {
  if (res.error) {
    appendBotMessage(`⚠️ ${res.error}`);
    return;
  }

  // If location was just collected → trigger plan generation automatically
  if (res.trigger_plan) {
    appendBotMessage(res.message);
    advanceStepper(res.state);
    updateProfileCard(res.user_profile);
    setTimeout(() => generatePlan(), 400);
    return;
  }

  appendBotMessage(res.message, res.plan_ready);
  advanceStepper(res.state);
  updateProfileCard(res.user_profile);

  if (res.state === 'chat') {
    quickSugg.style.display = 'flex';
  }
}

async function generatePlan() {
  setLoading(true);
  showTypingIndicator();
  try {
    const res = await api('/api/generate_plan', 'POST', { session_id: App.sessionId });
    removeTypingIndicator();
    handleResponse(res);
  } catch (err) {
    removeTypingIndicator();
    appendBotMessage(`⚠️ Plan generation failed: _${err.message}_`);
  } finally {
    setLoading(false);
  }
}

// ─── API helper ───────────────────────────────────────────────────────────────
async function api(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ─── Chat rendering ───────────────────────────────────────────────────────────
function appendBotMessage(markdown, showPlanBtn = false) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper bot';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '🌿';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = renderMarkdown(markdown);

  if (showPlanBtn) {
    App.planText = markdown;
    const badge = document.createElement('div');
    badge.className = 'plan-badge';
    badge.textContent = '📄 View Full Plan';
    badge.addEventListener('click', openPlanModal);
    bubble.appendChild(badge);
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

function appendUserMessage(text) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper user';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '👤';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  wrapper.appendChild(avatar);
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

function showTypingIndicator() {
  removeTypingIndicator();
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper bot';
  wrapper.id = 'typingWrapper';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '🌿';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = document.getElementById('typingWrapper');
  if (el) el.remove();
}

function clearChat() {
  chatWindow.innerHTML = '';
}

function showLoading(show) {
  if (show) {
    chatWindow.innerHTML = `
      <div class="chat-loading" id="chatLoading">
        <div class="spinner"></div>
        <p>Connecting to NutriBot…</p>
      </div>`;
  }
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ─── Stepper ──────────────────────────────────────────────────────────────────
function advanceStepper(state) {
  const stepKey = App.stepMap[state];
  if (!stepKey) return;
  const steps = document.querySelectorAll('.step');
  const stepNames = ['name', 'age', 'diet', 'medical', 'location', 'plan'];
  const currentIdx = stepNames.indexOf(stepKey);

  steps.forEach((el, idx) => {
    el.classList.remove('active', 'done');
    if (idx < currentIdx)  el.classList.add('done');
    if (idx === currentIdx) el.classList.add('active');
  });
}

// ─── Profile card ─────────────────────────────────────────────────────────────
function updateProfileCard(profile) {
  if (!profile || Object.keys(profile).length === 0) return;

  const fields = [
    { label: '👤 Name',     key: 'name'    },
    { label: '🎂 Age',      key: 'age'     },
    { label: '🥗 Diet',     key: 'diet',   transform: v => capitalize(v) },
    { label: '🩺 Medical',  key: 'medical', transform: v => v || 'None' },
    { label: '📍 City',     key: 'city'    },
    { label: '🌍 Country',  key: 'country' },
  ];

  profilePanel.innerHTML = fields
    .filter(f => profile[f.key] !== undefined)
    .map(f => {
      const val = f.transform ? f.transform(profile[f.key]) : profile[f.key];
      return `<div class="profile-row">
        <span class="profile-label">${f.label}</span>
        <span class="profile-value">${escHtml(String(val))}</span>
      </div>`;
    }).join('');
}

// ─── Plan modal ───────────────────────────────────────────────────────────────
function openPlanModal() {
  modalBody.innerHTML = renderMarkdown(App.planText);
  planModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closePlanModal() {
  planModal.style.display = 'none';
  document.body.style.overflow = '';
}

document.getElementById('modalClose').addEventListener('click',  closePlanModal);
document.getElementById('modalClose2').addEventListener('click', closePlanModal);
planModal.addEventListener('click', e => { if (e.target === planModal) closePlanModal(); });

document.getElementById('printBtn').addEventListener('click', () => {
  window.print();
});

document.getElementById('copyBtn').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(App.planText);
    const btn = document.getElementById('copyBtn');
    btn.textContent = '✅ Copied!';
    setTimeout(() => { btn.textContent = '📋 Copy to Clipboard'; }, 2000);
  } catch {
    alert('Could not access clipboard. Please copy manually.');
  }
});

// ─── Quick suggestions ────────────────────────────────────────────────────────
document.querySelectorAll('.qs-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    userInput.value = btn.dataset.msg;
    autoResizeInput();
    sendMessage();
  });
});

// ─── Reset ────────────────────────────────────────────────────────────────────
resetBtn.addEventListener('click', async () => {
  if (!confirm('Start a new session? Your current plan will be lost.')) return;
  quickSugg.style.display = 'none';
  profilePanel.innerHTML = '<p class="profile-placeholder">Your nutrition profile will appear here as you chat with NutriBot.</p>';
  App.planText = '';
  clearAllSteps();
  try {
    const res = await api('/api/reset', 'POST', { session_id: App.sessionId });
    App.sessionId = res.session_id;
    sessionInfo.textContent = `Session: ${App.sessionId.slice(0, 8)}…`;
    clearChat();
    appendBotMessage(res.message);
    advanceStepper(res.state);
    sendBtn.disabled = false;
  } catch (err) {
    appendBotMessage(`⚠️ Reset failed: ${err.message}`);
  }
});

function clearAllSteps() {
  document.querySelectorAll('.step').forEach(el => el.classList.remove('active', 'done'));
  const first = document.querySelector('.step');
  if (first) first.classList.add('active');
}

// ─── Input handlers ───────────────────────────────────────────────────────────
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

userInput.addEventListener('input', autoResizeInput);

function autoResizeInput() {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

function setLoading(loading) {
  App.isTyping = loading;
  sendBtn.disabled = loading;
  if (loading) {
    sendIcon.style.display = 'none';
    sendSpinner.style.display = '';
    showTypingIndicator();
  } else {
    sendIcon.style.display = '';
    sendSpinner.style.display = 'none';
    removeTypingIndicator();
  }
}

// ─── Markdown renderer (lightweight, no external deps) ────────────────────────
function renderMarkdown(md) {
  if (!md) return '';
  let html = escHtml(md);

  // Headings
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm,  '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,   '<h3>$1</h3>');
  html = html.replace(/^# (.+)$/gm,    '<h3>$1</h3>');

  // Bold, italic, inline code
  html = html.replace(/\*\*(.+?)\*\*/g,  '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g,      '<em>$1</em>');
  html = html.replace(/_(.+?)_/g,        '<em>$1</em>');
  html = html.replace(/`(.+?)`/g,        '<code>$1</code>');

  // Horizontal rule
  html = html.replace(/^---+$/gm, '<hr/>');

  // Tables (simple: | col | col |)
  html = renderTables(html);

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // Unordered lists
  html = html.replace(/(^[*\-] .+(\n[*\-] .+)*)/gm, match => {
    const items = match.split('\n')
      .filter(l => l.trim())
      .map(l => `<li>${l.replace(/^[*\-] /, '')}</li>`)
      .join('');
    return `<ul>${items}</ul>`;
  });

  // Ordered lists
  html = html.replace(/(^\d+\. .+(\n\d+\. .+)*)/gm, match => {
    const items = match.split('\n')
      .filter(l => l.trim())
      .map(l => `<li>${l.replace(/^\d+\. /, '')}</li>`)
      .join('');
    return `<ol>${items}</ol>`;
  });

  // Paragraphs (double newline → <p>)
  html = html
    .split(/\n{2,}/)
    .map(block => {
      block = block.trim();
      if (!block) return '';
      if (/^<(h[1-6]|ul|ol|li|table|blockquote|hr)/.test(block)) return block;
      return `<p>${block.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('\n');

  return html;
}

function renderTables(html) {
  // Match markdown table blocks
  return html.replace(/((\|.+\|\n?)+)/g, tableBlock => {
    const lines = tableBlock.trim().split('\n').filter(l => l.includes('|'));
    if (lines.length < 2) return tableBlock;
    const header = lines[0];
    const body   = lines.slice(2); // skip separator line

    const toTd = (line, tag) =>
      line.split('|')
          .filter((_, i, a) => i > 0 && i < a.length)
          .map(cell => `<${tag}>${cell.trim()}</${tag}>`)
          .join('');

    const thead = `<thead><tr>${toTd(header, 'th')}</tr></thead>`;
    const tbody = body.length
      ? `<tbody>${body.map(l => `<tr>${toTd(l, 'td')}</tr>`).join('')}</tbody>`
      : '';

    return `<table>${thead}${tbody}</table>`;
  });
}

function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}
