"""BlackPanther God Mode - Configuration"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Clean, standardized settings for BlackPanther"""
    
    # ─────────────────────────────────────────────────────────
    # SYSTEM
    # ─────────────────────────────────────────────────────────
    MODE: str = Field(default="PAPER")
    LOG_LEVEL: str = Field(default="INFO")
    
    # ─────────────────────────────────────────────────────────
    # BINANCE
    # ─────────────────────────────────────────────────────────
    BINANCE_API_KEY: str = Field(default="")
    BINANCE_API_SECRET: str = Field(default="")
    BINANCE_FUTURES_API_KEY: str = Field(default="")
    BINANCE_FUTURES_API_SECRET: str = Field(default="")
    BINANCE_TESTNET: bool = Field(default=True)
    
    # ─────────────────────────────────────────────────────────
    # GATE.IO
    # ─────────────────────────────────────────────────────────
    GATEIO_API_KEY: str = Field(default="")
    GATEIO_API_SECRET: str = Field(default="")
    GATEIO_TESTNET: bool = Field(default=True)
    
    # ─────────────────────────────────────────────────────────
    # DATABASE & STATE
    # ─────────────────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379")
    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")
    SUPABASE_SERVICE_KEY: str = Field(default="")
    
    # ─────────────────────────────────────────────────────────
    # INTELLIGENCE
    # ─────────────────────────────────────────────────────────
    PERPLEXITY_API_KEY: str = Field(default="")
    
    # ─────────────────────────────────────────────────────────
    # ALERTS
    # ─────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")
    
    # ─────────────────────────────────────────────────────────
    # RISK MANAGEMENT
    # ─────────────────────────────────────────────────────────
    MAX_LEVERAGE: int = Field(default=5)
    MAX_DAILY_DRAWDOWN: float = Field(default=0.10)
    MAX_POSITION_SIZE: float = Field(default=0.05)
    
    # ─────────────────────────────────────────────────────────
    # STRATEGIES
    # ─────────────────────────────────────────────────────────
    CASH_COW_ENABLED: bool = Field(default=True)
    TREND_KILLER_ENABLED: bool = Field(default=True)
    SNIPER_ENABLED: bool = Field(default=True)
    
    class Config:
        env_file = [".env", "../.env"]
        extra = "ignore"


settings = Settings()

# Strategy-specific config
CONFIG = {
    "SYSTEM": {
        "MODE": settings.MODE,
        "LEVERAGE_LIMIT": settings.MAX_LEVERAGE,
        "MAX_DAILY_DRAWDOWN_PCT": settings.MAX_DAILY_DRAWDOWN
    },
    "STRATEGIES": {
        "CASH_COW": {
            "ENABLED": settings.CASH_COW_ENABLED,
            "ALLOCATION_PCT": 0.40,
            "MIN_FUNDING_RATE": 0.0001,
            "MAX_BASIS_RISK": 0.01
        },
        "TREND_KILLER": {
            "ENABLED": settings.TREND_KILLER_ENABLED,
            "ALLOCATION_PCT": 0.30,
            "TIMEFRAME": "15m",
            "SUPERTREND_LENGTH": 10,
            "SUPERTREND_MULT": 3.0,
            "OI_SURGE_THRESHOLD": 1.05,
            "CVD_CONFIRMATION_REQUIRED": True
        },
        "SNIPER": {
            "ENABLED": settings.SNIPER_ENABLED,
            "ALLOCATION_PCT": 0.30,
            "RVOL_THRESHOLD": 5.0,
            "PRICE_CHANGE_MAX": 0.05,
            "SENTIMENT_THRESHOLD": 70,
            "TRAILING_STOP_PCT": 0.05
        }
    }
}
