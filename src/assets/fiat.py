# src/assets/fiat.py
import logging
from typing import Optional
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig
from src.config.settings import PriceSources
from src.services.cbr_service import cbr_service

logger = logging.getLogger(__name__)


class FiatAsset(BaseAsset):
    """Класс для фиатных валют"""

    # Коэффициенты для конвертации (если цена хранится не в RUB)
    CONVERSION_FACTORS = {
        "rub": 1.0,  # RUB к RUB
        "usd": 1.0,  # USD к USD (получаем курс USD/RUB)
        "eur": 1.0,  # EUR к USD через RUB
    }

    async def get_price(self) -> Optional[AssetPrice]:
        """Получает курс валюты"""
        try:
            if self.config.price_source == PriceSources.CBR:
                return await self._get_price_cbr()
            elif self.config.price_source == PriceSources.COINGECKO:
                return await self._get_price_coingecko()
            elif self.config.price_source == "static":
                return await self._get_price_static()
            else:
                logger.error(f"Unsupported price source for fiat: {self.config.price_source}")
                return None

        except Exception as e:
            logger.error(f"Error getting fiat price for {self.symbol}: {e}")
            return None

    async def _get_price_static(self) -> Optional[AssetPrice]:
        """Получает статический курс из конфигурации"""
        try:
            # Используем exchange_rate из конфигурации
            # Для рубля всегда 1
            if self.symbol.lower() == "rub":
                price = 1.0
            else:
                # Получаем курс из конфигурации (стоимость в USD)
                price = self.config.exchange_rate

            return AssetPrice(
                symbol=self.symbol,
                price=price,
                source="cbr",  # Уже строка
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting static price for {self.symbol}: {e}")
            return None

    async def _get_price_cbr(self) -> Optional[AssetPrice]:
        """Получает курс с ЦБ РФ"""
        try:
            # Для рубля всегда 1
            if self.symbol.lower() == "rub":
                return AssetPrice(
                    symbol=self.symbol,
                    price=1.0,
                    source="cbr",
                    timestamp=datetime.now()
                )

            # Получаем курс валюты к RUB
            rate = await cbr_service.get_currency_rate(self.symbol)

            if rate:
                # Если нужен курс в USD (для консистентности с другими активами)
                if self.symbol.lower() != "usd":
                    # Получаем курс USD/RUB
                    usd_rate = await cbr_service.get_usd_rub_rate()
                    if usd_rate:
                        # Конвертируем в USD: 1 единица валюты = rate / usd_rate USD
                        price_in_usd = rate / usd_rate
                    else:
                        logger.warning(f"Cannot get USD rate for {self.symbol}, using direct rate")
                        price_in_usd = rate
                else:
                    # Для USD цена в USD = 1 / курс USD/RUB
                    price_in_usd = 1.0 / rate if rate else 1.0

                return AssetPrice(
                    symbol=self.symbol,
                    price=price_in_usd,
                    source="cbr",
                    timestamp=datetime.now()
                )
            else:
                logger.error(f"Cannot get CBR rate for {self.symbol}")
                return None

        except Exception as e:
            logger.error(f"Error getting CBR price for {self.symbol}: {e}")
            return None

    async def _get_price_coingecko(self) -> Optional[AssetPrice]:
        """Получает курс из CoinGecko (fallback)"""
        from .crypto import CryptoAsset

        # Создаем временный крипто-актив для получения цены через CoinGecko
        # (для валют CoinGecko возвращает курс к USD)
        temp_asset = CryptoAsset(self.config)
        crypto_price = await temp_asset.get_price()

        if crypto_price:
            # Для фиатных валют цена уже в USD
            return AssetPrice(
                symbol=self.symbol,
                price=crypto_price.price,
                source="coingecko",
                timestamp=datetime.now()
            )

        return None

    def validate_amount(self, amount: float) -> bool:
        """Валидирует количество валюты"""
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    def format_amount(self, amount: float) -> str:
        """Форматирует количество валюты"""
        if self.symbol.lower() in ["rub", "usd", "eur"]:
            return f"{amount:,.2f}"
        else:
            return f"{amount:.2f}"