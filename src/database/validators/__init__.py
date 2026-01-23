"""
Валидаторы для данных базы данных.

Предоставляет функции для валидации:
- Портфелей пользователей
- Количества активов
- Символов активов
- Данных транзакций
"""

from typing import Tuple, Optional
import logging
from ...assets.registry import asset_registry

logger = logging.getLogger(__name__)

__all__ = [
    'validate_portfolio',
    'validate_asset_amount',
    'validate_asset_symbol',
    'validate_transaction'
]


def validate_portfolio(portfolio_data: dict) -> Tuple[bool, str]:
    """Валидирует данные портфеля"""
    try:
        # Проверяем обязательные поля
        required_fields = ["user_id", "assets", "created_at", "updated_at"]
        for field in required_fields:
            if field not in portfolio_data:
                return False, f"Missing required field: {field}"

        # Проверяем типы данных
        if not isinstance(portfolio_data["user_id"], (int, str)):
            return False, "user_id must be integer or string"

        if not isinstance(portfolio_data["assets"], dict):
            return False, "assets must be a dictionary"

        # Валидируем каждый актив
        for symbol, asset_data in portfolio_data["assets"].items():
            # Проверяем поддержку актива
            if not asset_registry.is_supported(symbol):
                return False, f"Unsupported asset: {symbol}"

            # Валидируем данные актива
            is_valid, message = validate_asset(asset_data, symbol)
            if not is_valid:
                return False, f"Invalid asset {symbol}: {message}"

        return True, "Portfolio is valid"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_asset(asset_data: dict, symbol: str) -> Tuple[bool, str]:
    """Валидирует данные актива"""
    try:
        required_fields = ["symbol", "amount", "added_at"]
        for field in required_fields:
            if field not in asset_data:
                return False, f"Missing field: {field}"

        # Проверяем соответствие символа
        if asset_data["symbol"] != symbol:
            return False, f"Symbol mismatch: {asset_data['symbol']} != {symbol}"

        # Проверяем количество
        amount = asset_data["amount"]
        if not isinstance(amount, (int, float)):
            return False, "Amount must be a number"

        # Получаем конфигурацию актива для валидации
        asset = asset_registry.get_asset(symbol)
        if asset:
            if not asset.validate_amount(amount):
                return False, f"Amount {amount} is outside valid range"

        return True, "Asset is valid"

    except Exception as e:
        return False, f"Asset validation error: {str(e)}"


def validate_asset_amount(symbol: str, amount: float) -> Tuple[bool, str]:
    """Валидирует количество актива"""
    try:
        asset = asset_registry.get_asset(symbol)
        if not asset:
            return False, f"Unsupported asset: {symbol}"

        if not isinstance(amount, (int, float)):
            return False, "Amount must be a number"

        if not asset.validate_amount(amount):
            min_amount = asset.config.min_amount
            max_amount = asset.config.max_amount
            return False, f"Amount must be between {min_amount} and {max_amount}"

        return True, "Amount is valid"

    except Exception as e:
        return False, f"Amount validation error: {str(e)}"


def validate_asset_symbol(symbol: str) -> Tuple[bool, str]:
    """Валидирует символ актива"""
    try:
        if not isinstance(symbol, str):
            return False, "Symbol must be a string"

        if not symbol:
            return False, "Symbol cannot be empty"

        if not asset_registry.is_supported(symbol):
            supported = ", ".join(asset_registry.get_supported_symbols())
            return False, f"Unsupported symbol. Supported: {supported}"

        return True, "Symbol is valid"

    except Exception as e:
        return False, f"Symbol validation error: {str(e)}"


def validate_transaction(transaction_data: dict) -> Tuple[bool, str]:
    """Валидирует данные транзакции"""
    try:
        required_fields = ["type", "symbol", "amount", "timestamp"]
        for field in required_fields:
            if field not in transaction_data:
                return False, f"Missing field: {field}"

        # Проверяем тип транзакции
        if transaction_data["type"] not in ["buy", "sell", "transfer"]:
            return False, "Type must be 'buy', 'sell', or 'transfer'"

        # Валидируем символ и количество
        symbol = transaction_data["symbol"]
        amount = transaction_data["amount"]

        is_valid, message = validate_asset_symbol(symbol)
        if not is_valid:
            return False, message

        is_valid, message = validate_asset_amount(symbol, amount)
        if not is_valid:
            return False, message

        return True, "Transaction is valid"

    except Exception as e:
        return False, f"Transaction validation error: {str(e)}"