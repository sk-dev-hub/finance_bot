# src/config/settings.py
import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


@dataclass
class PriceSources:
    """Источники данных для цен"""
    COINGECKO = "coingecko"
    BINANCE = "binance"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"


@dataclass
class Settings:
    """Основная конфигурация приложения"""

    # Telegram
    BOT_TOKEN: str

    # Источники данных
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    BINANCE_API_URL: str = "https://api.binance.com/api/v3"

    # Кэширование
    CACHE_TTL: int = 60
    REDIS_URL: str = ""

    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"

    # База данных
    DATA_FILE: str = "data/user_data.json"

    # Настройки приложения
    DEFAULT_CURRENCY: str = "USD"
    UPDATE_INTERVAL: int = 600  # секунды

    # Курс ЦБ  + 1 рубль
    RUB_EXCHANGE_RATE: float = 80.0  # Курс ЦБ + 1 рубль

    @classmethod
    def load(cls) -> 'Settings':
        """Загрузка конфигурации"""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен в .env файле")

        return cls(
            BOT_TOKEN=bot_token,
            COINGECKO_API_URL=os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3"),
            CACHE_TTL=int(os.getenv("CACHE_TTL", "60")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            DATA_FILE=os.getenv("DATA_FILE", "data/user_data.json"),
            DEFAULT_CURRENCY=os.getenv("DEFAULT_CURRENCY", "USD"),
            UPDATE_INTERVAL=int(os.getenv("UPDATE_INTERVAL", "60"))
        )


# Глобальный объект конфигурации
settings = Settings.load()