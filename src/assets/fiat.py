# src/assets/fiat.py
"""
Класс для фиатных валют (наличных денег).
"""

import logging
from typing import Optional
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig
from src.config.settings import settings

logger = logging.getLogger(__name__)


class FiatAsset(BaseAsset):
    """Класс для фиатных валют"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)
        self._exchange_rate = config.exchange_rate
        self._base_currency = config.base_currency

    async def get_price(self) -> Optional[AssetPrice]:
        """
        Получает цену фиатной валюты.
        Для фиатных валют цена - это курс к базовой валюте (обычно USD).
        """
        try:
            # Для фиатных валют возвращаем курс к USD
            # Можно добавить получение реального курса с API
            if self.symbol.upper() == "USD":
                price = 1.0  # USD к USD всегда 1
            else:
                # Используем статический курс из конфигурации
                price = self._exchange_rate

            return AssetPrice(
                symbol=self.symbol,
                price=price,
                currency=self._base_currency,
                source="static",
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting price for fiat {self.symbol}: {e}")
            return None

    def validate_amount(self, amount: float) -> bool:
        """Валидирует количество фиатной валюты"""
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    def format_amount(self, amount: float) -> str:
        """Форматирует количество фиатной валюты"""
        if self.symbol in ["rub", "cny", "kzt", "uah"]:
            # Для целых валют
            return f"{amount:,.0f}"
        else:
            # Для валют с дробными значениями
            return f"{amount:,.2f}"

    def format_value(self, amount: float, price: float) -> str:
        """Форматирует стоимость в базовой валюте"""
        value = amount * price

        if self._base_currency == "USD":
            return f"${value:,.2f}"
        elif self._base_currency == "EUR":
            return f"€{value:,.2f}"
        else:
            return f"{value:,.2f} {self._base_currency}"

    def get_exchange_rate(self, target_currency: str = "USD") -> float:
        """Возвращает курс к целевой валюте"""
        if target_currency.upper() == self._base_currency.upper():
            return self._exchange_rate
        else:
            # Здесь можно добавить логику конвертации через API
            logger.warning(f"Conversion from {self.symbol} to {target_currency} not implemented")
            return self._exchange_rate