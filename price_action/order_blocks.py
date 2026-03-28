import pandas as pd
from typing import List


def find_order_blocks(df: pd.DataFrame, lookback: int = 50) -> List[dict]:
    """
    Institutional order blocks: last bearish candle before a bullish impulse (demand)
    and last bullish candle before a bearish impulse (supply).
    """
    blocks = []
    data = df.tail(lookback).reset_index(drop=True)
    for i in range(2, len(data) - 1):
        c = data.iloc[i]
        nxt = data.iloc[i + 1]
        # Demand block: bearish candle followed by strong bullish move
        if c["close"] < c["open"]:
            if nxt["close"] > c["high"] * 1.002:
                blocks.append({
                    "type": "demand",
                    "top": c["open"],
                    "bottom": c["close"],
                    "timestamp": c["timestamp"],
                    "strength": (nxt["close"] - c["high"]) / c["high"] * 100,
                })
        # Supply block: bullish candle followed by strong bearish move
        if c["close"] > c["open"]:
            if nxt["close"] < c["low"] * 0.998:
                blocks.append({
                    "type": "supply",
                    "top": c["close"],
                    "bottom": c["open"],
                    "timestamp": c["timestamp"],
                    "strength": (c["low"] - nxt["close"]) / c["low"] * 100,
                })
    return blocks


def find_fvg(df: pd.DataFrame) -> List[dict]:
    """Fair Value Gaps — 3-candle imbalance zones."""
    gaps = []
    for i in range(2, len(df)):
        c1 = df.iloc[i - 2]
        c3 = df.iloc[i]
        # Bullish FVG: c3 low > c1 high
        if c3["low"] > c1["high"]:
            gaps.append({
                "type": "bullish_fvg",
                "top": c3["low"],
                "bottom": c1["high"],
                "timestamp": df.iloc[i - 1]["timestamp"],
            })
        # Bearish FVG: c3 high < c1 low
        if c3["high"] < c1["low"]:
            gaps.append({
                "type": "bearish_fvg",
                "top": c1["low"],
                "bottom": c3["high"],
                "timestamp": df.iloc[i - 1]["timestamp"],
            })
    return gaps[-10:]


def price_in_demand_zone(df: pd.DataFrame) -> bool:
    blocks = find_order_blocks(df)
    current = df["close"].iloc[-1]
    for b in blocks:
        if b["type"] == "demand" and b["bottom"] <= current <= b["top"]:
            return True
    return False


def price_in_supply_zone(df: pd.DataFrame) -> bool:
    blocks = find_order_blocks(df)
    current = df["close"].iloc[-1]
    for b in blocks:
        if b["type"] == "supply" and b["bottom"] <= current <= b["top"]:
            return True
    return False
