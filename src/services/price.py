# src/services/price.py
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.assets.registry import asset_registry
from src.assets.base import AssetPrice

logger = logging.getLogger(__name__)


class PriceService:
    """Сервис для получения цен активов"""

    def __init__(self):
        self.cache: Dict[str, AssetPrice] = {}
        self.cache_time: Dict[str, float] = {}
        self.cache_ttl = 60  # секунды

    async def get_price(self, symbol: str) -> Optional[AssetPrice]:
        """Получает цену одного актива"""
        # Проверяем кэш
        cache_key = f"price_{symbol}"
        current_time = asyncio.get_event_loop().time()

        if (cache_key in self.cache and
                cache_key in self.cache_time and
                current_time - self.cache_time[cache_key] < self.cache_ttl):
            logger.debug(f"Using cached price for {symbol}")
            return self.cache[cache_key]

        # Получаем актив из реестра
        asset = asset_registry.get_asset(symbol)
        if not asset:
            logger.error(f"Asset not found: {symbol}")
            return None

        # Получаем цену
        price = await asset.get_price()
        if price:
            # Сохраняем в кэш
            self.cache[cache_key] = price
            self.cache_time[cache_key] = current_time

        return price

    async def get_prices(self, symbols: List[str]) -> Dict[str, Optional[AssetPrice]]:
        """Получает цены для нескольких активов"""
        # Уникальные символы
        unique_symbols = list(set(symbols))

        # Запрашиваем цены параллельно
        tasks = [self.get_price(symbol) for symbol in unique_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем результаты
        prices = {}
        for symbol, result in zip(unique_symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Error getting price for {symbol}: {result}")
                prices[symbol] = None
            else:
                prices[symbol] = result

        return prices

    async def get_all_crypto_prices(self) -> Dict[str, Optional[AssetPrice]]:
        """Получает цены всех крипто активов"""
        crypto_assets = asset_registry.get_crypto_assets()
        symbols = [asset.symbol for asset in crypto_assets]
        return await self.get_prices(symbols)

    async def get_all_fiat_prices(self) -> Dict[str, Optional[AssetPrice]]:
        """Получает цены всех фиатных валют"""
        fiat_assets = asset_registry.get_fiat_assets()
        symbols = [asset.symbol for asset in fiat_assets]
        return await self.get_prices(symbols)

    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Конвертирует сумму из одной валюты в другую"""
        try:
            # Если конвертируем из USD в USD
            if from_currency.upper() == to_currency.upper():
                return amount

            # Получаем цены обеих валют
            prices = await self.get_prices([from_currency, to_currency])

            from_price = prices.get(from_currency)
            to_price = prices.get(to_currency)

            if not from_price or not to_price:
                logger.error(f"Cannot get prices for conversion: {from_currency} -> {to_currency}")
                return None

            # Конвертируем: amount * (price_from / price_to)
            result = amount * (from_price.price / to_price.price)
            return result

        except Exception as e:
            logger.error(f"Error converting currency: {e}")
            return None

    def clear_cache(self):
        """Очищает кэш цен"""
        self.cache.clear()
        self.cache_time.clear()
        logger.info("Price cache cleared")


# Глобальный экземпляр сервиса
price_service = PriceService()