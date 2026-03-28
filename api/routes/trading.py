from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.models import Trade
from core.schemas import OrderRequest
from trading.order_manager import OrderManager
from trading.paper_trader import get_balance, close_paper_trade, get_open_paper_trades
from trading.live_trader import get_live_positions, get_live_balance
from config import settings

router = APIRouter(prefix="/api/trading", tags=["trading"])


@router.get("/mode")
async def get_mode():
    return {"mode": "live" if settings.live_trading_enabled else "paper"}


@router.post("/order")
async def place_order(req: OrderRequest, db: AsyncSession = Depends(get_db)):
    mode = "live" if settings.live_trading_enabled else "paper"
    om   = OrderManager(mode=mode)
    risk = {"stop_loss_pct": 2.0, "take_profit_pct": 4.0, "position_size_pct": 10.0}
    if req.stop_loss:
        risk["stop_loss_pct"] = req.stop_loss
    result = await om.place_order(req.symbol, req.side, req.qty, risk)
    return result


@router.get("/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    trades = await get_open_paper_trades(db)
    return [{"id": t.id, "symbol": t.symbol, "side": t.side, "qty": t.qty,
             "entry_price": t.entry_price, "status": t.status} for t in trades]


@router.delete("/order/{trade_id}")
async def close_order(trade_id: int, exit_price: float, db: AsyncSession = Depends(get_db)):
    return await close_paper_trade(trade_id, exit_price)


@router.get("/balance")
async def balance(db: AsyncSession = Depends(get_db)):
    if settings.live_trading_enabled:
        return await get_live_balance()
    bal = await get_balance(db)
    return {"available": bal, "currency": "USD", "mode": "paper"}


@router.get("/history")
async def trade_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).order_by(Trade.entry_time.desc()))
    trades = result.scalars().all()
    return [{"id": t.id, "symbol": t.symbol, "side": t.side, "qty": t.qty,
             "entry_price": t.entry_price, "exit_price": t.exit_price,
             "pnl": t.pnl, "status": t.status, "mode": t.mode,
             "entry_time": str(t.entry_time)} for t in trades]
