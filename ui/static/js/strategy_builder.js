const INDICATORS = ["RSI","MACD","MACD_Signal","MACD_Hist","BB_Upper","BB_Lower","BB_Mid","SMA20","SMA50","SMA200","EMA9","EMA21","ATR","VWAP","Stoch_K","Stoch_D"];
const PA_PATTERNS = ["bullish_engulfing","bearish_engulfing","hammer","shooting_star","pin_bar_bull","pin_bar_bear","doji","morning_star","evening_star","inside_bar","marubozu_bull","marubozu_bear","tweezer_top","tweezer_bottom","at_support","at_resistance","uptrend","downtrend","bos_bullish","bos_bearish","choch_bullish","choch_bearish","in_demand_zone","in_supply_zone","breakout_up","breakout_down"];
const OPERATORS = ["greater_than","less_than","crosses_above","crosses_below","price_above","price_below"];

function conditionRow(section) {
  const div = document.createElement("div");
  div.className = "condition-item";
  div.innerHTML = `
    <select class="cond-type" onchange="updateCondRow(this)">
      <option value="indicator">Indicator</option>
      <option value="price_action">Price Action</option>
    </select>
    <select class="cond-detail"></select>
    <select class="cond-op">${OPERATORS.map(o => `<option>${o}</option>`).join("")}</select>
    <input class="cond-val" type="number" placeholder="value" step="any" style="width:70px;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:4px;border-radius:4px;">
    <button class="del-btn" onclick="this.parentElement.remove()">✕</button>`;
  const detail = div.querySelector(".cond-detail");
  INDICATORS.forEach(i => { const o = document.createElement("option"); o.value = i.toLowerCase(); o.textContent = i; detail.appendChild(o); });
  document.getElementById(`cond-${section}`).appendChild(div);
}

function updateCondRow(sel) {
  const row = sel.parentElement;
  const detail = row.querySelector(".cond-detail");
  const op     = row.querySelector(".cond-op");
  const val    = row.querySelector(".cond-val");
  detail.innerHTML = "";
  if (sel.value === "price_action") {
    PA_PATTERNS.forEach(p => { const o = document.createElement("option"); o.value = p; o.textContent = p.replace(/_/g," "); detail.appendChild(o); });
    op.style.display = "none"; val.style.display = "none";
  } else {
    INDICATORS.forEach(i => { const o = document.createElement("option"); o.value = i.toLowerCase(); o.textContent = i; detail.appendChild(o); });
    op.style.display = ""; val.style.display = "";
  }
}

function buildConditions(section) {
  const rows = document.querySelectorAll(`#cond-${section} .condition-item`);
  return Array.from(rows).map(row => {
    const type   = row.querySelector(".cond-type").value;
    const detail = row.querySelector(".cond-detail").value;
    const op     = row.querySelector(".cond-op").value;
    const val    = parseFloat(row.querySelector(".cond-val").value);
    if (type === "price_action") return { type: "price_action", pattern: detail };
    return { type: "indicator", indicator: detail, operator: op, value: isNaN(val) ? null : val };
  });
}

async function saveStrategy() {
  const conditions = {
    entry_long:  buildConditions("long"),
    entry_short: buildConditions("short"),
    exit:        buildConditions("exit"),
  };
  const risk = {
    stop_loss_pct:      parseFloat(document.getElementById("sl-pct").value) || 2,
    take_profit_pct:    parseFloat(document.getElementById("tp-pct").value) || 4,
    position_size_pct:  parseFloat(document.getElementById("size-pct").value) || 10,
    qty:                parseFloat(document.getElementById("order-qty").value) || 1,
  };
  const data = {
    name:            document.getElementById("strat-name").value,
    symbol:          document.getElementById("strat-symbol").value,
    timeframe:       document.getElementById("strat-tf").value,
    conditions_json: JSON.stringify(conditions),
    risk_json:       JSON.stringify(risk),
    mode:            document.getElementById("strat-mode").value,
  };
  if (!data.name || !data.symbol) { showToast("Name and symbol required", "error"); return; }
  await api("/api/strategy/", { method: "POST", body: JSON.stringify(data) });
  showToast(`Strategy "${data.name}" saved!`, "success");
  loadStrategies();
}

