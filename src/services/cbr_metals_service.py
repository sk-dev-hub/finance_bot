# src/services/cbr_metals_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MetalPrice:
    """Класс для хранения цен на драгоценные металлы"""
    date: datetime
    gold: float  # цена за грамм в рублях
    silver: float  # цена за грамм в рублях
    platinum: float  # цена за грамм в рублях
    palladium: float  # цена за грамм в рублях

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь"""
        return {
            "date": self.date,
            "gold": self.gold,
            "silver": self.silver,
            "platinum": self.platinum,
            "palladium": self.palladium
        }

    def format_price(self, metal_type: str) -> str:
        """Форматирует цену для вывода"""
        prices = {
            "gold": self.gold,
            "silver": self.silver,
            "platinum": self.platinum,
            "palladium": self.palladium
        }

        if metal_type not in prices:
            raise ValueError(f"Unknown metal type: {metal_type}")

        price = prices[metal_type]
        return f"{price:,.2f}".replace(',', ' ')


class MetalService:
    """Сервис для получения цен на драгоценные металлы от ЦБ РФ"""

    CBR_METAL_URL = "https://cbr.ru/hd_base/metall/metall_base_new/"

    # Коды металлов
    METAL_TYPES = {
        "gold": "Золото",
        "silver": "Серебро",
        "platinum": "Платина",
        "palladium": "Палладий"
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, List[MetalPrice]] = {}
        self.cache_time: Dict[str, datetime] = {}
        self.cache_ttl = 1800  # 30 минут в секундах (цены обновляются реже чем валюты)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Создает или возвращает сессию"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)  # На случай проблем с SSL
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session

    async def _fetch_metal_prices(self) -> List[MetalPrice]:
        """Загружает и парсит данные с сайта ЦБ РФ"""
        try:
            session = await self._get_session()

            async with session.get(self.CBR_METAL_URL) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch metal prices: HTTP {response.status}")
                    return []

                html_content = await response.text()
                return self._parse_metal_prices(html_content)

        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching metal prices: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching metal prices: {e}")
            return []

    def _parse_metal_prices(self, html_content: str) -> List[MetalPrice]:
        """Парсит HTML с ценами на металлы"""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table')

            if not table:
                logger.error("Metal price table not found")
                return []

            # Находим все строки таблицы
            rows = table.find_all('tr')
            prices = []

            # Пропускаем заголовок таблицы (первая строка)
            for row in rows[1:]:
                cols = row.find_all('td')

                # Проверяем, что строка содержит все 5 колонок (дата + 4 металла)
                if len(cols) >= 5:
                    try:
                        # Извлекаем и очищаем данные
                        date_str = cols[0].text.strip()

                        # Преобразуем дату
                        date = datetime.strptime(date_str, '%d.%m.%Y')

                        # Извлекаем и преобразуем цены
                        gold = float(cols[1].text.strip().replace(' ', '').replace(',', '.'))
                        silver = float(cols[2].text.strip().replace(' ', '').replace(',', '.'))
                        platinum = float(cols[3].text.strip().replace(' ', '').replace(',', '.'))
                        palladium = float(cols[4].text.strip().replace(' ', '').replace(',', '.'))

                        # Создаем объект MetalPrice
                        metal_price = MetalPrice(
                            date=date,
                            gold=gold,
                            silver=silver,
                            platinum=platinum,
                            palladium=palladium
                        )

                        prices.append(metal_price)

                    except ValueError as e:
                        logger.warning(f"Failed to parse row: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Unexpected error parsing row: {e}")
                        continue

            # Сортируем по дате (от новых к старым)
            prices.sort(key=lambda x: x.date, reverse=True)

            logger.info(f"Successfully parsed {len(prices)} metal price records")
            return prices

        except ImportError:
            logger.error("BeautifulSoup4 is required. Install it with: pip install beautifulsoup4")
            return []
        except Exception as e:
            logger.error(f"Error parsing metal prices: {e}")
            return []

    async def get_latest_prices(self, force_refresh: bool = False) -> List[MetalPrice]:
        """
        Получает последние доступные цены на металлы
        :param force_refresh: Принудительно обновить данные, игнорируя кэш
        :return: Список цен на металлы
        """
        cache_key = "latest"
        current_time = datetime.now()

        # Проверяем кэш, если не требуется принудительное обновление
        if not force_refresh:
            if (cache_key in self.cache and
                    cache_key in self.cache_time and
                    (current_time - self.cache_time[cache_key]).seconds < self.cache_ttl):
                logger.debug("Using cached metal prices")
                return self.cache[cache_key]

        # Загружаем свежие данные
        prices = await self._fetch_metal_prices()

        if prices:
            # Сохраняем в кэш
            self.cache[cache_key] = prices
            self.cache_time[cache_key] = current_time

        return prices

    async def get_latest_metal_price(self, metal_type: str = "gold") -> Optional[MetalPrice]:
        """
        Получает последнюю цену для конкретного металла
        :param metal_type: Тип металла (gold, silver, platinum, palladium)
        :return: Объект MetalPrice или None
        """
        if metal_type.lower() not in self.METAL_TYPES:
            logger.error(f"Unknown metal type: {metal_type}")
            return None

        prices = await self.get_latest_prices()

        if not prices:
            return None

        # Возвращаем последнюю (самую актуальную) запись
        return prices[0]

    async def get_metal_price_by_date(self, date: datetime) -> Optional[MetalPrice]:
        """
        Получает цену на металлы на определенную дату
        :param date: Дата для поиска
        :return: Объект MetalPrice или None
        """
        try:
            # Получаем все доступные цены
            prices = await self.get_latest_prices()

            if not prices:
                return None

            # Ищем цену на указанную дату
            target_date = date.date()
            for price in prices:
                if price.date.date() == target_date:
                    return price

            # Если точная дата не найдена, ищем ближайшую предыдущую
            for price in prices:
                if price.date.date() < target_date:
                    return price

            logger.warning(f"No metal price found for date {date.strftime('%d.%m.%Y')}")
            return None

        except Exception as e:
            logger.error(f"Error getting metal price by date: {e}")
            return None

    async def get_gold_price(self) -> Optional[float]:
        """Получает текущую цену на золото"""
        price = await self.get_latest_metal_price("gold")
        return price.gold if price else None

    async def get_silver_price(self) -> Optional[float]:
        """Получает текущую цену на серебро"""
        price = await self.get_latest_metal_price("silver")
        return price.silver if price else None

    async def get_platinum_price(self) -> Optional[float]:
        """Получает текущую цену на платину"""
        price = await self.get_latest_metal_price("platinum")
        return price.platinum if price else None

    async def get_palladium_price(self) -> Optional[float]:
        """Получает текущую цену на палладий"""
        price = await self.get_latest_metal_price("palladium")
        return price.palladium if price else None

    async def get_price_history(self, days: int = 30) -> List[MetalPrice]:
        """
        Получает историю цен за указанное количество дней
        :param days: Количество дней истории
        :return: Список цен на металлы
        """
        prices = await self.get_latest_prices()

        if not prices:
            return []

        # Фильтруем цены за последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_prices = [p for p in prices if p.date >= cutoff_date]

        return recent_prices

    async def get_metal_price_change(self, metal_type: str, days: int = 1) -> Optional[float]:
        """
        Получает изменение цены металла за указанное количество дней
        :param metal_type: Тип металла
        :param days: Количество дней для сравнения
        :return: Изменение в процентах или None
        """
        try:
            prices = await self.get_latest_prices()

            if len(prices) < days + 1:
                logger.warning(f"Not enough data to calculate {days}-day change")
                return None

            # Берем текущую цену и цену N дней назад
            current_price_obj = prices[0]
            historical_price_obj = prices[days]

            # Получаем цены для конкретного металла
            if metal_type.lower() not in self.METAL_TYPES:
                return None

            current_price = getattr(current_price_obj, metal_type.lower())
            historical_price = getattr(historical_price_obj, metal_type.lower())

            # Рассчитываем процентное изменение
            if historical_price == 0:
                return None

            change_percent = ((current_price - historical_price) / historical_price) * 100
            return change_percent

        except Exception as e:
            logger.error(f"Error calculating price change: {e}")
            return None

    async def get_all_metal_prices_dict(self) -> Dict[str, Any]:
        """
        Возвращает все текущие цены в виде словаря
        :return: Словарь с ценами на все металлы
        """
        latest = await self.get_latest_metal_price()

        if not latest:
            return {}

        return {
            "date": latest.date.strftime('%d.%m.%Y'),
            "gold": latest.gold,
            "silver": latest.silver,
            "platinum": latest.platinum,
            "palladium": latest.palladium,
            "formatted": {
                "gold": latest.format_price("gold"),
                "silver": latest.format_price("silver"),
                "platinum": latest.format_price("platinum"),
                "palladium": latest.format_price("palladium")
            }
        }

    async def get_available_metal_types(self) -> List[str]:
        """Возвращает список доступных типов металлов"""
        return list(self.METAL_TYPES.keys())

    async def get_metal_name(self, metal_type: str) -> Optional[str]:
        """Возвращает русское название металла"""
        return self.METAL_TYPES.get(metal_type.lower())

    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def clear_cache(self):
        """Очищает кэш"""
        self.cache.clear()
        self.cache_time.clear()
        logger.info("Metal service cache cleared")


# Глобальный экземпляр сервиса
metal_service = MetalService()

