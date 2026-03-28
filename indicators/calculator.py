import pandas as pd
import numpy as np


def compute_sma(df: pd.DataFrame, period: int) -> pd.Series:
    return df["close"].rolling(period).mean()


def compute_ema(df: pd.DataFrame, period: int) -> pd.Series:
    return df["close"].ewm(span=period, adjust=False).mean()


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "macd_signal": signal_line, "macd_hist": histogram})


def compute_bbands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    mid = df["close"].rolling(period).mean()
    stddev = df["close"].rolling(period).std()
    return pd.DataFrame({"bb_upper": mid + std * stddev, "bb_mid": mid, "bb_lower": mid - std * stddev})


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).cumsum() / df["volume"].cumsum()


def compute_stochastic(df: pd.DataFrame, k_period=14, d_period=3) -> pd.DataFrame:
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return pd.DataFrame({"stoch_k": k, "stoch_d": d})


def compute_all(df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["sma20"]  = compute_sma(df, 20)
    df["sma50"]  = compute_sma(df, 50)
    df["sma200"] = compute_sma(df, 200)
    df["ema9"]   = compute_ema(df, 9)
    df["ema21"]  = compute_ema(df, 21)
    df["rsi14"]  = compute_rsi(df, 14)
    macd = compute_macd(df)
    df["macd"] = macd["macd"]
    df["macd_signal"] = macd["macd_signal"]
    df["macd_hist"]   = macd["macd_hist"]
    bb = compute_bbands(df)
    df["bb_upper"] = bb["bb_upper"]
    df["bb_mid"]   = bb["bb_mid"]
    df["bb_lower"] = bb["bb_lower"]
    df["atr14"]  = compute_atr(df, 14)
    df["vwap"]   = compute_vwap(df)
    stoch = compute_stochastic(df)
    df["stoch_k"] = stoch["stoch_k"]
    df["stoch_d"] = stoch["stoch_d"]
    return df