async function runBacktest() {
  const strats = await api("/api/strategy/");
  if (!strats.length) { showToast("Create a strategy first", "error"); return; }
  const sid = strats[0].id;
  const req = {
    strategy_id:     parseInt(document.getElementById("bt-strategy").value) || sid,
    symbol:          document.getElementById("bt-symbol").value,
    timeframe:       document.getElementById("bt-tf").value,
    start_date:      document.getElementById("bt-start").value,
    end_date:        document.getElementById("bt-end").value,
    initial_capital: parseFloat(document.getElementById("bt-capital").value) || 10000,
  };
  document.getElementById("bt-run-btn").textContent = "Running...";
  const result = await api("/api/backtest/run", { method: "POST", body: JSON.stringify(req) });
  document.getElementById("bt-run-btn").textContent = "Run Backtest";
  if (result.error) { showToast(result.error, "error"); return; }
  renderBacktestResults(result);
}

function renderBacktestResults(result) {
  const m = result.metrics;
  document.getElementById("bt-results").style.display = "block";
  const metrics = [
    { label: "Total Trades", value: m.total_trades, color: "" },
    { label: "Win Rate", value: m.win_rate_pct + "%", color: m.win_rate_pct >= 50 ? "green" : "red" },
    { label: "Total P&L", value: "$" + m.total_pnl, color: m.total_pnl >= 0 ? "green" : "red" },
    { label: "Return", value: m.total_return_pct + "%", color: m.total_return_pct >= 0 ? "green" : "red" },
    { label: "Sharpe", value: m.sharpe_ratio, color: m.sharpe_ratio >= 1 ? "green" : "red" },
    { label: "Max DD", value: m.max_drawdown_pct + "%", color: m.max_drawdown_pct > 20 ? "red" : "green" },
    { label: "Profit Factor", value: m.profit_factor, color: m.profit_factor >= 1.5 ? "green" : "red" },
    { label: "Final Capital", value: "$" + m.final_capital, color: "" },
  ];
  document.getElementById("bt-metrics").innerHTML = metrics.map(m => `
    <div class="metric-card">
      <div class="m-label">${m.label}</div>
      <div class="m-value ${m.color}">${m.value}</div>
    </div>`).join("");

  // Equity curve chart
  renderEquityCurve(result.equity_curve);

  // Trade table
  document.getElementById("bt-trade-body").innerHTML = result.trades.map(t => `
    <tr>
      <td class="${t.side==='buy'?'green':'red'}">${t.side.toUpperCase()}</td>
      <td>${t.entry}</td>
      <td>${t.exit}</td>
      <td class="${t.pnl>=0?'green':'red'}">${t.pnl>=0?'+':''}${t.pnl}</td>
      <td>${t.exit_reason}</td>
    </tr>`).join("");
}

function renderEquityCurve(data) {
  const canvas = document.getElementById("equity-curve-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.offsetWidth;
  const h = canvas.height = 200;
  ctx.clearRect(0, 0, w, h);
  if (!data.length) return;
  const vals = data.map(d => d.v);
  const min = Math.min(...vals), max = Math.max(...vals);
  const range = max - min || 1;
  ctx.strokeStyle = "#3b82f6";
  ctx.lineWidth = 2;
  ctx.beginPath();
  data.forEach((d, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((d.v - min) / range) * (h - 20) - 10;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
  // Fill
  ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
  ctx.fillStyle = "rgba(59,130,246,.1)";
  ctx.fill();
}

// Load strategies into backtest dropdown
async function loadBacktestStrategies() {
  const strats = await api("/api/strategy/");
  const sel = document.getElementById("bt-strategy");
  if (sel) sel.innerHTML = strats.map(s => `<option value="${s.id}">${s.name} (${s.symbol})</option>`).join("");
}
