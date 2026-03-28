import pandas as pd
import numpy as np


def detect_swing_points(df: pd.DataFrame, window: int = 5):
    swing_highs, swing_lows = [], []
    for i in range(window, len(df) - window):
        if df["high"].iloc[i] == df["high"].iloc[i - window: i + window + 1].max():
            swing_highs.append((i, df["high"].iloc[i]))
        if df["low"].iloc[i] == df["low"].iloc[i - window: i + window + 1].min():
            swing_lows.append((i, df["low"].iloc[i]))
    return swing_highs, swing_lows


def detect_trend(df: pd.DataFrame, window: int = 5) -> str:
    if len(df) < window * 3:
        return "neutral"
    sh, sl = detect_swing_points(df, window)
    if len(sh) < 2 or len(sl) < 2:
        return "neutral"
    hh = sh[-1][1] > sh[-2][1]
    hl = sl[-1][1] > sl[-2][1]
    lh = sh[-1][1] < sh[-2][1]
    ll = sl[-1][1] < sl[-2][1]
    if hh and hl:
        return "uptrend"
    if lh and ll:
        return "downtrend"
    return "neutral"


def detect_bos(df: pd.DataFrame, window: int = 5) -> dict:
    """Break of Structure detection."""
    sh, sl = detect_swing_points(df, window)
    result = {"bos_bullish": False, "bos_bearish": False}
    if len(sh) >= 2:
        last_high = sh[-2][1]
        if df["close"].iloc[-1] > last_high:
            result["bos_bullish"] = True
    if len(sl) >= 2:
        last_low = sl[-2][1]
        if df["close"].iloc[-1] < last_low:
            result["bos_bearish"] = True
    return result


def detect_choch(df: pd.DataFrame, window: int = 5) -> dict:
    """Change of Character — early reversal signal."""
    trend = detect_trend(df.iloc[:-10], window)
    bos   = detect_bos(df, window)
    result = {"choch_bullish": False, "choch_bearish": False}
    if trend == "downtrend" and bos["bos_bullish"]:
        result["choch_bullish"] = True
    if trend == "uptrend" and bos["bos_bearish"]:
        result["choch_bearish"] = True
    return result


def get_market_structure(df: pd.DataFrame) -> dict:
    trend = detect_trend(df)
    bos   = detect_bos(df)
    choch = detect_choch(df)
    return {"trend": trend, **bos, **choch}
