from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from data.market_data import fetch_and_store_candles, get_symbols
from data.ticker import get_all_tickers, get_ticker
from exchange.delta_client import delta_client
from indicators.calculator import compute_all
from price_action.candlestick_patterns import detect_all as detect_patterns
from price_action.support_resistance import get_sr_levels
from price_action.trend_structure import get_market_structure
from price_action.order_blocks import find_order_blocks, find_fvg

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/symbols")
async def symbols(db: AsyncSession = Depends(get_db)):
    return await get_symbols(db)


@router.get("/candles/{symbol}")
async def candles(symbol: str, timeframe: str = "15m", limit: int = 200,
                  indicators: bool = True, price_action: bool = True,
                  db: AsyncSession = Depends(get_db)):
    df = await fetch_and_store_candles(db, symbol, timeframe, limit)
    if df.empty:
        return []
    if indicators:
        df = compute_all(df)
    if price_action:
        df = detect_patterns(df)

    df = df.fillna(0)
    return df.to_dict(orient="records")


@router.get("/ticker/{symbol}")
async def ticker(symbol: str):
    return get_ticker(symbol) or await delta_client.get_ticker(symbol)


@router.get("/tickers")
async def tickers():
    cached = get_all_tickers()
    if cached:
        return cached
    return await delta_client.get_tickers()


@router.get("/orderbook/{symbol}")
async def orderbook(symbol: str, depth: int = 10):
    return await delta_client.get_orderbook(symbol, depth)


@router.get("/analysis/{symbol}")
async def full_analysis(symbol: str, timeframe: str = "1h",
                        db: AsyncSession = Depends(get_db)):
    df = await fetch_and_store_candles(db, symbol, timeframe, 200)
    if df.empty:
        return {"error": "No data"}
    df = compute_all(df)
    sr   = get_sr_levels(df)
    ms   = get_market_structure(df)
    obs  = find_order_blocks(df)
    fvgs = find_fvg(df)
    return {
        "symbol": symbol, "timeframe": timeframe,
        "price": df["close"].iloc[-1],
        "indicators": {
            "rsi14": round(df["rsi14"].iloc[-1], 2),
            "macd":  round(df["macd"].iloc[-1], 4),
            "macd_signal": round(df["macd_signal"].iloc[-1], 4),
            "macd_hist":   round(df["macd_hist"].iloc[-1], 4),
            "bb_upper": round(df["bb_upper"].iloc[-1], 4),
            "bb_lower": round(df["bb_lower"].iloc[-1], 4),
            "sma20": round(df["sma20"].iloc[-1], 4),
            "ema9":  round(df["ema9"].iloc[-1], 4),
            "atr14": round(df["atr14"].iloc[-1], 4),
        },
        "market_structure": ms,
        "support_resistance": sr,
        "order_blocks": obs[:5],
        "fair_value_gaps": fvgs[:5],
    }
