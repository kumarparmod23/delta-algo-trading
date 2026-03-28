from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Alert, AlertHistory
from data.ticker import get_ticker
from datetime import datetime


async def check_alerts(db: AsyncSession):
    result = await db.execute(select(Alert).where(Alert.active == True))
    alerts = result.scalars().all()
    triggered = []
    for alert in alerts:
        ticker = get_ticker(alert.symbol)
        if not ticker:
            continue
        price = float(ticker.get("close", 0))
        fired = False
        if alert.condition_type == "price_above" and alert.threshold and price > alert.threshold:
            fired = True
        elif alert.condition_type == "price_below" and alert.threshold and price < alert.threshold:
            fired = True

        if fired:
            msg = f"{alert.name}: {alert.symbol} price {price} triggered {alert.condition_type} @ {alert.threshold}"
            hist = AlertHistory(alert_id=alert.id, triggered_at=datetime.utcnow(),
                                trigger_value=price, message=msg)
            db.add(hist)
            triggered.append({"alert_id": alert.id, "message": msg, "price": price})

    if triggered:
        await db.commit()
    return triggered
