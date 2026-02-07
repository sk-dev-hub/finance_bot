# src/services/cbr_metals_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import aiohttp
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class CBRMetalsService:
    """Сервис для получения учетных цен драгоценных металлов от Центрального Банка РФ"""

    CBR_METALS_URL = "https://www.cbr.ru/scripts/xml_metall.asp"

    # Коды металлов по ЦБ РФ
    METAL_CODES = {
        "gold": "1",  # Золото
        "silver": "2",  # Серебро
        "platinum": "3",  # Платина
        "palladium": "4",  # Палладий
    }

    METAL_NAMES = {
        "gold": "Золото",
        "silver": "Серебро",
        "platinum": "Платина",
        "palladium": "Палладий",
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Dict] = {}  # key: "gold_20250207" → {"rate": 12008.30, "date": ...}
        self.cache_time: Dict[str, datetime] = {}
        self.cache_ttl = 3600 * 4  # 4 часа — цены обновляются раз в день

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def get_metal_price_rub(
            self,
            metal: str = "gold",
            date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Получает учетную цену металла в рублях за грамм на указанную дату

        :param metal: 'gold', 'silver', 'platinum', 'palladium'
        :param date: дата (по умолчанию — сегодня)
        :return: цена за 1 грамм в RUB или None
        """
        metal = metal.lower()
        if metal not in self.METAL_CODES:
            logger.error(f"Неизвестный металл: {metal}")
            return None

        try:
            cache_key = f"{metal}_{date.strftime('%Y%m%d') if date else 'today'}"
            now = datetime.now()

            if cache_key in self.cache and (now - self.cache_time.get(cache_key, now)).seconds < self.cache_ttl:
                logger.debug(f"Используем кэш для {metal} → {cache_key}")
                return self.cache[cache_key]["rate"]

            session = await self._get_session()

            params = {}
            if date:
                date_str = date.strftime("%d/%m/%Y")
                params["date_req1"] = date_str
                params["date_req2"] = date_str
            else:
                # Для сегодняшнего дня можно не указывать даты — вернёт последнюю доступную
                pass

            async with session.get(self.CBR_METALS_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"Ошибка CBR metals API: {response.status}")
                    return None

                xml_data = await response.text()
                price = self._parse_metal_price(xml_data, metal, date)

                if price is not None:
                    self.cache[cache_key] = {"rate": price, "fetched": now}
                    self.cache_time[cache_key] = now
                    logger.info(f"Получена цена {metal}: {price} RUB/г на {date or 'сегодня'}")

                return price

        except Exception as e:
            logger.error(f"Ошибка при получении цены на {metal}: {e}", exc_info=True)
            return None

    def _parse_metal_price(
            self,
            xml_data: str,
            metal: str,
            requested_date: Optional[datetime]
    ) -> Optional[float]:
        """Парсит XML и возвращает цену нужного металла за грамм"""
        try:
            root = ET.fromstring(xml_data)
            metal_code = self.METAL_CODES[metal]

            # Ищем записи
            for record in root.findall("Record"):
                code = record.get("Code")
                if code != metal_code:
                    continue

                # Дата записи
                rec_date_str = record.get("Date")
                if rec_date_str:
                    try:
                        rec_date = datetime.strptime(rec_date_str, "%d.%m.%Y")
                    except ValueError:
                        continue

                    # Если запрошена конкретная дата — проверяем совпадение
                    if requested_date and rec_date.date() != requested_date.date():
                        continue

                # Цена
                price_elem = record.find("Price")
                if price_elem is None:
                    continue

                price_text = price_elem.text.replace(",", ".").strip()
                try:
                    price = float(price_text)
                    return price
                except ValueError:
                    logger.warning(f"Не удалось преобразовать цену: {price_text}")
                    continue

            logger.warning(f"Цена для {metal} (код {metal_code}) не найдена в XML")
            return None

        except Exception as e:
            logger.error(f"Ошибка парсинга XML металлов: {e}", exc_info=True)
            return None

    async def get_gold_price_rub(self, date: Optional[datetime] = None) -> Optional[float]:
        """Текущая (или на дату) учетная цена золота в рублях за грамм"""
        return await self.get_metal_price_rub("gold", date)

    async def get_silver_price_rub(self, date: Optional[datetime] = None) -> Optional[float]:
        return await self.get_metal_price_rub("silver", date)

    async def get_all_metal_prices(
            self,
            date: Optional[datetime] = None
    ) -> Dict[str, Optional[float]]:
        """Получить цены всех металлов сразу"""
        tasks = {}
        for metal in self.METAL_CODES:
            tasks[metal] = await self.get_metal_price_rub(metal, date)
        return tasks

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def clear_cache(self):
        self.cache.clear()
        self.cache_time.clear()
        logger.info("CBR Metals cache cleared")


# Глобальный экземпляр сервиса
cbr_metals_service = CBRMetalsService()