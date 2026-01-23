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

        if self.config.price_source == PriceSources.COINGECKO:
            return await self._get_price_coingecko()
        elif self.config.price_source == PriceSources.BINANCE:
            return await self._get_price_binance()
        else:
            logger.error(f"Unsupported price source: {self.config.price_source}")
            return None

    async def _get_price_coingecko(self) -> Optional[AssetPrice]:
        """Получает цену с CoinGecko"""
        try:
            session = await self._get_session()
            url = f"{settings.COINGECKO_API_URL}/simple/price"

            params = {
                "ids": self.config.source_id,
                "vs_currencies": "usd",
                "precision": 8
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if self.config.source_id in data:
                        price = data[self.config.source_id].get("usd")
                        if price:
                            return AssetPrice(
                                symbol=self.symbol,
                                price=price,
                                source=PriceSources.COINGECKO
                            )
                    else:
                        logger.error(f"Coin {self.config.source_id} not found in response")
                else:
                    logger.error(f"CoinGecko API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching price from CoinGecko: {e}")

        return None

    async def _get_price_binance(self) -> Optional[AssetPrice]:
        """Получает цену с Binance"""
        try:
            session = await self._get_session()
            symbol = f"{self.symbol.upper()}USDT"
            url = f"{settings.BINANCE_API_URL}/ticker/price"

            params = {"symbol": symbol}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data.get("price", 0))

                    return AssetPrice(
                        symbol=self.symbol,
                        price=price,
                        source=PriceSources.BINANCE
                    )
                else:
                    logger.error(f"Binance API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching price from Binance: {e}")

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