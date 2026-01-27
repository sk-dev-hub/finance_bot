# src/bot/helpers/command_utils.py
"""
Утилиты для обработки команд.
"""

from typing import Tuple, Optional
from telegram import Update
from telegram.ext import ContextTypes

from ...database.simple_user_repo import user_repo
from ...assets.registry import asset_registry


def get_user_display_name(update: Update) -> str:
    """Получает отображаемое имя пользователя"""
    user = update.effective_user
    if user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    else:
        return "инвестор"


def record_user_activity(user_id: int, command: str):
    """Записывает активность пользователя"""
    user_repo.record_user_activity(user_id, command)


async def validate_add_remove_args(
        context: ContextTypes.DEFAULT_TYPE,
        expected_args: int = 2,
        command_type: str = "add"
) -> Tuple[bool, Optional[str], Optional[str], Optional[float]]:
    """
    Валидирует аргументы команд add/remove.

    Returns:
        Tuple[is_valid, error_message, symbol, amount]
    """
    args = context.args

    if command_type == "add" and len(args) != expected_args:
        return False, "Неправильный формат команды", None, None

    if command_type == "remove" and not (1 <= len(args) <= 2):
        return False, "Неправильный формат команды", None, None

    symbol = args[0].lower() if args else None

    amount = None
    if len(args) > 1:
        try:
            amount = float(args[1])
            if amount <= 0:
                return False, "Количество должно быть больше 0", None, None
        except ValueError:
            return False, "Некорректное количество", None, None

    return True, None, symbol, amount


def get_command_usage_examples(command: str, asset_type: str = "crypto") -> str:
    """Возвращает примеры использования команды"""
    examples = {
        "add": {
            "crypto": [
                "`/add btc 0.5` — добавить 0.5 BTC",
                "`/add eth 2.0` — добавить 2 ETH",
                "`/add ton 100` — добавить 100 TON"
            ],
            "fiat": [
                "`/add rub 10000` — добавить 10,000 рублей",
                "`/add eur 500` — добавить 500 евро"
            ],
            "precious_metal": [
                "`/add gold_coin_7_78 2` — добавить 2 золотые монеты",
                "`/add silver_coin_31_1 5` — добавить 5 серебряных монет"
            ],
            "commodity": [
                "`/add product_1 5` — добавить 5 единиц Товара 1"
            ],
            "receivable": [
                "`/add receivable_ecm 50000` — добавить дебиторку $50,000"
            ]
        },
        "remove": {
            "crypto": [
                "`/remove btc` — удалить весь BTC",
                "`/remove eth 1.0` — удалить 1 ETH",
                "`/remove ton 50` — удалить 50 TON"
            ],
            "default": [
                "`/remove <символ>` — удалить весь актив",
                "`/remove <символ> <количество>` — удалить часть актива"
            ]
        }
    }

    if command in examples and asset_type in examples[command]:
        return "\n".join(examples[command][asset_type])
    elif command in examples and "default" in examples[command]:
        return "\n".join(examples[command]["default"])

    return ""


def get_asset_type_from_symbol(symbol: str) -> str:
    """Определяет тип актива по символу"""
    asset = asset_registry.get_asset(symbol)

    if asset:
        asset_type = asset.asset_type.value
        type_map = {
            "crypto": "crypto",
            "fiat": "fiat",
            "precious_metal": "precious_metal",
            "commodity": "commodity",
            "receivable": "receivable"
        }
        return type_map.get(asset_type, "crypto")

    # Эвристика по символу
    if symbol in ["btc", "eth", "ton", "usdt", "sol"]:
        return "crypto"
    elif symbol in ["rub", "eur", "usd", "cny"]:
        return "fiat"
    elif "gold" in symbol or "silver" in symbol:
        return "precious_metal"
    elif "product" in symbol:
        return "commodity"
    elif "receivable" in symbol:
        return "receivable"

    return "crypto"