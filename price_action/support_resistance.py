import pandas as pd
import numpy as np
from typing import List, Tuple


def find_pivots(df: pd.DataFrame, left: int = 5, right: int = 5) -> Tuple[List[float], List[float]]:
    highs, lows = [], []
    for i in range(left, len(df) - right):
        window_h = df["high"].iloc[i - left: i + right + 1]
        window_l = df["low"].iloc[i - left: i + right + 1]
        if df["high"].iloc[i] == window_h.max():
            highs.append(df["high"].iloc[i])
        if df["low"].iloc[i] == window_l.min():
            lows.append(df["low"].iloc[i])
    return highs, lows


def cluster_levels(levels: List[float], tolerance_pct: float = 0.003) -> List[float]:
    if not levels:
        return []
    levels = sorted(levels)
    clusters = [[levels[0]]]
    for lvl in levels[1:]:
        if abs(lvl - clusters[-1][-1]) / clusters[-1][-1] < tolerance_pct:
            clusters[-1].append(lvl)
        else:
            clusters.append([lvl])
    return [sum(c) / len(c) for c in clusters]


def get_sr_levels(df: pd.DataFrame, n: int = 8) -> dict:
    highs, lows = find_pivots(df)
    resistance = sorted(cluster_levels(highs), reverse=True)[:n]
    support    = sorted(cluster_levels(lows))[:n]
    current    = df["close"].iloc[-1]
    nearest_res = min((r for r in resistance if r > current), default=None)
    nearest_sup = max((s for s in support if s < current), default=None)
    return {
        "resistance": resistance,
        "support": support,
        "nearest_resistance": nearest_res,
        "nearest_support": nearest_sup,
        "current_price": current,
    }


def price_at_support(df: pd.DataFrame, tolerance_pct: float = 0.005) -> bool:
    levels = get_sr_levels(df)
    sup = levels["nearest_support"]
    if sup is None:
        return False
    current = df["close"].iloc[-1]
    return abs(current - sup) / sup < tolerance_pct


def price_at_resistance(df: pd.DataFrame, tolerance_pct: float = 0.005) -> bool:
    levels = get_sr_levels(df)
    res = levels["nearest_resistance"]
    if res is None:
        return False
    current = df["close"].iloc[-1]
    return abs(current - res) / res < tolerance_pct
