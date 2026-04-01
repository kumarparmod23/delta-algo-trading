import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.models import Strategy
from core.schemas import StrategyCreate, StrategyOut
from strategy.registry import register, unregister
from api.auth import require_auth, require_admin

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


@router.get("/", response_model=list[StrategyOut])
async def list_strategies(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_auth),
):
    result = await db.execute(select(Strategy))
    return result.scalars().all()


@router.post("/", response_model=StrategyOut)
async def create_strategy(
    data: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    s = Strategy(**data.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.put("/{sid}", response_model=StrategyOut)
async def update_strategy(
    sid: int,
    data: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    result = await db.execute(select(Strategy).where(Strategy.id == sid))
    s = result.scalars().first()
    if not s:
        raise HTTPException(404, "Strategy not found")
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/{sid}")
async def delete_strategy(
    sid: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    result = await db.execute(select(Strategy).where(Strategy.id == sid))
    s = result.scalars().first()
    if not s:
        raise HTTPException(404, "Strategy not found")
    unregister(sid)
    await db.delete(s)
    await db.commit()
    return {"deleted": sid}


@router.post("/{sid}/activate")
async def activate_strategy(
    sid: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    result = await db.execute(select(Strategy).where(Strategy.id == sid))
    s = result.scalars().first()
    if not s:
        raise HTTPException(404, "Strategy not found")
    s.active = True
    await db.commit()
    register(sid, {
        "name": s.name, "symbol": s.symbol, "timeframe": s.timeframe,
        "conditions_json": s.conditions_json, "risk_json": s.risk_json,
        "mode": s.mode, "qty": json.loads(s.risk_json).get("qty", 1),
    })
    return {"activated": sid}


@router.post("/{sid}/deactivate")
async def deactivate_strategy(
    sid: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    result = await db.execute(select(Strategy).where(Strategy.id == sid))
    s = result.scalars().first()
    if not s:
        raise HTTPException(404)
    s.active = False
    await db.commit()
    unregister(sid)
    return {"deactivated": sid}
