import time
import pandas as pd
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Candle
from exchange.delta_client import delta_client

RESOLUTION_SECONDS = {
    "1m": 60, "3m": 180, "5m": 300, "15m": 900,
    "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400,
    "6h": 21600, "12h": 43200, "1d": 86400, "1w": 604800,
}


async def fetch_and_store_candles(db: AsyncSession, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
    secs = RESOLUTION_SECONDS.get(timeframe, 900)
    end = int(time.time())
    start = end - secs * limit

    raw = await delta_client.get_candles(symbol, timeframe, start, end)
    if not raw:
        return pd.DataFrame()

    await db.execute(delete(Candle).where(
        Candle.symbol == symbol, Candle.timeframe == timeframe
    ))

    for c in raw:
        db.add(Candle(
            symbol=symbol, timeframe=timeframe,
            timestamp=c["time"], open=c["open"], high=c["high"],
            low=c["low"], close=c["close"], volume=c["volume"],
        ))
    await db.commit()
    return candles_to_df(raw)


async def get_candles_from_db(db: AsyncSession, symbol: str, timeframe: str) -> pd.DataFrame:
    result = await db.execute(
        select(Candle)
        .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
        .order_by(Candle.timestamp)
    )
    rows = result.scalars().all()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([{
        "timestamp": r.timestamp, "open": r.open, "high": r.high,
        "low": r.low, "close": r.close, "volume": r.volume,
    } for r in rows])


def candles_to_df(raw: list) -> pd.DataFrame:
    df = pd.DataFrame(raw)
    if df.empty:
        return df
    df = df.rename(columns={"time": "timestamp"})
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


async def get_symbols(db: AsyncSession) -> list:
    products = await delta_client.get_products()
    return [p["symbol"] for p in products if p.get("symbol")]
