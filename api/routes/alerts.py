from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.models import Alert, AlertHistory
from core.schemas import AlertCreate, AlertOut
from api.auth import require_auth, require_admin

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertOut])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_auth),
):
    result = await db.execute(select(Alert))
    return result.scalars().all()


@router.post("/", response_model=AlertOut)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    alert = Alert(**data.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{aid}")
async def delete_alert(
    aid: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    result = await db.execute(select(Alert).where(Alert.id == aid))
    a = result.scalars().first()
    if not a:
        raise HTTPException(404)
    await db.delete(a)
    await db.commit()
    return {"deleted": aid}


@router.get("/history")
async def alert_history(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_auth),
):
    result = await db.execute(
        select(AlertHistory).order_by(AlertHistory.triggered_at.desc()).limit(100)
    )
    rows = result.scalars().all()
    return [{"id": r.id, "alert_id": r.alert_id, "message": r.message,
             "trigger_value": r.trigger_value, "triggered_at": str(r.triggered_at)} for r in rows]
