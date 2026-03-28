from exchange.delta_client import delta_client
from config import settings


async def place_live_order(symbol: str, side: str, qty: float,
                           order_type: str = "market_order",
                           limit_price: float = None) -> dict:
    if not settings.live_trading_enabled:
        return {"error": "Live trading is disabled. Set LIVE_TRADING_ENABLED=true in .env"}
    return await delta_client.place_order(symbol, side, qty, order_type, limit_price)


async def cancel_live_order(order_id: int, product_id: int) -> dict:
    if not settings.live_trading_enabled:
        return {"error": "Live trading is disabled"}
    return await delta_client.cancel_order(order_id, product_id)


async def get_live_positions() -> list:
    return await delta_client.get_positions()


async def get_live_balance() -> list:
    return await delta_client.get_wallet_balance()
