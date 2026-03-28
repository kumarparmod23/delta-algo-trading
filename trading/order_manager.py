from data.ticker import get_ticker
from trading.paper_trader import place_paper_order
from trading.live_trader import place_live_order
from risk.manager import compute_sl_tp


class OrderManager:
    def __init__(self, mode: str = "paper"):
        self.mode = mode

    async def place_order(self, symbol: str, side: str, qty: float,
                          risk_config: dict = None, strategy_id: int = None) -> dict:
        ticker = get_ticker(symbol)
        price = float(ticker.get("close", ticker.get("mark_price", 0)))
        if price <= 0:
            return {"error": f"No price available for {symbol}"}

        sl_tp = compute_sl_tp(price, side, risk_config or {}) if risk_config else {}

        if self.mode == "paper":
            return await place_paper_order(
                symbol=symbol, side=side, qty=qty, price=price,
                stop_loss=sl_tp.get("stop_loss"), take_profit=sl_tp.get("take_profit"),
                strategy_id=strategy_id,
            )
        else:
            return await place_live_order(symbol=symbol, side=side, qty=qty)
