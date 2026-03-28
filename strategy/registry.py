from typing import Dict

_active_strategies: Dict[int, dict] = {}


def register(strategy_id: int, strategy: dict):
    _active_strategies[strategy_id] = strategy


def unregister(strategy_id: int):
    _active_strategies.pop(strategy_id, None)


def get_all() -> Dict[int, dict]:
    return dict(_active_strategies)


def get(strategy_id: int) -> dict:
    return _active_strategies.get(strategy_id)
