# src/assets/commodity.py
"""Класс для товаров (коммодити)."""

import logging
from typing import Optional
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig
from src.config.settings import settings  # Импортируем settings

logger = logging.getLogger(__name__)


class CommodityAsset(BaseAsset):
    """Класс для товаров"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)

    async def get_price(self) -> Optional[AssetPrice]:
        """
        Получает цену товара из настроек.
        """
        try:
            # Получаем цену в рублях из настроек
            price_rub = settings.PRODUCTS_PRICES.get(self.symbol, 0)

            # Конвертируем в USD через currency_service
            from src.services.currency_service import currency_service
            price_usd = None
            if price_rub > 0:
                usd_to_rub_rate = currency_service.get_real_usd_rub_rate_sync()
                if usd_to_rub_rate > 0:
                    price_usd = price_rub / usd_to_rub_rate

            return AssetPrice(
                symbol=self.symbol,
                price=price_usd if price_usd else 0,  # Возвращаем в USD
                currency="USD",
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
        # Обновляем цену в настройках
        if self.symbol in settings.PRODUCTS_PRICES:
            settings.PRODUCTS_PRICES[self.symbol] = new_price
            logger.info(f"Updated price for {self.symbol} to {new_price} ₽")