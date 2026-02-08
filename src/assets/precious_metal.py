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

    async def get_current_metal_price(self, metal_type: str) -> Optional[float]:
        """
        Получает актуальную цену металла за грамм в рублях от ЦБ РФ
        """
        try:
            from src.services.cbr_metals_service import metal_service

            # Получаем последние цены на металлы
            metal_prices = await metal_service.get_latest_prices()

            if not metal_prices:
                logger.warning(f"No metal prices available for {metal_type}")
                return None

            latest_price = metal_prices[0]  # Самая актуальная запись

            if metal_type == "gold":
                return latest_price.gold
            elif metal_type == "silver":
                return latest_price.silver
            else:
                logger.warning(f"Unknown metal type: {metal_type}")
                return None

        except Exception as e:
            logger.error(f"Error getting current metal price for {metal_type}: {e}")
            return None

    # Изменения в precious_metal.py - метод calculate_price

    async def calculate_price(self) -> float:
        """
        Рассчитывает актуальную цену монеты по формуле:
        цена = (стоимость_металла_за_грамм_от_ЦБ * вес) * metal_premium
        """
        try:
            weight = self.get_weight()
            metal_type = self.get_metal_type()

            # Получаем premium из конфигурации
            premium = getattr(self.config, 'metal_premium', 1.0)

            if weight <= 0:
                return 0

            # Получаем актуальную цену металла от ЦБ РФ
            current_price_per_gram_rub = await self.get_current_metal_price(metal_type)

            if current_price_per_gram_rub is None or current_price_per_gram_rub <= 0:
                logger.warning(f"No current price available for {metal_type}, using fallback")
                return 0

            # Расчет: стоимость металла в монете + premium надбавка
            metal_value_rub = current_price_per_gram_rub * weight
            final_price_rub = metal_value_rub * premium

            # Конвертируем в USD для совместимости с другими активами
            from src.services.currency_service import currency_service
            await currency_service.initialize()
            usd_rate = currency_service.get_real_usd_rub_rate_sync()

            if usd_rate > 0:
                final_price_usd = final_price_rub / usd_rate
            else:
                final_price_usd = 0

            logger.debug(f"Calculated price for {self.symbol}: "
                         f"weight={weight}g, "
                         f"current_{metal_type}_price={current_price_per_gram_rub:.2f} ₽/g, "
                         f"metal_value={metal_value_rub:.2f} ₽, "
                         f"premium={premium}, "
                         f"final_price={final_price_usd:.2f} USD ({final_price_rub:.2f} ₽)")

            return final_price_usd

        except Exception as e:
            logger.error(f"Error calculating price for {self.symbol}: {e}")
            return 0

    async def get_price(self) -> Optional[AssetPrice]:
        """
        Получает актуальную цену драгоценного металла.
        Рассчитывается на основе текущей цены металла от ЦБ РФ и веса монеты.
        """
        try:
            price = await self.calculate_price()

            return AssetPrice(
                symbol=self.symbol,
                price=price,
                currency="USD",
                source="calculated_from_cbr",
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
        weight = self.get_weight()
        return {
            "symbol": self.symbol,
            "name": self.name,
            "weight_g": weight,
            "weight_oz": weight / 31.1035 if weight > 0 else 0,  # Конвертация в тройские унции
            "purity": self.get_purity(),
            "metal_type": self.get_metal_type(),
        }

    async def get_detailed_price_info(self) -> Dict[str, Any]:
        """Возвращает подробную информацию о цене"""
        try:
            weight = self.get_weight()
            metal_type = self.get_metal_type()

            current_price_per_gram_rub = await self.get_current_metal_price(metal_type)

            if current_price_per_gram_rub:
                metal_value_rub = current_price_per_gram_rub * weight
                final_price_rub = metal_value_rub * 1.10

                from src.services.currency_service import currency_service
                await currency_service.initialize()
                usd_rate = currency_service.get_real_usd_rub_rate_sync()

                if usd_rate > 0:
                    final_price_usd = final_price_rub / usd_rate
                    current_price_per_gram_usd = current_price_per_gram_rub / usd_rate
                else:
                    final_price_usd = 0
                    current_price_per_gram_usd = 0

                return {
                    "weight_g": weight,
                    "metal_type": metal_type,
                    "current_price_per_gram_rub": current_price_per_gram_rub,
                    "current_price_per_gram_usd": current_price_per_gram_usd,
                    "metal_value_rub": metal_value_rub,
                    "final_price_rub": final_price_rub,
                    "final_price_usd": final_price_usd,
                    "premium_percent": 10.0,
                    "calculation_formula": f"{current_price_per_gram_rub:.2f} ₽/g × {weight}g × 1.10"
                }

            return {
                "weight_g": weight,
                "metal_type": metal_type,
                "error": "Цена металла недоступна"
            }

        except Exception as e:
            logger.error(f"Error getting detailed price info for {self.symbol}: {e}")
            return {
                "weight_g": self.get_weight(),
                "metal_type": self.get_metal_type(),
                "error": str(e)
            }