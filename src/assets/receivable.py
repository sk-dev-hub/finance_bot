# src/assets/receivable.py
"""
Класс для дебиторской задолженности.
"""

import logging
from typing import Optional
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig

logger = logging.getLogger(__name__)


class ReceivableAsset(BaseAsset):
    """Класс для дебиторской задолженности"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)

        # Коэффициент обесценивания (например, 1.0 = 100% стоимости)
        # Можно настроить в зависимости от срока задолженности
        self.discount_factor = {
            "receivable_ecm": 0.95,  # 95% от номинала
            "receivable_ozon": 0.98,  # 98% от номинала
        }

    async def get_price(self) -> Optional[AssetPrice]:
        """
        Получает цену дебиторской задолженности.
        Для задолженности цена всегда 1.0 (номинал),
        но можно применить коэффициент дисконтирования.
        """
        try:
            # Номинальная стоимость 1 единицы задолженности = 1 USD
            nominal_price = 1.0

            # Применяем коэффициент дисконтирования
            discount = self.discount_factor.get(self.symbol, 1.0)
            price = nominal_price * discount

            return AssetPrice(
                symbol=self.symbol,
                price=price,
                currency="USD",
                source="calculated",
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting price for receivable {self.symbol}: {e}")
            return None

    def validate_amount(self, amount: float) -> bool:
        """Валидирует сумму задолженности"""
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    def format_amount(self, amount: float) -> str:
        """Форматирует сумму задолженности"""
        return f"${amount:,.2f}"

    def format_value(self, amount: float, price: float) -> str:
        """Форматирует стоимость (для задолженности это та же сумма)"""
        value = amount * price
        return f"${value:,.2f} (номинал: ${amount:,.2f})"

    def update_discount_factor(self, new_factor: float):
        """Обновляет коэффициент дисконтирования"""
        if 0 <= new_factor <= 1.0:
            self.discount_factor[self.symbol] = new_factor
            logger.info(f"Updated discount factor for {self.symbol} to {new_factor}")