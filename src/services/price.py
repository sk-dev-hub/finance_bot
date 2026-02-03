# src/services/price.py
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter

from src.assets.registry import asset_registry
from src.assets.base import AssetPrice
from src.config.settings import PriceSources

logger = logging.getLogger(__name__)


class PriceService:
    """Сервис для получения цен активов"""

    def __init__(self):
        self.cache: Dict[str, AssetPrice] = {}
        self.cache_time: Dict[str, float] = {}
        self.cache_ttl = 60  # секунды
        self.rate_limit_delay = 1.0  # Задержка между запросами
        self.last_request_time = 0.0
        self.request_counter = Counter()  # Счетчик запросов по источникам

    def get_active_price_source(self) -> str:
        """Определяет активный источник цен на основе статистики запросов"""
        try:
            if not self.request_counter:
                # Если счетчик пуст, проверяем конфигурацию активов
                crypto_assets = asset_registry.get_crypto_assets()
                if crypto_assets:
                    # Проверяем первый актив
                    asset = crypto_assets[0]
                    if hasattr(asset, 'config') and hasattr(asset.config, 'price_source'):
                        if asset.config.price_source == PriceSources.COINGECKO:
                            return "CoinGecko API"
                        elif asset.config.price_source == PriceSources.BINANCE:
                            return "Binance API"
                return "CoinGecko API, Binance API"

            # Находим самый частый источник
            most_common = self.request_counter.most_common(1)
            if most_common:
                source, count = most_common[0]
                if source == PriceSources.COINGECKO:
                    return f"CoinGecko API ({count} запросов)"
                elif source == PriceSources.BINANCE:
                    return f"Binance API ({count} запросов)"
                else:
                    return f"{source} ({count} запросов)"

            return "не определен"

        except Exception as e:
            logger.error(f"Error determining price source: {e}")
            return "CoinGecko API, Binance API"

    def get_price_sources_stats(self) -> Dict[str, int]:
        """Возвращает статистику по источникам цен"""
        return dict(self.request_counter)


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

            # Увеличиваем счетчик для источника
            if hasattr(price, 'source'):
                source_str = str(price.source)
                self.request_counter[source_str] += 1

        return price

    async def get_prices(self, symbols: List[str]) -> Dict[str, Optional[AssetPrice]]:
        """Получает цены для нескольких активов"""
        # Уникальные символы
        unique_symbols = list(set(symbols))

        # Сначала проверяем кэш для всех символов
        cached_results = {}
        remaining_symbols = []

        for symbol in unique_symbols:
            cache_key = f"price_{symbol}"
            current_time = asyncio.get_event_loop().time()

            if (cache_key in self.cache and
                    cache_key in self.cache_time and
                    current_time - self.cache_time[cache_key] < self.cache_ttl):
                cached_results[symbol] = self.cache[cache_key]
            else:
                remaining_symbols.append(symbol)

        # Если все есть в кэше, возвращаем
        if not remaining_symbols:
            return cached_results

        # Для оставшихся символов получаем цены с задержкой
        prices = cached_results.copy()

        for symbol in remaining_symbols:
            # Задержка между запросами
            current_time = asyncio.get_event_loop().time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last_request)

            asset = asset_registry.get_asset(symbol)
            if asset:
                price = await asset.get_price()
                self.last_request_time = asyncio.get_event_loop().time()

                if price:
                    # Увеличиваем счетчик для источника
                    if hasattr(price, 'source'):
                        source_str = str(price.source)
                        self.request_counter[source_str] += 1

                    cache_key = f"price_{symbol}"
                    self.cache[cache_key] = price
                    self.cache_time[cache_key] = current_time
                    prices[symbol] = price
                else:
                    prices[symbol] = None
            else:
                prices[symbol] = None

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