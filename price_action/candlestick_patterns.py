import pandas as pd
import numpy as np


def _body(df): return (df["close"] - df["open"]).abs()
def _upper_wick(df): return df["high"] - df[["open", "close"]].max(axis=1)
def _lower_wick(df): return df[["open", "close"]].min(axis=1) - df["low"]
def _is_bull(df): return df["close"] > df["open"]
def _is_bear(df): return df["close"] < df["open"]


def detect_doji(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    candle_range = df["high"] - df["low"]
    return (body <= candle_range * 0.1) & (candle_range > 0)


def detect_hammer(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    lower = _lower_wick(df)
    upper = _upper_wick(df)
    return (lower >= body * 2) & (upper <= body * 0.3) & (body > 0)


def detect_shooting_star(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    upper = _upper_wick(df)
    lower = _lower_wick(df)
    return (upper >= body * 2) & (lower <= body * 0.3) & (body > 0)


def detect_bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    prev_bear = _is_bear(df.shift(1))
    curr_bull = _is_bull(df)
    engulfs = (df["open"] < df.shift(1)["close"]) & (df["close"] > df.shift(1)["open"])
    return prev_bear & curr_bull & engulfs


def detect_bearish_engulfing(df: pd.DataFrame) -> pd.Series:
    prev_bull = _is_bull(df.shift(1))
    curr_bear = _is_bear(df)
    engulfs = (df["open"] > df.shift(1)["close"]) & (df["close"] < df.shift(1)["open"])
    return prev_bull & curr_bear & engulfs


def detect_pin_bar_bull(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    lower = _lower_wick(df)
    upper = _upper_wick(df)
    candle_range = df["high"] - df["low"]
    return (lower >= candle_range * 0.6) & (body <= candle_range * 0.3) & (upper <= candle_range * 0.1)


def detect_pin_bar_bear(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    upper = _upper_wick(df)
    lower = _lower_wick(df)
    candle_range = df["high"] - df["low"]
    return (upper >= candle_range * 0.6) & (body <= candle_range * 0.3) & (lower <= candle_range * 0.1)


def detect_morning_star(df: pd.DataFrame) -> pd.Series:
    c1_bear = _is_bear(df.shift(2))
    c2_small = _body(df.shift(1)) < _body(df.shift(2)) * 0.3
    c3_bull = _is_bull(df)
    c3_closes_above = df["close"] > (df.shift(2)["open"] + df.shift(2)["close"]) / 2
    return c1_bear & c2_small & c3_bull & c3_closes_above


def detect_evening_star(df: pd.DataFrame) -> pd.Series:
    c1_bull = _is_bull(df.shift(2))
    c2_small = _body(df.shift(1)) < _body(df.shift(2)) * 0.3
    c3_bear = _is_bear(df)
    c3_closes_below = df["close"] < (df.shift(2)["open"] + df.shift(2)["close"]) / 2
    return c1_bull & c2_small & c3_bear & c3_closes_below


def detect_inside_bar(df: pd.DataFrame) -> pd.Series:
    return (df["high"] < df.shift(1)["high"]) & (df["low"] > df.shift(1)["low"])


def detect_marubozu_bull(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    candle_range = df["high"] - df["low"]
    return _is_bull(df) & (body >= candle_range * 0.9)


def detect_marubozu_bear(df: pd.DataFrame) -> pd.Series:
    body = _body(df)
    candle_range = df["high"] - df["low"]
    return _is_bear(df) & (body >= candle_range * 0.9)


def detect_tweezer_top(df: pd.DataFrame) -> pd.Series:
    same_high = (df["high"] - df.shift(1)["high"]).abs() < df["high"] * 0.001
    return _is_bull(df.shift(1)) & _is_bear(df) & same_high


def detect_tweezer_bottom(df: pd.DataFrame) -> pd.Series:
    same_low = (df["low"] - df.shift(1)["low"]).abs() < df["low"] * 0.001
    return _is_bear(df.shift(1)) & _is_bull(df) & same_low


def detect_all(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["doji"]              = detect_doji(df)
    out["hammer"]            = detect_hammer(df)
    out["shooting_star"]     = detect_shooting_star(df)
    out["bullish_engulfing"] = detect_bullish_engulfing(df)
    out["bearish_engulfing"] = detect_bearish_engulfing(df)
    out["pin_bar_bull"]      = detect_pin_bar_bull(df)
    out["pin_bar_bear"]      = detect_pin_bar_bear(df)
    out["morning_star"]      = detect_morning_star(df)
    out["evening_star"]      = detect_evening_star(df)
    out["inside_bar"]        = detect_inside_bar(df)
    out["marubozu_bull"]     = detect_marubozu_bull(df)
    out["marubozu_bear"]     = detect_marubozu_bear(df)
    out["tweezer_top"]       = detect_tweezer_top(df)
    out["tweezer_bottom"]    = detect_tweezer_bottom(df)
    return out
