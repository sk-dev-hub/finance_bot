# src/assets/commodity.py
"""
Класс для товаров (коммодити).
"""

import logging
from typing import Optional
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig

logger = logging.getLogger(__name__)


class CommodityAsset(BaseAsset):
    """Класс для товаров"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)

        # Статические цены для товаров (можно расширить для динамических цен)
        self.static_prices = {
            "Приборы класик 24": 1250.0,
            "Приборы класик 16": 1150.0,
            "Приборы класик 24 зол": 1365.0,
            "Приборы Флора 24": 1250.0,
            "Анализатор": 100000.0,
            "Гитара 1007 SN": 120000.0,
        }

    async def get_price(self) -> Optional[AssetPrice]:
        """
        Получает цену товара.
        Для начала используем статические цены.
        """
        try:
            price = self.static_prices.get(self.symbol, 0)

            return AssetPrice(
                symbol=self.symbol,
                price=price,
                currency="RUB",
                source="static",
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting price for commodity {self.symbol}: {e}")
            return None

    def validate_amount(self, amount: float) -> bool:
        """Валидирует количество товара"""
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    def format_amount(self, amount: float) -> str:
        """Форматирует количество товара"""
        if amount.is_integer():
            return f"{amount:,.0f} шт"
        else:
            return f"{amount:,.2f} шт"

    def update_price(self, new_price: float):
        """Обновляет цену товара"""
        if self.symbol in self.static_prices:
            self.static_prices[self.symbol] = new_price
            logger.info(f"Updated price for {self.symbol} to ${new_price}")