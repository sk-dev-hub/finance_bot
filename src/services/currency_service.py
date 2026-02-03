# src/services/currency_service.py
import logging
from typing import Optional
from datetime import datetime
from src.config.settings import settings
from src.services.cbr_service import cbr_service

logger = logging.getLogger(__name__)


class CurrencyService:
    """Сервис для конвертации валют"""

    def __init__(self):
        self.usd_rub_rate_cbr = None  # Чистый курс USD/RUB от ЦБ
        self.other_rates_cbr = {}  # Курсы других валют от ЦБ {currency: rate_to_rub}
        self.last_update = None
        self.update_interval = 3600  # 1 час
        self.usd_additional_rub = 2.0  # +2 рубля только к USD (ИЗМЕНИЛ НАЗВАНИЕ!)
        self._initialized = False

    async def initialize(self):
        """Инициализация сервиса - загружает курсы при старте"""
        if not self._initialized:
            await self.update_rates_from_cbr()
            self._initialized = True
            logger.info("CurrencyService инициализирован")

    async def _ensure_initialized(self):
        """Убеждается, что сервис инициализирован"""
        if not self._initialized:
            await self.initialize()

    async def _update_rates_if_needed(self):
        """Внутренний метод для обновления курсов если устарели"""
        await self._ensure_initialized()

        if (self.last_update is None or
                (datetime.now() - self.last_update).seconds > self.update_interval):
            await self.update_rates_from_cbr()

    async def update_rates_from_cbr(self):
        """Обновляет все курсы из ЦБ РФ"""
        try:
            logger.info("Обновление курсов из ЦБ РФ...")

            # Получаем курс USD/RUB
            usd_rate = await cbr_service.get_usd_rub_rate()

            if usd_rate:
                self.usd_rub_rate_cbr = usd_rate

                # Получаем курсы других валют
                self.other_rates_cbr = {}
                other_currencies = ["eur", "cny", "kzt", "uah"]

                for currency in other_currencies:
                    rate = await cbr_service.get_currency_rate(currency)
                    if rate:
                        self.other_rates_cbr[currency] = rate
                    else:
                        logger.warning(f"Не удалось получить курс для {currency}")

                self.last_update = datetime.now()

                logger.info(f"Курсы обновлены из ЦБ РФ:")
                logger.info(f"  - USD/RUB: {usd_rate:.2f} ₽")
                logger.info(
                    f"  - USD/RUB (реальный): {self.get_real_usd_rub_rate_sync():.2f} ₽ (+{self.usd_additional_rub} ₽)")  # ИЗМЕНИЛ НА usd_additional_rub

                # Логируем другие курсы
                for currency, rate in self.other_rates_cbr.items():
                    logger.info(f"  - {currency.upper()}/RUB: {rate:.2f} ₽")
            else:
                logger.error("Не удалось получить курс USD/RUB из ЦБ РФ")
                self._set_default_rates()

        except Exception as e:
            logger.error(f"Ошибка обновления курсов из CBR: {e}")
            # Используем значения по умолчанию если не удалось получить
            self._set_default_rates()

    def _set_default_rates(self):
        """Устанавливает курсы по умолчанию если ЦБ недоступен"""
        self.usd_rub_rate_cbr = settings.RUB_EXCHANGE_RATE or 80.0
        self.other_rates_cbr = {
            "eur": 88.0,  # примерно
            "cny": 11.2,  # примерно
            "kzt": 0.18,  # примерно
            "uah": 2.4,  # примерно
        }
        self.last_update = datetime.now()
        logger.warning(f"Используются курсы по умолчанию (ЦБ недоступен)")

    # ======================== ОСНОВНЫЕ МЕТОДЫ ========================

    async def usd_to_rub(self, amount_usd: float) -> float:
        """Для обратной совместимости - использует реальный курс"""
        return await self.usd_to_rub_real(amount_usd)

    # ======================== КУРС USD ========================

    async def get_real_usd_rub_rate(self) -> float:
        """Возвращает реальный курс USD/RUB (курс ЦБ + 2 рубля)"""
        await self._update_rates_if_needed()

        if self.usd_rub_rate_cbr is None:
            await self.update_rates_from_cbr()

        return self.usd_rub_rate_cbr + self.usd_additional_rub

    def get_real_usd_rub_rate_sync(self) -> float:
        """Синхронная версия - реальный курс USD/RUB"""
        if self.usd_rub_rate_cbr is None:
            logger.warning("Курс USD еще не загружен, используем дефолтный")
            default_rate = settings.RUB_EXCHANGE_RATE or 80.0
            return default_rate + self.usd_additional_rub
        return self.usd_rub_rate_cbr + self.usd_additional_rub

    async def get_cbr_usd_rub_rate(self) -> float:
        """Возвращает курс USD/RUB от ЦБ"""
        await self._update_rates_if_needed()

        if self.usd_rub_rate_cbr is None:
            await self.update_rates_from_cbr()

        return self.usd_rub_rate_cbr

    def get_cbr_usd_rub_rate_sync(self) -> float:
        """Синхронная версия - курс USD/RUB от ЦБ"""
        if self.usd_rub_rate_cbr is None:
            logger.warning("Курс USD еще не загружен, используем дефолтный")
            return settings.RUB_EXCHANGE_RATE or 80.0
        return self.usd_rub_rate_cbr

    # ======================== КУРСЫ ДРУГИХ ВАЛЮТ ========================

    async def get_currency_to_rub_rate(self, currency: str) -> Optional[float]:
        """Возвращает курс валюты к RUB от ЦБ"""
        await self._update_rates_if_needed()

        if currency.lower() == "usd":
            return await self.get_cbr_usd_rub_rate()
        elif currency.lower() == "rub":
            return 1.0
        else:
            return self.other_rates_cbr.get(currency.lower())

    def get_currency_to_rub_rate_sync(self, currency: str) -> Optional[float]:
        """Синхронная версия - курс валюты к RUB от ЦБ (ДОБАВИЛ ЭТОТ МЕТОД!)"""
        if currency.lower() == "usd":
            return self.get_cbr_usd_rub_rate_sync()
        elif currency.lower() == "rub":
            return 1.0
        else:
            return self.other_rates_cbr.get(currency.lower())

    async def get_currency_to_usd_rate(self, currency: str) -> Optional[float]:
        """Возвращает курс валюты к USD"""
        if currency.lower() == "usd":
            return 1.0

        # Получаем курс к RUB
        currency_to_rub = await self.get_currency_to_rub_rate(currency)
        if not currency_to_rub:
            return None

        # Получаем реальный курс USD/RUB
        usd_to_rub_real = await self.get_real_usd_rub_rate()

        # Конвертируем: 1 валюта = X RUB = X / usd_to_rub_real USD
        return currency_to_rub / usd_to_rub_real

    def get_currency_to_usd_rate_sync(self, currency: str) -> Optional[float]:
        """Синхронная версия - курс валюты к USD"""
        if currency.lower() == "usd":
            return 1.0

        currency_to_rub = self.get_currency_to_rub_rate_sync(currency)
        if not currency_to_rub:
            return None

        usd_to_rub_real = self.get_real_usd_rub_rate_sync()
        return currency_to_rub / usd_to_rub_real

    # ======================== КОНВЕРТАЦИЯ ========================

    async def usd_to_rub_real(self, amount_usd: float) -> float:
        """Конвертирует USD в RUB по реальному курсу (+2 руб)"""
        if not amount_usd:
            return 0.0
        rate = await self.get_real_usd_rub_rate()
        return round(amount_usd * rate, 2)

    def usd_to_rub_real_sync(self, amount_usd: float) -> float:
        """Синхронная версия - конвертация USD в RUB"""
        if not amount_usd:
            return 0.0
        rate = self.get_real_usd_rub_rate_sync()
        return round(amount_usd * rate, 2)

    async def usd_to_rub_cbr(self, amount_usd: float) -> float:
        """Конвертирует USD в RUB по курсу ЦБ РФ (без надбавки)"""
        if not amount_usd:
            return 0.0
        rate = await self.get_cbr_usd_rub_rate()
        return round(amount_usd * rate, 2)

    def usd_to_rub_cbr_sync(self, amount_usd: float) -> float:
        """Синхронная версия - конвертация по курсу ЦБ"""
        if not amount_usd:
            return 0.0
        rate = self.get_cbr_usd_rub_rate_sync()
        return round(amount_usd * rate, 2)

    async def convert_to_usd(self, amount: float, from_currency: str) -> Optional[float]:
        """Конвертирует любую валюту в USD"""
        if from_currency.lower() == "usd":
            return amount

        rate = await self.get_currency_to_usd_rate(from_currency)
        if rate:
            return amount * rate
        return None

    def convert_to_usd_sync(self, amount: float, from_currency: str) -> Optional[float]:
        """Синхронная версия - конвертация в USD"""
        if from_currency.lower() == "usd":
            return amount

        rate = self.get_currency_to_usd_rate_sync(from_currency)
        if rate:
            return amount * rate
        return None

    # ======================== ФОРМАТИРОВАНИЕ И ИНФО ========================

    def format_rub(self, amount_rub: float) -> str:
        """Форматирует сумму в рублях"""
        if amount_rub >= 1000:
            return f"{amount_rub:,.0f} ₽"
        else:
            return f"{amount_rub:.2f} ₽"

    def get_rate_info(self) -> str:
        """Возвращает информацию о курсах"""
        cbr_rate = self.get_cbr_usd_rub_rate_sync()
        real_rate = self.get_real_usd_rub_rate_sync()

        info = f"💰 **Курсы валют:**\n"
        info += f"• USD/RUB (ЦБ): {cbr_rate:.2f} ₽\n"
        info += f"• USD/RUB (реальный): {real_rate:.2f} ₽ (+{self.usd_additional_rub} ₽)\n"  # ИЗМЕНИЛ

        # Добавляем другие валюты
        for currency, rate in self.other_rates_cbr.items():
            if rate:
                info += f"• {currency.upper()}/RUB: {rate:.2f} ₽\n"

        return info

    # ======================== ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ ========================

    @staticmethod
    def usd_to_rub_static(amount_usd: float) -> float:
        """Статический метод для обратной совместимости"""
        if not amount_usd:
            return 0.0

        # Используем глобальный экземпляр
        try:
            rate = currency_service.get_real_usd_rub_rate_sync()
            return round(amount_usd * rate, 2)
        except Exception as e:
            logger.error(f"Error in usd_to_rub_static: {e}")
            return amount_usd * 93.0  # Fallback

    @property
    def additional_rub(self):
        """Свойство для обратной совместимости (возвращает usd_additional_rub)"""
        return self.usd_additional_rub

    @additional_rub.setter
    def additional_rub(self, value):
        """Сеттер для обратной совместимости"""
        self.usd_additional_rub = value


# Глобальный экземпляр
currency_service = CurrencyService()