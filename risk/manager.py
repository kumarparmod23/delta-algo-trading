def validate_order(symbol: str, side: str, qty: float, price: float,
                   balance: float, risk_config: dict) -> dict:
    max_pct = risk_config.get("position_size_pct", 10.0) / 100
    max_value = balance * max_pct
    order_value = qty * price

    if order_value > max_value:
        safe_qty = max_value / price
        return {"valid": False, "reason": f"Position too large. Max qty: {safe_qty:.4f}", "safe_qty": safe_qty}
    return {"valid": True}


def compute_sl_tp(price: float, side: str, risk_config: dict) -> dict:
    sl_pct = risk_config.get("stop_loss_pct", 2.0) / 100
    tp_pct = risk_config.get("take_profit_pct", 4.0) / 100
    if side == "buy":
        return {"stop_loss": round(price * (1 - sl_pct), 6), "take_profit": round(price * (1 + tp_pct), 6)}
    else:
        return {"stop_loss": round(price * (1 + sl_pct), 6), "take_profit": round(price * (1 - tp_pct), 6)}


def check_sl_tp(position: dict, current_price: float) -> str:
    side = position["side"]
    sl   = position.get("stop_loss")
    tp   = position.get("take_profit")
    if side == "buy":
        if sl and current_price <= sl: return "stop_loss"
        if tp and current_price >= tp: return "take_profit"
    else:
        if sl and current_price >= sl: return "stop_loss"
        if tp and current_price <= tp: return "take_profit"
    return "none"
