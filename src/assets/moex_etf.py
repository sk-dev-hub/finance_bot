# src/assets/moex_etf.py
import aiohttp
import logging
from typing import Optional
from datetime import datetime, timedelta

from .base import BaseAsset, AssetPrice
from src.config.assets import AssetConfig

logger = logging.getLogger(__name__)


class MoexETFAsset(BaseAsset):
    """Класс для ETF на Московской бирже"""

    def __init__(self, config: AssetConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache = {}
        self._cache_time = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def get_price(self) -> Optional[AssetPrice]:
        """Получает цену с Московской биржи"""

        # Проверяем кэш (актуален 1 минуту)
        if self.symbol in self._cache:
            if datetime.now() - self._cache_time[self.symbol] < timedelta(minutes=1):
                return self._cache[self.symbol]

        try:
            # Пробуем несколько способов

            # Способ 1: MOEX ISS API
            price = await self._get_price_moex_iss()

            if price is None:
                # Способ 2: Investing.com через парсинг
                price = await self._get_price_investing()

            if price is None:
                # Способ 3: Фиксированная цена из конфигурации
                price = self._get_fallback_price()

            if price:
                asset_price = AssetPrice(
                    symbol=self.symbol,
                    price=price,
                    source="moex",
                    timestamp=datetime.now()
                )

                # Кэшируем
                self._cache[self.symbol] = asset_price
                self._cache_time[self.symbol] = datetime.now()

                return asset_price

        except Exception as e:
            logger.error(f"Error fetching MOEX ETF price for {self.symbol}: {e}")

        return None

    async def _get_price_moex_iss(self) -> Optional[float]:
        """Получает цену через MOEX ISS API"""
        try:
            session = await self._get_session()

            # Для FXGD используем тикер FXGD
            board = "TQTF"  # Торговая площадка для ETF
            security = "FXGD"  # Или self.config.source_id

            # API Московской биржи
            url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/{board}/securities/{security}.json"
            params = {
                "iss.meta": "off",
                "iss.json": "extended",
                "securities.columns": "SECID,LAST,LASTTOPREVPRICE"
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Структура ответа MOEX
                    if len(data) > 1 and 'securities' in data[1]:
                        securities_data = data[1]['securities']
                        if securities_data and len(securities_data['data']) > 0:
                            last_price = securities_data['data'][0][1]  # LAST цена
                            if last_price and last_price > 0:
                                return float(last_price)

            # Альтернативный endpoint
            url2 = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{security}.json"
            params2 = {
                "iss.meta": "off",
                "iss.json": "extended",
                "securities.columns": "PREVPRICE"
            }

            async with session.get(url2, params=params2) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data) > 1 and 'securities' in data[1]:
                        securities_data = data[1]['securities']
                        if securities_data and len(securities_data['data']) > 0:
                            prev_price = securities_data['data'][0][0]  # PREVPRICE
                            if prev_price and prev_price > 0:
                                return float(prev_price)

        except Exception as e:
            logger.error(f"MOEX ISS API error for {self.symbol}: {e}")

        return None

    async def _get_price_investing(self) -> Optional[float]:
        """Получает цену через парсинг Investing.com"""
        try:
            session = await self._get_session()

            # Investing.com для FXGD
            urls = [
                f"https://ru.investing.com/etfs/finex-fizicheskoe-zoloto",
                f"https://ru.investing.com/etfs/finex-physical-gold"
            ]

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            for url in urls:
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()

                            # Простой парсинг (нужно доработать под конкретную структуру)
                            import re

                            # Ищем цену в HTML
                            price_patterns = [
                                r'"last":"([\d\.]+)"',
                                r'data-test="instrument-price-last">([\d\.,]+)',
                                r'class="text-2xl"[^>]*>([\d\.,]+)'
                            ]

                            for pattern in price_patterns:
                                matches = re.search(pattern, html)
                                if matches:
                                    price_str = matches.group(1).replace(',', '.')
                                    return float(price_str)

                except:
                    continue

        except Exception as e:
            logger.error(f"Investing.com parsing error: {e}")

        return None

    def _get_fallback_price(self) -> Optional[float]:
        """Возвращает резервную цену из конфигурации"""
        # Можно добавить поле в AssetConfig для резервной цены
        fallback_prices = {
            "fxgd": 35.0,  # Примерная цена в рублях
            "tbrd": 1500.0
        }

        return fallback_prices.get(self.symbol)

    def validate_amount(self, amount: float) -> bool:
        return (
                amount >= self.config.min_amount and
                amount <= self.config.max_amount
        )

    def get_etf_info(self) -> dict:
        """Информация об ETF"""
        info = {
            "name": self.config.name,
            "currency": "RUB",
            "exchange": "MOEX",
            "ticker": "FXGD",
            "isin": "IE00B8XB7377",  # ISIN код FXGD
            "expense_ratio": 0.45,  # 0.45% комиссия
            "gold_per_share": 0.1,  # 0.1 грамма золота на акцию
            "fund_size": "~100 млрд руб",  # Примерный размер фонда
            "description": self.config.description
        }

        # Добавляем текущую цену если есть
        if self.symbol in self._cache:
            info["current_price"] = self._cache[self.symbol].price

        return info

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()