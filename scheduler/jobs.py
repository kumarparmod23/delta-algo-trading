from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import AsyncSessionLocal
from data.market_data import fetch_and_store_candles
from strategy.executor import run_all_strategies
from strategy.registry import get_all
from alerts.manager import check_alerts
from portfolio.tracker import save_snapshot

scheduler = AsyncIOScheduler()


async def _refresh_candles():
    strategies = get_all()
    async with AsyncSessionLocal() as db:
        seen = set()
        for strat in strategies.values():
            key = (strat["symbol"], strat["timeframe"])
            if key not in seen:
                seen.add(key)
                await fetch_and_store_candles(db, strat["symbol"], strat["timeframe"])


async def _check_alerts_job():
    async with AsyncSessionLocal() as db:
        triggered = await check_alerts(db)
        if triggered:
            from api.websocket import manager
            for t in triggered:
                await manager.broadcast({"type": "alert", **t})


async def _snapshot_job():
    async with AsyncSessionLocal() as db:
        await save_snapshot(db, "paper")


def start_scheduler():
    scheduler.add_job(_refresh_candles,   "interval", minutes=1,  id="refresh_candles")
    scheduler.add_job(run_all_strategies, "interval", minutes=1,  id="run_strategies")
    scheduler.add_job(_check_alerts_job,  "interval", seconds=15, id="check_alerts")
    scheduler.add_job(_snapshot_job,      "interval", hours=1,    id="snapshot")
    scheduler.start()
