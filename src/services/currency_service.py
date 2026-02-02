# src/services/currency_service.py
import logging
from typing import Optional
from src.config.settings import settings

logger = logging.getLogger(__name__)


class CurrencyService:
    """Сервис для конвертации валют"""

    @staticmethod
    def usd_to_rub(amount_usd: float) -> float:
        """Конвертирует USD в RUB по курсу из настроек"""
        if not amount_usd:
            return 0.0

        try:
            rate = settings.RUB_EXCHANGE_RATE
            return round(amount_usd * rate, 2)
        except Exception as e:
            logger.error(f"Error converting USD to RUB: {e}")
            return amount_usd * 91.0  # fallback

    @staticmethod
    def format_rub(amount_rub: float) -> str:
        """Форматирует сумму в рублях"""
        if amount_rub >= 1000:
            return f"{amount_rub:,.0f} ₽"
        else:
            return f"{amount_rub:.2f} ₽"

    @staticmethod
    def format_usd_and_rub(amount_usd: float) -> str:
        """Форматирует сумму в USD и RUB"""
        if not amount_usd:
            return "0.00 $ | 0.00 ₽"

        # USD
        if amount_usd >= 1000:
            usd_str = f"${amount_usd:,.0f}"
        elif amount_usd >= 1:
            usd_str = f"${amount_usd:.2f}"
        else:
            usd_str = f"${amount_usd:.4f}"

        # RUB
        amount_rub = CurrencyService.usd_to_rub(amount_usd)
        rub_str = CurrencyService.format_rub(amount_rub)

        return f"{usd_str} | {rub_str}"


# Глобальный экземпляр
currency_service = CurrencyService()