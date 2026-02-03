# src/services/cbr_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import aiohttp
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class CBRService:
    """Сервис для получения курсов валют от Центрального Банка РФ"""

    CBR_API_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
    CBR_API_URL_DYNAMIC = "https://www.cbr.ru/scripts/XML_dynamic.asp"

    # Коды валют по ЦБ РФ
    CURRENCY_CODES = {
        "usd": "R01235",  # Доллар США
        "eur": "R01239",  # Евро
        "cny": "R01375",  # Китайский юань
        "gbp": "R01035",  # Фунт стерлингов
        "jpy": "R01820",  # Японская йена
        "chf": "R01775",  # Швейцарский франк
        "try": "R01700J",  # Турецкая лира
        "kzt": "R01335",  # Казахстанский тенге
        "uah": "R01720",  # Украинская гривна
        "byn": "R01090B",  # Белорусский рубль
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Dict] = {}
        self.cache_time: Dict[str, datetime] = {}
        self.cache_ttl = 3600  # 1 час в секундах

    async def _get_session(self) -> aiohttp.ClientSession:
        """Создает или возвращает сессию"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def get_daily_rates(self, date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Получает курсы валют на определенную дату
        :param date: Дата, на которую нужны курсы (по умолчанию - сегодня)
        :return: Словарь с курсами валют {currency_code: rate}
        """
        try:
            session = await self._get_session()

            # Формируем параметры запроса
            params = {}
            if date:
                params['date_req'] = date.strftime('%d/%m/%Y')

            async with session.get(self.CBR_API_URL, params=params) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    return self._parse_daily_rates(xml_data)
                else:
                    logger.error(f"CBR API error: {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error getting CBR rates: {e}")
            return {}

    async def get_currency_rate(self, currency_code: str, date: Optional[datetime] = None) -> Optional[float]:
        """
        Получает курс конкретной валюты
        :param currency_code: Код валюты (например, 'usd', 'eur')
        :param date: Дата (по умолчанию - сегодня)
        :return: Курс валюты или None в случае ошибки
        """
        try:
            # Проверяем кэш
            cache_key = f"{currency_code}_{date.strftime('%Y%m%d') if date else 'today'}"
            current_time = datetime.now()

            if (cache_key in self.cache and
                    cache_key in self.cache_time and
                    (current_time - self.cache_time[cache_key]).seconds < self.cache_ttl):
                logger.debug(f"Using cached rate for {currency_code}")
                return self.cache[cache_key]

            # Получаем код валюты для ЦБ РФ
            cbr_currency_code = self.CURRENCY_CODES.get(currency_code.lower())
            if not cbr_currency_code:
                logger.error(f"Unknown currency code: {currency_code}")
                return None

            session = await self._get_session()

            # Если нужна историческая дата, используем динамический API
            if date and date != datetime.now().date():
                date_req1 = date.strftime('%d/%m/%Y')
                date_req2 = date.strftime('%d/%m/%Y')

                params = {
                    'date_req1': date_req1,
                    'date_req2': date_req2,
                    'VAL_NM_RQ': cbr_currency_code
                }

                async with session.get(self.CBR_API_URL_DYNAMIC, params=params) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        rate = self._parse_dynamic_rate(xml_data, currency_code)
                        if rate:
                            # Сохраняем в кэш
                            self.cache[cache_key] = rate
                            self.cache_time[cache_key] = current_time
                        return rate
                    else:
                        logger.error(f"CBR dynamic API error: {response.status}")
                        return None
            else:
                # Для текущей даты используем основной API
                rates = await self.get_daily_rates(date)
                rate = rates.get(currency_code.lower())
                if rate:
                    # Сохраняем в кэш
                    self.cache[cache_key] = rate
                    self.cache_time[cache_key] = current_time
                return rate

        except Exception as e:
            logger.error(f"Error getting currency rate for {currency_code}: {e}")
            return None

    async def get_usd_rub_rate(self) -> Optional[float]:
        """Получает текущий курс USD/RUB"""
        return await self.get_currency_rate('usd')

    async def get_eur_rub_rate(self) -> Optional[float]:
        """Получает текущий курс EUR/RUB"""
        return await self.get_currency_rate('eur')

    def _parse_daily_rates(self, xml_data: str) -> Dict[str, float]:
        """Парсит XML с ежедневными курсами"""
        rates = {}
        try:
            root = ET.fromstring(xml_data)

            # Получаем дату курсов
            date_str = root.attrib.get('Date')
            logger.info(f"Parsing CBR rates for date: {date_str}")

            for valute in root.findall('Valute'):
                char_code = valute.find('CharCode').text.lower()
                value = valute.find('Value').text
                nominal = int(valute.find('Nominal').text)

                # Конвертируем в число
                value_clean = value.replace(',', '.')
                try:
                    rate = float(value_clean) / nominal
                    rates[char_code] = rate
                except ValueError:
                    logger.warning(f"Could not parse rate for {char_code}: {value}")

        except Exception as e:
            logger.error(f"Error parsing CBR XML: {e}")

        return rates

    def _parse_dynamic_rate(self, xml_data: str, currency_code: str) -> Optional[float]:
        """Парсит XML с динамикой курса"""
        try:
            root = ET.fromstring(xml_data)

            # Ищем последнюю запись
            records = root.findall('Record')
            if records:
                last_record = records[-1]
                value = last_record.find('Value').text
                nominal = int(last_record.find('Nominal').text)

                # Конвертируем в число
                value_clean = value.replace(',', '.')
                rate = float(value_clean) / nominal
                return rate

        except Exception as e:
            logger.error(f"Error parsing CBR dynamic XML for {currency_code}: {e}")

        return None

    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Конвертирует сумму из одной валюты в другую через RUB
        :param amount: Сумма для конвертации
        :param from_currency: Исходная валюта
        :param to_currency: Целевая валюта
        :return: Результат конвертации или None в случае ошибки
        """
        try:
            # Если конвертируем в ту же валюту
            if from_currency.lower() == to_currency.lower():
                return amount

            # Получаем курсы обеих валют к RUB
            from_rate = await self.get_currency_rate(from_currency)
            to_rate = await self.get_currency_rate(to_currency)

            if not from_rate or not to_rate:
                logger.error(f"Cannot get rates for conversion: {from_currency} -> {to_currency}")
                return None

            # Конвертируем через RUB: amount * (from_rate / to_rate)
            result = amount * (from_rate / to_rate)
            return result

        except Exception as e:
            logger.error(f"Error converting currency {from_currency} -> {to_currency}: {e}")
            return None

    async def get_available_currencies(self) -> List[str]:
        """Возвращает список доступных валют"""
        return list(self.CURRENCY_CODES.keys())

    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def clear_cache(self):
        """Очищает кэш"""
        self.cache.clear()
        self.cache_time.clear()
        logger.info("CBR cache cleared")


# Глобальный экземпляр сервиса
cbr_service = CBRService()