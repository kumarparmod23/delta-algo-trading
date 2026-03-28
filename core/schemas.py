from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class CandleOut(BaseModel):
    symbol: str
    timeframe: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class StrategyCreate(BaseModel):
    name: str
    symbol: str
    timeframe: str
    conditions_json: str
    risk_json: str
    mode: str = "paper"


class StrategyOut(BaseModel):
    id: int
    name: str
    symbol: str
    timeframe: str
    conditions_json: str
    risk_json: str
    mode: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TradeOut(BaseModel):
    id: int
    strategy_id: Optional[int]
    symbol: str
    side: str
    qty: float
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    mode: str
    status: str
    entry_time: datetime
    exit_time: Optional[datetime]

    class Config:
        from_attributes = True


class BacktestRequest(BaseModel):
    strategy_id: int
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0


class BacktestResultOut(BaseModel):
    id: int
    strategy_id: int
    symbol: str
    metrics_json: str
    equity_curve_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    name: str
    symbol: str
    condition_type: str
    threshold: Optional[float] = None
    indicator_json: Optional[str] = None


class AlertOut(BaseModel):
    id: int
    name: str
    symbol: str
    condition_type: str
    threshold: Optional[float]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrderRequest(BaseModel):
    symbol: str
    side: str
    qty: float
    order_type: str = "market"
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
