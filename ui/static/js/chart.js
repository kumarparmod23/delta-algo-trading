let mainChart, candleSeries, rsiChart, rsiSeries, macdChart, macdSeries, signalSeries, histSeries;
let smaSeries = {}, emaSeries = {}, bbSeries = {};

function initCharts() {
  const opts = {
    layout: { background: { color: "#151820" }, textColor: "#94a3b8" },
    grid: { vertLines: { color: "#1e2130" }, horzLines: { color: "#1e2130" } },
    timeScale: { timeVisible: true, secondsVisible: false },
    crosshair: { mode: 1 },
  };

  mainChart = LightweightCharts.createChart(document.getElementById("main-chart"), { ...opts, height: document.getElementById("main-chart").offsetHeight });
  candleSeries = mainChart.addCandlestickSeries({
    upColor: "#26a69a", downColor: "#ef5350",
    borderUpColor: "#26a69a", borderDownColor: "#ef5350",
    wickUpColor: "#26a69a", wickDownColor: "#ef5350",
  });

  rsiChart = LightweightCharts.createChart(document.getElementById("rsi-chart"), { ...opts, height: document.getElementById("rsi-chart").offsetHeight });
  rsiSeries = rsiChart.addLineSeries({ color: "#8b5cf6", lineWidth: 1 });
  rsiChart.addLineSeries({ color: "rgba(239,83,80,.3)", lineWidth: 1 }).setData([]);

  macdChart = LightweightCharts.createChart(document.getElementById("macd-chart"), { ...opts, height: document.getElementById("macd-chart").offsetHeight });
  macdSeries   = macdChart.addLineSeries({ color: "#3b82f6", lineWidth: 1 });
  signalSeries = macdChart.addLineSeries({ color: "#f59e0b", lineWidth: 1 });
  histSeries   = macdChart.addHistogramSeries({ color: "#26a69a" });

  // Sync time scales
  mainChart.timeScale().subscribeVisibleLogicalRangeChange(r => {
    if (r) { rsiChart.timeScale().setVisibleLogicalRange(r); macdChart.timeScale().setVisibleLogicalRange(r); }
  });
}

async function loadChart(symbol, timeframe) {
  document.getElementById("chart-loading").style.display = "block";
  const data = await api(`/api/market/candles/${symbol}?timeframe=${timeframe}&indicators=true&price_action=true`);
  document.getElementById("chart-loading").style.display = "none";
  if (!data || !data.length) return;

  const candles = data.map(d => ({ time: d.timestamp, open: d.open, high: d.high, low: d.low, close: d.close }));
  candleSeries.setData(candles);

  // RSI
  const rsi = data.filter(d => d.rsi14).map(d => ({ time: d.timestamp, value: d.rsi14 }));
  rsiSeries.setData(rsi);

  // MACD
  const macdData = data.filter(d => d.macd).map(d => ({ time: d.timestamp, value: d.macd }));
  const sigData  = data.filter(d => d.macd_signal).map(d => ({ time: d.timestamp, value: d.macd_signal }));
  const histData = data.filter(d => d.macd_hist).map(d => ({ time: d.timestamp, value: d.macd_hist, color: d.macd_hist >= 0 ? "#26a69a" : "#ef5350" }));
  macdSeries.setData(macdData);
  signalSeries.setData(sigData);
  histSeries.setData(histData);

  renderOverlays(data);
  renderPriceActionMarkers(data);
  mainChart.timeScale().fitContent();
  updateAnalysisPanel(data[data.length - 1]);
}

function renderOverlays(data) {
  // Remove old
  Object.values(smaSeries).forEach(s => { try { mainChart.removeSeries(s); } catch(e){} });
  Object.values(emaSeries).forEach(s => { try { mainChart.removeSeries(s); } catch(e){} });
  Object.values(bbSeries).forEach(s  => { try { mainChart.removeSeries(s); } catch(e){} });
  smaSeries = {}; emaSeries = {}; bbSeries = {};

  if (document.getElementById("ind-sma").classList.contains("active")) {
    smaSeries.sma20 = mainChart.addLineSeries({ color: "#f59e0b", lineWidth: 1, title: "SMA20" });
    smaSeries.sma50 = mainChart.addLineSeries({ color: "#3b82f6", lineWidth: 1, title: "SMA50" });
    smaSeries.sma20.setData(data.filter(d => d.sma20).map(d => ({ time: d.timestamp, value: d.sma20 })));
    smaSeries.sma50.setData(data.filter(d => d.sma50).map(d => ({ time: d.timestamp, value: d.sma50 })));
  }
  if (document.getElementById("ind-ema").classList.contains("active")) {
    emaSeries.ema9  = mainChart.addLineSeries({ color: "#ec4899", lineWidth: 1, title: "EMA9" });
    emaSeries.ema21 = mainChart.addLineSeries({ color: "#a78bfa", lineWidth: 1, title: "EMA21" });
    emaSeries.ema9.setData(data.filter(d => d.ema9).map(d => ({ time: d.timestamp, value: d.ema9 })));
    emaSeries.ema21.setData(data.filter(d => d.ema21).map(d => ({ time: d.timestamp, value: d.ema21 })));
  }
  if (document.getElementById("ind-bb").classList.contains("active")) {
    bbSeries.upper = mainChart.addLineSeries({ color: "rgba(59,130,246,.5)", lineWidth: 1, title: "BB Upper" });
    bbSeries.lower = mainChart.addLineSeries({ color: "rgba(59,130,246,.5)", lineWidth: 1, title: "BB Lower" });
    bbSeries.mid   = mainChart.addLineSeries({ color: "rgba(59,130,246,.3)", lineWidth: 1, lineStyle: 2 });
    bbSeries.upper.setData(data.filter(d => d.bb_upper).map(d => ({ time: d.timestamp, value: d.bb_upper })));
    bbSeries.lower.setData(data.filter(d => d.bb_lower).map(d => ({ time: d.timestamp, value: d.bb_lower })));
    bbSeries.mid.setData(data.filter(d => d.bb_mid).map(d => ({ time: d.timestamp, value: d.bb_mid })));
  }
}

