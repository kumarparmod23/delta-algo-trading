import numpy as np
from typing import List


def calculate_metrics(trades: list, equity_curve: list, initial_capital: float) -> dict:
    if not trades:
        return {"error": "No trades executed"}

    pnls   = [t["pnl"] for t in trades if t["pnl"] is not None]
    wins   = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    total_pnl    = sum(pnls)
    win_rate     = len(wins) / len(pnls) * 100 if pnls else 0
    avg_win      = sum(wins)  / len(wins)  if wins   else 0
    avg_loss     = sum(losses)/ len(losses)if losses else 0
    profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float("inf")

    # Max drawdown
    peak = initial_capital
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100
        if dd > max_dd:
            max_dd = dd

    # Sharpe ratio (annualized, assume 252 trading days)
    returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
    sharpe  = 0.0
    if len(returns) > 1 and returns.std() > 0:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

    final_capital = equity_curve[-1] if equity_curve else initial_capital
    return {
        "total_trades":   len(pnls),
        "winning_trades": len(wins),
        "losing_trades":  len(losses),
        "win_rate_pct":   round(win_rate, 2),
        "total_pnl":      round(total_pnl, 4),
        "total_return_pct": round((final_capital - initial_capital) / initial_capital * 100, 2),
        "avg_win":        round(avg_win, 4),
        "avg_loss":       round(avg_loss, 4),
        "profit_factor":  round(profit_factor, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio":   round(sharpe, 3),
        "final_capital":  round(final_capital, 2),
        "initial_capital": initial_capital,
    }
