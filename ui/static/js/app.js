// ── WebSocket ──────────────────────────────────────────────────────────────
let ws;
function connectWS() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "ticker")           handleTicker(msg);
    if (msg.type === "strategy_signal")  handleSignal(msg);
    if (msg.type === "alert")            showToast(msg.message, "warning");
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
}

// ── Tabs ──────────────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach(t => {
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(x => x.classList.remove("active"));
    t.classList.add("active");
    document.getElementById(`panel-${t.dataset.tab}`).classList.add("active");
    if (t.dataset.tab === "portfolio") loadPortfolio();
    if (t.dataset.tab === "history")   loadHistory();
    if (t.dataset.tab === "alerts")    loadAlerts();
    if (t.dataset.tab === "strategy")  loadStrategies();
  });
});

// ── Toast ─────────────────────────────────────────────────────────────────
function showToast(msg, type = "info") {
  const c = document.getElementById("toast-container");
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 5000);
}

// ── Ticker updates ────────────────────────────────────────────────────────
const tickerEls = {};
function handleTicker(msg) {
  const sym = msg.symbol;
  const data = msg.data;
  const price = parseFloat(data.close || data.mark_price || 0);
  if (!price) return;
  if (!tickerEls[sym]) {
    const el = document.getElementById(`price-${sym}`);
    if (el) tickerEls[sym] = el;
  }
  if (tickerEls[sym]) tickerEls[sym].textContent = price.toFixed(2);
}

function handleSignal(msg) {
  const s = msg.signals;
  if (s.entry_long)  showToast(`📈 ${msg.strategy_name}: LONG signal on ${msg.symbol}`, "success");
  if (s.entry_short) showToast(`📉 ${msg.strategy_name}: SHORT signal on ${msg.symbol}`, "error");
}

// ── API helpers ───────────────────────────────────────────────────────────
async function api(path, options = {}) {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  return r.json();
}

// ── Portfolio ─────────────────────────────────────────────────────────────
async function loadPortfolio() {
  const s = await api("/api/portfolio/summary");
  document.getElementById("bal-total").textContent   = "$" + s.total_value.toFixed(2);
  document.getElementById("bal-avail").textContent   = "$" + s.available_balance.toFixed(2);
  document.getElementById("bal-rpnl").textContent    = "$" + s.realized_pnl.toFixed(2);
  document.getElementById("bal-urpnl").textContent   = "$" + s.unrealized_pnl.toFixed(4);
  const tbody = document.getElementById("positions-body");
  tbody.innerHTML = s.positions.map(p => `
    <tr>
      <td>${p.symbol}</td>
      <td class="${p.side==='buy'?'green':'red'}">${p.side.toUpperCase()}</td>
      <td>${p.qty}</td>
      <td>${p.entry_price}</td>
      <td>${p.current_price}</td>
      <td class="${p.unrealized_pnl>=0?'green':'red'}">${p.unrealized_pnl>=0?'+':''}${p.unrealized_pnl}</td>
      <td><button class="btn btn-danger btn-sm" onclick="closePos(${p.trade_id},${p.current_price})">Close</button></td>
    </tr>`).join("");
}

async function closePos(id, price) {
  await api(`/api/trading/order/${id}?exit_price=${price}`, { method: "DELETE" });
  showToast("Position closed", "success");
  loadPortfolio();
}

// ── Trade History ─────────────────────────────────────────────────────────
async function loadHistory() {
  const trades = await api("/api/trading/history");
  const tbody = document.getElementById("history-body");
  tbody.innerHTML = trades.map(t => `
    <tr>
      <td>${t.symbol}</td>
      <td class="${t.side==='buy'?'green':'red'}">${t.side.toUpperCase()}</td>
      <td>${t.qty}</td>
      <td>${t.entry_price}</td>
      <td>${t.exit_price || '-'}</td>
      <td class="${(t.pnl||0)>=0?'green':'red'}">${t.pnl ? (t.pnl>=0?'+':'')+t.pnl : '-'}</td>
      <td><span class="badge ${t.status==='open'?'badge-active':'badge-inactive'}">${t.status}</span></td>
      <td>${t.mode}</td>
      <td>${t.entry_time?.slice(0,16)}</td>
    </tr>`).join("");
}

// ── Alerts ────────────────────────────────────────────────────────────────
async function loadAlerts() {
  const alerts = await api("/api/alerts/");
  const tbody = document.getElementById("alerts-body");
  tbody.innerHTML = alerts.map(a => `
    <tr>
      <td>${a.name}</td>
      <td>${a.symbol}</td>
      <td>${a.condition_type}</td>
      <td>${a.threshold || '-'}</td>
      <td><span class="badge ${a.active?'badge-active':'badge-inactive'}">${a.active?'Active':'Off'}</span></td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteAlert(${a.id})">Del</button></td>
    </tr>`).join("");
}

async function createAlert() {
  const data = {
    name:           document.getElementById("al-name").value,
    symbol:         document.getElementById("al-symbol").value,
    condition_type: document.getElementById("al-type").value,
    threshold:      parseFloat(document.getElementById("al-threshold").value) || null,
  };
  await api("/api/alerts/", { method: "POST", body: JSON.stringify(data) });
  showToast("Alert created", "success");
  loadAlerts();
}

async function deleteAlert(id) {
  await api(`/api/alerts/${id}`, { method: "DELETE" });
  showToast("Alert deleted", "info");
  loadAlerts();
}

// ── Strategies ────────────────────────────────────────────────────────────
async function loadStrategies() {
  const strats = await api("/api/strategy/");
  const list = document.getElementById("strategy-list");
  list.innerHTML = strats.map(s => `
    <div class="strategy-list-item">
      <div>
        <div class="strat-name">${s.name}</div>
        <div class="strat-meta">${s.symbol} · ${s.timeframe} · ${s.mode}</div>
      </div>
      <div class="actions">
        <span class="badge ${s.active?'badge-active':'badge-inactive'}">${s.active?'Active':'Idle'}</span>
        <button class="btn btn-success btn-sm" onclick="activateStrategy(${s.id})">▶</button>
        <button class="btn btn-danger btn-sm" onclick="deleteStrategy(${s.id})">✕</button>
      </div>
    </div>`).join("");
}

async function activateStrategy(id) {
  await api(`/api/strategy/${id}/activate`, { method: "POST" });
  showToast("Strategy activated", "success");
  loadStrategies();
}

async function deleteStrategy(id) {
  await api(`/api/strategy/${id}`, { method: "DELETE" });
  showToast("Strategy deleted", "info");
  loadStrategies();
}

// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  connectWS();
  document.getElementById("panel-chart").classList.add("active");
  document.querySelector('[data-tab="chart"]').classList.add("active");
});
