import pandas as pd
from price_action.support_resistance import get_sr_levels


def detect_breakout(df: pd.DataFrame, volume_confirm: bool = True) -> dict:
    levels = get_sr_levels(df)
    current = df["close"].iloc[-1]
    prev    = df["close"].iloc[-2]
    avg_vol = df["volume"].rolling(20).mean().iloc[-1]
    curr_vol = df["volume"].iloc[-1]
    vol_ok  = (curr_vol > avg_vol * 1.2) if volume_confirm else True

    result = {"breakout_up": False, "breakout_down": False, "level": None}
    res = levels["nearest_resistance"]
    sup = levels["nearest_support"]

    if res and prev < res and current > res and vol_ok:
        result["breakout_up"] = True
        result["level"] = res
    if sup and prev > sup and current < sup and vol_ok:
        result["breakout_down"] = True
        result["level"] = sup
    return result


def detect_consolidation(df: pd.DataFrame, period: int = 20, threshold: float = 0.02) -> bool:
    recent = df.tail(period)
    price_range = (recent["high"].max() - recent["low"].min()) / recent["close"].mean()
    return price_range < threshold
