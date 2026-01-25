# src/assets/precious_metal.py
"""
Класс для драгоценных металлов (золотые и серебряные монеты).
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig
from src.config.settings import settings

logger = logging.getLogger(__name__)


class PreciousMetalAsset(BaseAsset):
    """Класс для драгоценных металлов"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)

        # Вес монет в граммах
        self.weights = {
            "gold_coin_7_78": 7.78,  # 1/4 тройской унции
            "gold_coin_15_55": 15.55,  # 1/2 тройской унции
            "silver_coin_31_1": 31.1,  # 1 тройская унция
        }

        # Чистота металла (проба)
        self.purities = {
            "gold_coin_7_78": 0.9999,  # 9999 проба
            "gold_coin_15_55": 0.9999,  # 9999 проба
            "silver_coin_31_1": 0.999,  # 999 проба
        }

        # Текущие цены на металлы (USD за грамм)
        # Эти значения можно получать из API
        self.metal_prices = {
            "gold": 65.0,  # USD за грамм золота (примерно)
            "silver": 0.85,  # USD за грамм серебра (примерно)
        }

    def get_weight(self) -> float:
        """Возвращает вес монеты в граммах"""
        return self.weights.get(self.symbol, 0)

    def get_purity(self) -> float:
        """Возвращает чистоту металла (0-1)"""
        return self.purities.get(self.symbol, 0)

    def get_metal_type(self) -> str:
        """Определяет тип металла"""
        if "gold" in self.symbol:
            return "gold"
        elif "silver" in self.symbol:
            return "silver"
        else:
            return "unknown"

    def calculate_price(self) -> float:
        """
        Рассчитывает цену монеты по формуле:
        цена = вес * цена_металла * чистота * коэффициент_премии
        """
        try:
            weight = self.get_weight()
            purity = self.get_purity()
            metal_type = self.get_metal_type()
            metal_price = self.metal_prices.get(metal_type, 0)

            if weight <= 0 or metal_price <= 0:
                return 0

            # Базовая стоимость металла в монете
            base_value = weight * metal_price * purity

            # Коэффициент премии (надбавка за чеканку, бренд и т.д.)
            # Для золота обычно 5-15%, для серебра 10-30%
            premium_multiplier = 1.15 if metal_type == "gold" else 1.20

            # Итоговая цена
            final_price = base_value * premium_multiplier

            logger.debug(f"Calculated price for {self.symbol}: "
                         f"weight={weight}g, purity={purity}, "
                         f"metal_price=${metal_price}/g, "
                         f"base_value=${base_value:.2f}, "
                         f"final_price=${final_price:.2f}")

            return final_price

        except Exception as e:
            logger.error(f"Error calculating price for {self.symbol}: {e}")
            return 0

    async def get_price(self) -> Optional[AssetPrice]:
        """
        Получает цену драгоценного металла.
        Рассчитывается на основе текущей цены металла и характеристик монеты.
        """
        try:
            # Здесь можно добавить получение реальных цен на металлы из API
            # Например, из London Bullion Market Association (LBMA)
            # Пока используем расчетную цену

            price = self.calculate_price()

            return AssetPrice(
                symbol=self.symbol,
                price=price,
                currency="USD",
                source="calculated",
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting price for precious metal {self.symbol}: {e}")
            return None

    def validate_amount(self, amount: float) -> bool:
        """Валидирует количество монет"""
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    def format_amount(self, amount: float) -> str:
        """Форматирует количество монет"""
        # Обычно монеты считаются штуками
        if amount.is_integer():
            return f"{amount:,.0f} шт"
        else:
            return f"{amount:,.2f} шт"

    def format_value(self, amount: float, price: float) -> str:
        """Форматирует стоимость"""
        value = amount * price
        return f"${value:,.2f}"

    def get_metal_info(self) -> Dict[str, Any]:
        """Возвращает информацию о металле"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "weight_g": self.get_weight(),
            "weight_oz": self.get_weight() / 31.1035,  # Конвертация в тройские унции
            "purity": self.get_purity(),
            "metal_type": self.get_metal_type(),
            "price_per_g": self.metal_prices.get(self.get_metal_type(), 0)
        }

    def update_metal_price(self, metal_type: str, price_per_g: float):
        """Обновляет цену металла"""
        if metal_type in ["gold", "silver"]:
            self.metal_prices[metal_type] = price_per_g
            logger.info(f"Updated {metal_type} price to ${price_per_g}/g")