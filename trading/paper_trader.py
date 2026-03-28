from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import Trade, PaperBalance
from core.database import AsyncSessionLocal
from config import settings


async def get_balance(db: AsyncSession) -> float:
    result = await db.execute(select(PaperBalance))
    bal = result.scalars().first()
    if not bal:
        bal = PaperBalance(available=settings.paper_initial_balance)
        db.add(bal)
        await db.commit()
    return bal.available


async def place_paper_order(symbol: str, side: str, qty: float, price: float,
                            stop_loss: float = None, take_profit: float = None,
                            strategy_id: int = None) -> dict:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PaperBalance))
        bal = result.scalars().first()
        if not bal:
            bal = PaperBalance(available=settings.paper_initial_balance)
            db.add(bal)
            await db.flush()

        cost = qty * price
        if side == "buy" and bal.available < cost:
            return {"error": "Insufficient paper balance"}

        if side == "buy":
            bal.available -= cost
        trade = Trade(
            strategy_id=strategy_id, symbol=symbol, side=side,
            qty=qty, entry_price=price, mode="paper", status="open",
            entry_time=datetime.utcnow(),
        )
        if stop_loss:   trade.exit_price = stop_loss
        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        return {"trade_id": trade.id, "symbol": symbol, "side": side, "qty": qty, "price": price}


async def close_paper_trade(trade_id: int, exit_price: float) -> dict:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Trade).where(Trade.id == trade_id))
        trade = result.scalars().first()
        if not trade:
            return {"error": "Trade not found"}

        pnl = (exit_price - trade.entry_price) * trade.qty if trade.side == "buy" \
              else (trade.entry_price - exit_price) * trade.qty

        trade.exit_price = exit_price
        trade.pnl = round(pnl, 6)
        trade.status = "closed"
        trade.exit_time = datetime.utcnow()

        result2 = await db.execute(select(PaperBalance))
        bal = result2.scalars().first()
        if bal:
            bal.available += trade.qty * exit_price + (pnl if trade.side == "sell" else 0)
        await db.commit()
        return {"trade_id": trade_id, "pnl": pnl, "exit_price": exit_price}


async def get_open_paper_trades(db: AsyncSession) -> list:
    result = await db.execute(select(Trade).where(Trade.mode == "paper", Trade.status == "open"))
    return result.scalars().all()
