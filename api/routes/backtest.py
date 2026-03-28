import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.models import Strategy, BacktestResult
from core.schemas import BacktestRequest
from backtesting.engine import run_backtest

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run")
async def run(req: BacktestRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Strategy).where(Strategy.id == req.strategy_id))
    s = result.scalars().first()
    if not s:
        raise HTTPException(404, "Strategy not found")

    bt = await run_backtest(
        strategy={"conditions_json": s.conditions_json, "risk_json": s.risk_json},
        symbol=req.symbol, timeframe=req.timeframe,
        start_date=req.start_date, end_date=req.end_date,
        initial_capital=req.initial_capital,
    )
    if "error" in bt:
        raise HTTPException(400, bt["error"])

    record = BacktestResult(
        strategy_id=req.strategy_id, symbol=req.symbol, timeframe=req.timeframe,
        start_date=req.start_date, end_date=req.end_date,
        params_json=req.model_dump_json(),
        metrics_json=json.dumps(bt["metrics"]),
        equity_curve_json=json.dumps(bt["equity_curve"]),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {
        "backtest_id": record.id,
        "metrics": bt["metrics"],
        "trades": bt["trades"],
        "equity_curve": bt["equity_curve"],
    }


@router.get("/results/{strategy_id}")
async def get_results(strategy_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BacktestResult).where(BacktestResult.strategy_id == strategy_id)
        .order_by(BacktestResult.created_at.desc())
    )
    rows = result.scalars().all()
    return [{"id": r.id, "symbol": r.symbol, "timeframe": r.timeframe,
             "metrics": json.loads(r.metrics_json), "created_at": str(r.created_at)} for r in rows]
