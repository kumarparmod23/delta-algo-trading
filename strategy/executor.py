import asyncio
from strategy.registry import get_all
from strategy.builder import evaluate_strategy
from data.market_data import fetch_and_store_candles
from core.database import AsyncSessionLocal


async def run_all_strategies():
    strategies = get_all()
    if not strategies:
        return
    async with AsyncSessionLocal() as db:
        for sid, strat in strategies.items():
            try:
                df = await fetch_and_store_candles(db, strat["symbol"], strat["timeframe"], limit=100)
                if df.empty:
                    continue
                signals = evaluate_strategy(df, strat["conditions_json"])
                if signals["entry_long"] or signals["entry_short"] or signals["exit"]:
                    from api.websocket import manager
                    await manager.broadcast({
                        "type": "strategy_signal",
                        "strategy_id": sid,
                        "strategy_name": strat["name"],
                        "symbol": strat["symbol"],
                        "signals": signals,
                    })
                    if strat.get("mode") == "paper":
                        from trading.order_manager import OrderManager
                        om = OrderManager(mode="paper")
                        if signals["entry_long"]:
                            await om.place_order(strat["symbol"], "buy",
                                                 strat.get("qty", 1), strategy_id=sid)
                        elif signals["entry_short"]:
                            await om.place_order(strat["symbol"], "sell",
                                                 strat.get("qty", 1), strategy_id=sid)
            except Exception as e:
                print(f"[Executor] Strategy {sid} error: {e}")
