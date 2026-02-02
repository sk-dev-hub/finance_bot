# src/assets/crypto.py
import aiohttp
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig
from src.config.settings import settings, PriceSources

logger = logging.getLogger(__name__)


class CryptoAsset(BaseAsset):
    """Класс для криптовалютных активов"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Создает или возвращает сессию"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def get_price(self) -> Optional[AssetPrice]:
        """Получает цену криптовалюты"""
        logger.info(f"Getting price for {self.symbol} from {self.config.price_source}")

        # Пробуем основной источник
        if self.config.price_source == PriceSources.COINGECKO:
            logger.info(f"Trying CoinGecko for {self.symbol}")
            price = await self._get_price_coingecko()
            if price:
                logger.info(f"CoinGecko price for {self.symbol}: {price.price}")
                return price
            # Fallback на Binance если CoinGecko недоступен
            logger.warning(f"CoinGecko failed for {self.symbol}, trying Binance")

        # Получаем цену с Binance (основной или fallback источник)
        logger.info(f"Trying Binance for {self.symbol}")
        binance_price = await self._get_price_binance()
        if binance_price:
            logger.info(f"Binance price for {self.symbol}: {binance_price.price}")
        else:
            logger.warning(f"Both CoinGecko and Binance failed for {self.symbol}")

        return binance_price

    async def _get_price_coingecko(self) -> Optional[AssetPrice]:
        """Получает цену с CoinGecko"""
        try:
            session = await self._get_session()
            url = f"{settings.COINGECKO_API_URL}/simple/price"

            params = {
                "ids": self.config.source_id,
                "vs_currencies": "usd",
                "precision": 8,
                "x_cg_demo_api_key": settings.COINGECKO_API_KEY
            }

            headers = {}
            if settings.COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY

            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    if self.config.source_id in data:
                        price = data[self.config.source_id].get("usd")
                        if price:
                            return AssetPrice(
                                symbol=self.symbol,
                                price=price,
                                source=PriceSources.COINGECKO,
                                timestamp=datetime.now()
                            )
                    else:
                        logger.error(f"Coin {self.config.source_id} not found in response")

                elif response.status == 429:
                    logger.warning(f"CoinGecko rate limit exceeded for {self.symbol}")
                    return None
                else:
                    logger.error(f"CoinGecko API error {self.symbol}: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching price from CoinGecko for {self.symbol}: {e}")

        return None

    async def _get_price_binance(self) -> Optional[AssetPrice]:
        """Получает цену с Binance"""
        try:
            session = await self._get_session()

            # Формируем символ для Binance (большинство крипто торгуются против USDT)
            if self.symbol.upper() == "USDT":
                # USDT/USD обычно 1:1, но можно получить через другую пару
                return AssetPrice(
                    symbol=self.symbol,
                    price=1.0,  # USDT обычно равен 1 USD
                    source=PriceSources.BINANCE,
                    timestamp=datetime.now()
                )

            # Для основных крипто используем USDT пары
            symbol_mapping = {
                "btc": "BTCUSDT",
                "eth": "ETHUSDT",
                "ton": "TONUSDT",
                "sol": "SOLUSDT",
                "usdt": "USDTUSD",  # Для получения точного курса
            }

            binance_symbol = symbol_mapping.get(self.symbol.lower(), f"{self.symbol.upper()}USDT")

            url = f"{settings.BINANCE_API_URL}/ticker/price"
            params = {"symbol": binance_symbol}

            # Добавляем API ключ Binance если есть
            headers = {}
            if settings.BINANCE_API_KEY:
                headers["X-MBX-APIKEY"] = settings.BINANCE_API_KEY

            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data.get("price", 0))

                    if price > 0:
                        return AssetPrice(
                            symbol=self.symbol,
                            price=price,
                            source=PriceSources.BINANCE,
                            timestamp=datetime.now()
                        )
                    else:
                        logger.error(f"Invalid price from Binance for {self.symbol}: {price}")

                elif response.status == 429:
                    logger.warning(f"Binance rate limit exceeded for {self.symbol}")
                    # Можно попробовать другой endpoint
                    return await self._get_price_binance_alternative()
                else:
                    logger.error(f"Binance API error {self.symbol}: {response.status} - {await response.text()}")

        except Exception as e:
            logger.error(f"Error fetching price from Binance for {self.symbol}: {e}")

        return None

    async def _get_price_binance_alternative(self) -> Optional[AssetPrice]:
        """Альтернативный метод получения цены с Binance"""
        try:
            session = await self._get_session()

            # Пробуем endpoint /ticker/24hr который также содержит текущую цену
            if self.symbol.upper() == "USDT":
                return AssetPrice(
                    symbol=self.symbol,
                    price=1.0,
                    source=PriceSources.BINANCE,
                    timestamp=datetime.now()
                )

            symbol_mapping = {
                "btc": "BTCUSDT",
                "eth": "ETHUSDT",
                "ton": "TONUSDT",
                "sol": "SOLUSDT",
            }

            binance_symbol = symbol_mapping.get(self.symbol.lower(), f"{self.symbol.upper()}USDT")
            url = f"{settings.BINANCE_API_URL}/ticker/24hr"
            params = {"symbol": binance_symbol}

            headers = {}
            if settings.BINANCE_API_KEY:
                headers["X-MBX-APIKEY"] = settings.BINANCE_API_KEY

            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Используем последнюю цену из 24hr данных
                    last_price = data.get("lastPrice")
                    if last_price:
                        price = float(last_price)
                        return AssetPrice(
                            symbol=self.symbol,
                            price=price,
                            source=PriceSources.BINANCE,
                            timestamp=datetime.now()
                        )

        except Exception as e:
            logger.error(f"Error fetching price from Binance alternative for {self.symbol}: {e}")

        return None


    def validate_amount(self, amount: float) -> bool:
        """Валидирует количество криптовалюты"""
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()