from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class Candle(Base):
    __tablename__ = "candles"
    id        = Column(Integer, primary_key=True)
    symbol    = Column(String, index=True)
    timeframe = Column(String)
    timestamp = Column(Integer, index=True)
    open      = Column(Float)
    high      = Column(Float)
    low       = Column(Float)
    close     = Column(Float)
    volume    = Column(Float)


class Strategy(Base):
    __tablename__ = "strategies"
    id               = Column(Integer, primary_key=True)
    name             = Column(String)
    symbol           = Column(String)
    timeframe        = Column(String)
    conditions_json  = Column(Text)   # JSON string
    risk_json        = Column(Text)   # JSON string
    mode             = Column(String, default="paper")  # paper | live
    active           = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    trades           = relationship("Trade", back_populates="strategy")


class Trade(Base):
    __tablename__ = "trades"
    id           = Column(Integer, primary_key=True)
    strategy_id  = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    symbol       = Column(String)
    side         = Column(String)        # buy | sell
    qty          = Column(Float)
    entry_price  = Column(Float)
    exit_price   = Column(Float, nullable=True)
    pnl          = Column(Float, nullable=True)
    mode         = Column(String)        # paper | live
    status       = Column(String, default="open")   # open | closed
    entry_time   = Column(DateTime, default=datetime.utcnow)
    exit_time    = Column(DateTime, nullable=True)
    strategy     = relationship("Strategy", back_populates="trades")


class PaperBalance(Base):
    __tablename__ = "paper_balance"
    id        = Column(Integer, primary_key=True)
    currency  = Column(String, default="USD")
    available = Column(Float)
    locked    = Column(Float, default=0.0)


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    id          = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol      = Column(String)
    timeframe   = Column(String)
    start_date  = Column(String)
    end_date    = Column(String)
    params_json = Column(Text)
    metrics_json     = Column(Text)
    equity_curve_json = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id             = Column(Integer, primary_key=True)
    name           = Column(String)
    symbol         = Column(String)
    condition_type = Column(String)   # price_above | price_below | indicator | pattern
    threshold      = Column(Float, nullable=True)
    indicator_json = Column(Text, nullable=True)
    active         = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)


class AlertHistory(Base):
    __tablename__ = "alert_history"
    id           = Column(Integer, primary_key=True)
    alert_id     = Column(Integer, ForeignKey("alerts.id"))
    triggered_at = Column(DateTime, default=datetime.utcnow)
    trigger_value = Column(Float, nullable=True)
    message      = Column(String)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    id             = Column(Integer, primary_key=True)
    timestamp      = Column(DateTime, default=datetime.utcnow)
    total_value    = Column(Float)
    realized_pnl   = Column(Float)
    unrealized_pnl = Column(Float)
    mode           = Column(String)