function renderPriceActionMarkers(data) {
  if (!document.getElementById("ind-pa").classList.contains("active")) return;
  const markers = [];
  data.forEach(d => {
    if (d.bullish_engulfing) markers.push({ time: d.timestamp, position: "belowBar", color: "#26a69a", shape: "arrowUp", text: "BE" });
    if (d.bearish_engulfing) markers.push({ time: d.timestamp, position: "aboveBar", color: "#ef5350", shape: "arrowDown", text: "BE" });
    if (d.hammer)            markers.push({ time: d.timestamp, position: "belowBar", color: "#26a69a", shape: "arrowUp", text: "H" });
    if (d.shooting_star)     markers.push({ time: d.timestamp, position: "aboveBar", color: "#ef5350", shape: "arrowDown", text: "SS" });
    if (d.pin_bar_bull)      markers.push({ time: d.timestamp, position: "belowBar", color: "#3b82f6", shape: "arrowUp", text: "PB" });
    if (d.pin_bar_bear)      markers.push({ time: d.timestamp, position: "aboveBar", color: "#f59e0b", shape: "arrowDown", text: "PB" });
    if (d.doji)              markers.push({ time: d.timestamp, position: "aboveBar", color: "#8b5cf6", shape: "circle", text: "D" });
    if (d.morning_star)      markers.push({ time: d.timestamp, position: "belowBar", color: "#26a69a", shape: "arrowUp", text: "MS" });
    if (d.evening_star)      markers.push({ time: d.timestamp, position: "aboveBar", color: "#ef5350", shape: "arrowDown", text: "ES" });
    if (d.inside_bar)        markers.push({ time: d.timestamp, position: "aboveBar", color: "#94a3b8", shape: "circle", text: "IB" });
  });
  candleSeries.setMarkers(markers.sort((a, b) => a.time - b.time));
}

function updateAnalysisPanel(last) {
  if (!last) return;
  const rsi = last.rsi14 || 0;
  document.getElementById("ind-rsi").textContent   = rsi.toFixed(1);
  document.getElementById("ind-rsi").className     = rsi > 70 ? "value red" : rsi < 30 ? "value green" : "value";
  document.getElementById("ind-macd").textContent  = (last.macd || 0).toFixed(4);
  document.getElementById("ind-bb-u").textContent  = (last.bb_upper || 0).toFixed(2);
  document.getElementById("ind-bb-l").textContent  = (last.bb_lower || 0).toFixed(2);
  document.getElementById("ind-atr").textContent   = (last.atr14 || 0).toFixed(4);
}

// Indicator toggles
document.querySelectorAll(".ind-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    btn.classList.toggle("active");
    reloadChart();
  });
});

function reloadChart() {
  const sym = document.getElementById("symbol-select").value;
  const tf  = document.getElementById("tf-select").value;
  if (sym) loadChart(sym, tf);
}

// Symbol + timeframe controls
async function initSymbols() {
  const syms = await api("/api/market/symbols");
  const sel = document.getElementById("symbol-select");
  const defaultSyms = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"];
  const filtered = syms.filter(s => defaultSyms.includes(s)).concat(
    syms.filter(s => !defaultSyms.includes(s)).slice(0, 50)
  );
  sel.innerHTML = filtered.map(s => `<option value="${s}">${s}</option>`).join("");
  loadChart(sel.value, document.getElementById("tf-select").value);
}

document.getElementById("symbol-select").addEventListener("change", reloadChart);
document.getElementById("tf-select").addEventListener("change", reloadChart);
document.getElementById("refresh-btn").addEventListener("click", reloadChart);

window.addEventListener("DOMContentLoaded", () => {
  initCharts();
  initSymbols();
  loadOrderbook();
  setInterval(loadOrderbook, 5000);
  setInterval(updateLivePrices, 3000);
});

async function loadOrderbook() {
  const sym = document.getElementById("symbol-select").value;
  if (!sym) return;
  const ob = await api(`/api/market/orderbook/${sym}?depth=8`);
  const asks = (ob.sell || []).slice(0, 8);
  const bids = (ob.buy  || []).slice(0, 8);
  document.getElementById("ob-asks").innerHTML =
    asks.map(a => `<tr><td class="ask">${parseFloat(a.price).toFixed(2)}</td><td>${a.size}</td></tr>`).join("");
  document.getElementById("ob-bids").innerHTML =
    bids.map(b => `<tr><td class="bid">${parseFloat(b.price).toFixed(2)}</td><td>${b.size}</td></tr>`).join("");
}

async function updateLivePrices() {
  const tickers = await api("/api/market/tickers");
  const syms = ["BTCUSD","ETHUSD","SOLUSD"];
  syms.forEach(sym => {
    const el = document.getElementById(`price-${sym}`);
    if (!el) return;
    const t = Array.isArray(tickers) ? tickers.find(x => x.symbol === sym) : tickers[sym];
    if (t) el.textContent = parseFloat(t.close || t.mark_price || 0).toFixed(2);
  });
}
