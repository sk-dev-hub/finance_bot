# src/config/settings.py
import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv
from enum import Enum

# Загружаем переменные окружения
load_dotenv()


@dataclass
class PriceSources(str, Enum):
    COINGECKO = "coingecko"
    BINANCE = "binance"
    CBR = "cbr"  # Добавляем ЦБ РФ
    MANUAL = "manual"
    STATIC = "static"


@dataclass
class Settings:
    """Основная конфигурация приложения"""

    # Telegram
    BOT_TOKEN: str

    # Источники данных
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"

    BINANCE_API_URL: str = "https://api.binance.com/api/v3"
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")

    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
    COINGECKO_RATE_LIMIT = 30  # запросов в минуту

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
    RUB_EXCHANGE_RATE: float = 180.0  # Курс ЦБ + 1 рубль

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