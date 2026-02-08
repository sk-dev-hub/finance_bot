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
    CBR = "cbr"
    CBR_METALS = "cbr_metals"
    PRECIOUS_METAL = "precious_metal"
    MANUAL = "manual"
    STATIC = "static"


@dataclass
class ProductPrices:
    """Цены товаров в рублях"""
    # Приборы
    PRODUCT_1_PRICE: float = 1250.0  # Приборы класик 24
    PRODUCT_2_PRICE: float = 1150.0  # Приборы класик 16
    PRODUCT_3_PRICE: float = 1365.0  # Приборы класик 24 зол
    PRODUCT_4_PRICE: float = 1250.0  # Приборы Флора 24
    PRODUCT_5_PRICE: float = 100000.0  # Анализатор
    PRODUCT_6_PRICE: float = 120000.0  # Гитара 1007 SN


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
    RUB_EXCHANGE_RATE: float = 80.0  # Курс ЦБ + 1 рубль

    # Цены товаров (в рублях)
    PRODUCTS_PRICES: Dict[str, float] = None

    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.PRODUCTS_PRICES is None:
            self.PRODUCTS_PRICES = {
                "product_1": ProductPrices.PRODUCT_1_PRICE,
                "product_2": ProductPrices.PRODUCT_2_PRICE,
                "product_3": ProductPrices.PRODUCT_3_PRICE,
                "product_4": ProductPrices.PRODUCT_4_PRICE,
                "product_5": ProductPrices.PRODUCT_5_PRICE,
                "product_6": ProductPrices.PRODUCT_6_PRICE,
            }

    @classmethod
    def load(cls) -> 'Settings':
        """Загрузка конфигурации"""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен в .env файле")

        # Загружаем цены товаров из переменных окружения если они есть
        products_prices = {
            "product_1": float(os.getenv("PRODUCT_1_PRICE", ProductPrices.PRODUCT_1_PRICE)),
            "product_2": float(os.getenv("PRODUCT_2_PRICE", ProductPrices.PRODUCT_2_PRICE)),
            "product_3": float(os.getenv("PRODUCT_3_PRICE", ProductPrices.PRODUCT_3_PRICE)),
            "product_4": float(os.getenv("PRODUCT_4_PRICE", ProductPrices.PRODUCT_4_PRICE)),
            "product_5": float(os.getenv("PRODUCT_5_PRICE", ProductPrices.PRODUCT_5_PRICE)),
            "product_6": float(os.getenv("PRODUCT_6_PRICE", ProductPrices.PRODUCT_6_PRICE)),
        }

        return cls(
            BOT_TOKEN=bot_token,
            COINGECKO_API_URL=os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3"),
            CACHE_TTL=int(os.getenv("CACHE_TTL", "60")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            DATA_FILE=os.getenv("DATA_FILE", "data/user_data.json"),
            DEFAULT_CURRENCY=os.getenv("DEFAULT_CURRENCY", "USD"),
            UPDATE_INTERVAL=int(os.getenv("UPDATE_INTERVAL", "60")),
            RUB_EXCHANGE_RATE=float(os.getenv("RUB_EXCHANGE_RATE", "80.0")),
            PRODUCTS_PRICES=products_prices
        )


# Глобальный объект конфигурации
settings = Settings.load()