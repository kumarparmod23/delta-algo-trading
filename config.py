from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    delta_api_key: str = ""
    delta_api_secret: str = ""
    delta_base_url: str = "https://api.india.delta.exchange"
    delta_ws_url: str = "wss://socket.india.delta.exchange"

    live_trading_enabled: bool = False
    paper_initial_balance: float = 100000.0
    db_path: str = "./trading.db"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_auth_enabled: bool = False
    api_tokens: str = ""
    api_admin_tokens: str = ""
    market_symbols: str = "BTCUSD,ETHUSD,SOLUSD"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
