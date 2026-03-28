import json
import time
import pandas as pd
from datetime import datetime
from strategy.builder import evaluate_strategy, compute_all
from backtesting.metrics import calculate_metrics
from exchange.delta_client import delta_client


async def run_backtest(strategy: dict, symbol: str, timeframe: str,
                       start_date: str, end_date: str, initial_capital: float) -> dict:
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts   = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

    raw = await delta_client.get_candles(symbol, timeframe, start_ts, end_ts)
    if not raw:
        return {"error": "No candle data available for this range"}

    df = pd.DataFrame(raw).rename(columns={"time": "timestamp"})
    df = df.sort_values("timestamp").reset_index(drop=True)

    capital   = initial_capital
    position  = None
    trades    = []
    equity    = [capital]

    risk = json.loads(strategy.get("risk_json", "{}"))
    sl_pct = risk.get("stop_loss_pct", 2.0) / 100
    tp_pct = risk.get("take_profit_pct", 4.0) / 100
    size_pct = risk.get("position_size_pct", 10.0) / 100

    for i in range(50, len(df)):
        window = df.iloc[:i + 1].copy()
        signals = evaluate_strategy(window, strategy["conditions_json"])
        price = df["close"].iloc[i]

        # Check SL/TP on open position
        if position:
            if position["side"] == "buy":
                sl_hit = price <= position["sl"]
                tp_hit = price >= position["tp"]
            else:
                sl_hit = price >= position["sl"]
                tp_hit = price <= position["tp"]

            if sl_hit or tp_hit or signals["exit"]:
                exit_price = position["sl"] if sl_hit else (position["tp"] if tp_hit else price)
                pnl = (exit_price - position["entry"]) * position["qty"] if position["side"] == "buy" \
                      else (position["entry"] - exit_price) * position["qty"]
                capital += pnl
                trades.append({
                    "entry": position["entry"], "exit": exit_price,
                    "side": position["side"], "qty": position["qty"],
                    "pnl": round(pnl, 4),
                    "exit_reason": "sl" if sl_hit else ("tp" if tp_hit else "signal"),
                    "timestamp": int(df["timestamp"].iloc[i]),
                })
                position = None
                equity.append(capital)
                continue

        # Entry
        if not position:
            qty = (capital * size_pct) / price
            if signals["entry_long"]:
                position = {
                    "side": "buy", "entry": price, "qty": qty,
                    "sl": price * (1 - sl_pct), "tp": price * (1 + tp_pct),
                }
            elif signals["entry_short"]:
                position = {
                    "side": "sell", "entry": price, "qty": qty,
                    "sl": price * (1 + sl_pct), "tp": price * (1 - tp_pct),
                }

    # Close any open position at end
    if position:
        last_price = df["close"].iloc[-1]
        pnl = (last_price - position["entry"]) * position["qty"] if position["side"] == "buy" \
              else (position["entry"] - last_price) * position["qty"]
        capital += pnl
        trades.append({
            "entry": position["entry"], "exit": last_price,
            "side": position["side"], "qty": position["qty"],
            "pnl": round(pnl, 4), "exit_reason": "end_of_data",
            "timestamp": int(df["timestamp"].iloc[-1]),
        })
        equity.append(capital)

    metrics = calculate_metrics(trades, equity, initial_capital)
    return {
        "metrics": metrics,
        "trades": trades,
        "equity_curve": [{"t": i, "v": round(v, 2)} for i, v in enumerate(equity)],
    }
