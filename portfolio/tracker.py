from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Trade, PaperBalance, PortfolioSnapshot
from data.ticker import get_ticker
from datetime import datetime


async def get_portfolio_summary(db: AsyncSession, mode: str = "paper") -> dict:
    # Balance
    if mode == "paper":
        result = await db.execute(select(PaperBalance))
        bal = result.scalars().first()
        available = bal.available if bal else 0
    else:
        from trading.live_trader import get_live_balance
        balances = await get_live_balance()
        available = sum(float(b.get("available_balance", 0)) for b in balances)

    # Open trades with unrealized P&L
    result = await db.execute(select(Trade).where(Trade.mode == mode, Trade.status == "open"))
    open_trades = result.scalars().all()
    unrealized_pnl = 0.0
    positions = []
    for t in open_trades:
        ticker = get_ticker(t.symbol)
        current = float(ticker.get("close", t.entry_price))
        upnl = (current - t.entry_price) * t.qty if t.side == "buy" else (t.entry_price - current) * t.qty
        unrealized_pnl += upnl
        positions.append({
            "trade_id": t.id, "symbol": t.symbol, "side": t.side,
            "qty": t.qty, "entry_price": t.entry_price,
            "current_price": current, "unrealized_pnl": round(upnl, 4),
        })

    # Realized P&L
    result2 = await db.execute(
        select(func.sum(Trade.pnl)).where(Trade.mode == mode, Trade.status == "closed")
    )
    realized_pnl = result2.scalar() or 0.0

    return {
        "available_balance": round(available, 2),
        "unrealized_pnl": round(unrealized_pnl, 4),
        "realized_pnl": round(realized_pnl, 4),
        "total_value": round(available + unrealized_pnl, 2),
        "positions": positions,
        "mode": mode,
    }


async def save_snapshot(db: AsyncSession, mode: str = "paper"):
    summary = await get_portfolio_summary(db, mode)
    snap = PortfolioSnapshot(
        total_value=summary["total_value"],
        realized_pnl=summary["realized_pnl"],
        unrealized_pnl=summary["unrealized_pnl"],
        mode=mode,
    )
    db.add(snap)
    await db.commit()
