# src/bot/helpers/formatters.py
"""
Функции для форматирования данных.

"""
import logging
from typing import Optional, Dict, Any
from src.services.currency_service import currency_service
from datetime import datetime, timezone, timedelta

logger = logging.getLogger()

def format_currency(value: float) -> str:
    """Форматирует денежное значение"""
    if value >= 1000:
        return f"${value:,.2f}"
    elif value >= 1:
        return f"${value:.2f}"
    else:
        return f"${value:.4f}"


def format_percentage(value: float) -> str:
    """Форматирует процентное значение"""
    return f"{value:+.1f}%" if value is not None else "0.0%"


def format_price_for_asset(symbol: str, price: float, currency: str = "usd") -> str:  # Добавлен параметр currency
    """Форматирует цену в зависимости от типа актива и валюты"""
    if currency.lower() == "rub":
        if price >= 1000:
            return f"{price:,.0f} ₽"
        elif price >= 1:
            return f"{price:.2f} ₽"
        else:
            return f"{price:.4f} ₽"
    else:  # USD по умолчанию
        if symbol in ["btc", "eth"]:
            return f"${price:,.2f}"
        elif symbol in ["ton", "sol"]:
            return f"${price:,.4f}"
        elif symbol == "usdt":
            return f"${price:.2f}"
        else:
            return f"${price:,.4f}"




def format_amount_for_asset(symbol: str, amount: float) -> str:
    """Форматирует количество в зависимости от типа актива"""
    if symbol in ["btc", "eth"]:
        return f"{amount:.6f}"
    elif symbol in ["ton", "sol"]:
        return f"{amount:.2f}"
    elif symbol in ["rub", "eur", "usd"]:
        return f"{amount:,.0f}"
    else:
        return f"{amount:.2f}"


def format_portfolio_asset(
        symbol: str,
        amount: float,
        price_usd: Optional[float] = None,
        price_rub: Optional[float] = None  # Добавлен параметр
) -> Dict[str, Any]:
    """Форматирует информацию об активе в портфеле"""
    result = {
        "symbol": symbol,
        "amount": amount,
        "amount_formatted": format_amount_for_asset(symbol, amount),
        "price_usd": price_usd,
        "price_usd_formatted": format_price_for_asset(symbol, price_usd, "usd") if price_usd else "❌ недоступна",
        "price_rub": price_rub,
        "price_rub_formatted": format_price_for_asset(symbol, price_rub, "rub") if price_rub else "❌ недоступна",
        "value_usd": None,
        "value_usd_formatted": "❌ недоступна",
        "value_rub": None,
        "value_rub_formatted": "❌ недоступна"
    }

    if price_usd:
        value_usd = amount * price_usd
        result["value_usd"] = value_usd
        result["value_usd_formatted"] = format_currency(value_usd)

        # Рассчитываем стоимость в рублях
        value_rub = currency_service.usd_to_rub_real_sync(value_usd)
        result["value_rub"] = value_rub
        result["value_rub_formatted"] = currency_service.format_rub(value_rub)

        # Также сохраняем сырое значение для обратной совместимости
        result["raw_value"] = value_usd
        result["value"] = value_usd  # Для обратной совместимости
        result["value_formatted"] = result["value_usd_formatted"]  # Для обратной совместимости

    return result


def format_fiat_rate(symbol: str, price: float) -> str:
    """Форматирует курс фиатной валюты"""
    if symbol == "usd":
        return f"1 USD = 1.0000 {symbol.upper()}"
    else:
        return f"1 USD = {1 / price:.4f} {symbol.upper()}\n(1 {symbol.upper()} = ${price:.4f})"


def format_metal_info(weight_g: float, purity: float) -> str:
    """Форматирует информацию о металле"""
    weight_oz = weight_g / 31.1035
    return f"Вес: {weight_g}g ({weight_oz:.2f} oz)\nЧистота: {purity * 100:.2f}%"


def format_timestamp(timestamp: str = None) -> str:
    """Форматирует временную метку в московское время (MSK)"""
    try:
        if timestamp:
            # Если передана временная метка
            # Просто извлекаем время из ISO строки и показываем как есть с пометкой MSK
            if 'T' in timestamp:
                time_part = timestamp.split('T')[1]
                time_part = time_part.split('.')[0]  # Убираем микросекунды
                return f"{time_part} MSK"
            else:
                return f"{timestamp} MSK"
        else:
            # Если метка не передана, возвращаем текущее московское время
            from datetime import datetime, timezone, timedelta

            # Создаем смещение для MSK (UTC+3)
            msk_offset = timedelta(hours=3)
            msk_tz = timezone(msk_offset)

            # Получаем текущее время в MSK
            current_time = datetime.now(msk_tz)
            return current_time.strftime("%H:%M:%S MSK")

    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {e}")
        return "недавно"