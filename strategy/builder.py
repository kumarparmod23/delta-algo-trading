import json
import pandas as pd
from indicators.calculator import compute_all
from price_action.candlestick_patterns import detect_all as detect_patterns
from price_action.support_resistance import price_at_support, price_at_resistance
from price_action.trend_structure import get_market_structure
from price_action.order_blocks import price_in_demand_zone, price_in_supply_zone
from price_action.breakout_detector import detect_breakout


INDICATOR_MAP = {
    "rsi": "rsi14", "macd": "macd", "macd_signal": "macd_signal",
    "macd_hist": "macd_hist", "bb_upper": "bb_upper", "bb_lower": "bb_lower",
    "bb_mid": "bb_mid", "sma20": "sma20", "sma50": "sma50", "sma200": "sma200",
    "ema9": "ema9", "ema21": "ema21", "atr": "atr14", "vwap": "vwap",
    "stoch_k": "stoch_k", "stoch_d": "stoch_d",
}


def evaluate_condition(df: pd.DataFrame, condition: dict) -> bool:
    ctype = condition.get("type", "indicator")

    if ctype == "indicator":
        indicator = condition["indicator"].lower()
        operator  = condition["operator"]
        value     = condition.get("value")
        col = INDICATOR_MAP.get(indicator, indicator)
        if col not in df.columns:
            return False
        current = df[col].iloc[-1]
        prev    = df[col].iloc[-2] if len(df) > 1 else current

        if operator == "greater_than":    return current > value
        if operator == "less_than":       return current < value
        if operator == "crosses_above":   return prev < value <= current
        if operator == "crosses_below":   return prev > value >= current
        if operator == "price_above":     return df["close"].iloc[-1] > current
        if operator == "price_below":     return df["close"].iloc[-1] < current

    elif ctype == "price_action":
        pattern = condition["pattern"]
        df_pat  = detect_patterns(df)
        ms      = get_market_structure(df)
        bo      = detect_breakout(df)

        if pattern == "bullish_engulfing":  return bool(df_pat["bullish_engulfing"].iloc[-1])
        if pattern == "bearish_engulfing":  return bool(df_pat["bearish_engulfing"].iloc[-1])
        if pattern == "hammer":             return bool(df_pat["hammer"].iloc[-1])
        if pattern == "shooting_star":      return bool(df_pat["shooting_star"].iloc[-1])
        if pattern == "pin_bar_bull":       return bool(df_pat["pin_bar_bull"].iloc[-1])
        if pattern == "pin_bar_bear":       return bool(df_pat["pin_bar_bear"].iloc[-1])
        if pattern == "doji":               return bool(df_pat["doji"].iloc[-1])
        if pattern == "morning_star":       return bool(df_pat["morning_star"].iloc[-1])
        if pattern == "evening_star":       return bool(df_pat["evening_star"].iloc[-1])
        if pattern == "inside_bar":         return bool(df_pat["inside_bar"].iloc[-1])
        if pattern == "marubozu_bull":      return bool(df_pat["marubozu_bull"].iloc[-1])
        if pattern == "marubozu_bear":      return bool(df_pat["marubozu_bear"].iloc[-1])
        if pattern == "tweezer_top":        return bool(df_pat["tweezer_top"].iloc[-1])
        if pattern == "tweezer_bottom":     return bool(df_pat["tweezer_bottom"].iloc[-1])
        if pattern == "at_support":         return price_at_support(df)
        if pattern == "at_resistance":      return price_at_resistance(df)
        if pattern == "uptrend":            return ms["trend"] == "uptrend"
        if pattern == "downtrend":          return ms["trend"] == "downtrend"
        if pattern == "bos_bullish":        return ms["bos_bullish"]
        if pattern == "bos_bearish":        return ms["bos_bearish"]
        if pattern == "choch_bullish":      return ms["choch_bullish"]
        if pattern == "choch_bearish":      return ms["choch_bearish"]
        if pattern == "in_demand_zone":     return price_in_demand_zone(df)
        if pattern == "in_supply_zone":     return price_in_supply_zone(df)
        if pattern == "breakout_up":        return bo["breakout_up"]
        if pattern == "breakout_down":      return bo["breakout_down"]

    return False


def evaluate_strategy(df: pd.DataFrame, conditions_json: str) -> dict:
    if df.empty or len(df) < 30:
        return {"entry_long": False, "entry_short": False, "exit": False}

    df = compute_all(df)
    conditions = json.loads(conditions_json)

    entry_long_conds  = conditions.get("entry_long", [])
    entry_short_conds = conditions.get("entry_short", [])
    exit_conds        = conditions.get("exit", [])

    entry_long  = all(evaluate_condition(df, c) for c in entry_long_conds)  if entry_long_conds  else False
    entry_short = all(evaluate_condition(df, c) for c in entry_short_conds) if entry_short_conds else False
    exit_signal = all(evaluate_condition(df, c) for c in exit_conds)        if exit_conds        else False

    return {"entry_long": entry_long, "entry_short": entry_short, "exit": exit_signal}
