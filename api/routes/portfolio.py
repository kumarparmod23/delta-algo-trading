from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.models import PortfolioSnapshot
from portfolio.tracker import get_portfolio_summary
from config import settings

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    mode = "live" if settings.live_trading_enabled else "paper"
    return await get_portfolio_summary(db, mode)


@router.get("/snapshots")
async def snapshots(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.desc()).limit(168)
    )
    rows = result.scalars().all()
    return [{"timestamp": str(r.timestamp), "total_value": r.total_value,
             "realized_pnl": r.realized_pnl, "unrealized_pnl": r.unrealized_pnl} for r in rows]
