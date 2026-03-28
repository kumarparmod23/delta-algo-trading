from typing import Dict

_ticker_cache: Dict[str, dict] = {}


def update_ticker(symbol: str, data: dict):
    _ticker_cache[symbol] = data


def get_ticker(symbol: str) -> dict:
    return _ticker_cache.get(symbol, {})


def get_all_tickers() -> dict:
    return dict(_ticker_cache)
