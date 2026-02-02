# src/bot/helpers/asset_info.py
"""
Функции для получения информации об активах.
"""

import logging
from typing import List, Dict, Any
from src.assets.registry import asset_registry
from src.services.price import price_service
from src.services.currency_service import currency_service

logger = logging.getLogger(__name__)

def get_crypto_assets() -> List[Any]:
    """Получает список криптоактивов"""
    return asset_registry.get_crypto_assets()


def get_fiat_assets() -> List[Any]:
    """Получает список фиатных валют"""
    return asset_registry.get_fiat_assets()


def get_precious_metal_assets() -> List[Any]:
    """Получает список драгоценных металлов"""
    return asset_registry.get_precious_metal_assets()


def get_commodity_assets() -> List[Any]:
    """Получает список товаров"""
    return asset_registry.get_commodity_assets()


def get_receivable_assets() -> List[Any]:
    """Получает список дебиторской задолженности"""
    return asset_registry.get_receivable_assets()


def get_all_assets() -> List[Any]:
    """Получает список всех активов"""
    return asset_registry.get_all_assets()


def get_supported_assets_text() -> str:
    """Возвращает текст со списком поддерживаемых активов"""
    assets = get_all_assets()

    if not assets:
        return "На данный момент нет доступных активов."

    text = ""
    for asset in assets:
        text += f"{asset.display_name}\n"

    return text


def get_supported_assets_detailed() -> str:
    """Возвращает детальный список активов с примерами"""
    assets = get_all_assets()

    if not assets:
        return "На данный момент нет доступных активов."

    text = ""
    for asset in assets:
        text += f"{asset.display_name}\n"

        # Пример количества в зависимости от типа актива
        if asset.asset_type.value == "crypto":
            if asset.symbol == "btc":
                example = "0.01"
            elif asset.symbol == "eth":
                example = "0.1"
            elif asset.symbol == "ton":
                example = "10"
            elif asset.symbol == "usdt":
                example = "100"
            elif asset.symbol == "sol":
                example = "1.0"
            else:
                example = "1.0"
        else:
            example = "1.0"

        text += f"   Пример: `/add {asset.symbol} {example}`\n\n"

    return text


async def get_asset_details_with_prices(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Получает детальную информацию об активах с ценами"""
    prices_result = await price_service.get_prices(symbols)
    assets_info = {}


    for symbol in symbols:
        asset = asset_registry.get_asset(symbol)
        price_data = prices_result.get(symbol)


        if asset:
            price_usd = price_data.price if price_data else None
            source = price_data.source if price_data else None

            # Рассчитываем стоимость в рублях
            price_rub = None
            if price_usd is not None:
                price_rub = currency_service.usd_to_rub(price_usd)

            info = {
                "emoji": asset.config.emoji,
                "name": asset.config.name,
                "symbol": asset.symbol,
                "price_usd": price_usd,
                "price_rub": price_rub,
                "source": source,  # Добавляем источник цены
                "change_24h": getattr(price_data, 'change_24h', None) if price_data else None
            }

            # Добавляем специфичную информацию
            if hasattr(asset, 'get_metal_info'):
                info["metal_info"] = asset.get_metal_info()
            elif asset.asset_type.value == "receivable":
                discount = getattr(asset, 'discount_factor', {}).get(asset.symbol, 1.0)
                info["discount"] = (1 - discount) * 100

            assets_info[symbol] = info

    return assets_info


def generate_asset_list_message(
        assets: List[Any],
        title: str,
        asset_type: str = "crypto"
) -> str:
    """Генерирует сообщение со списком активов"""
    if not assets:
        return f"❌ **{title} не поддерживаются.**\n\n"

    message = f"**{title}:**\n\n"

    for asset in assets:
        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Код: `{asset.symbol.upper() if asset_type in ['crypto', 'fiat'] else asset.symbol}`\n"

        # Пример добавления
        example_amount = _get_example_amount(asset.symbol, asset_type)
        message += f"   Пример: `/add {asset.symbol} {example_amount}`\n\n"

    return message


def _get_example_amount(symbol: str, asset_type: str) -> str:
    """Возвращает примерное количество для актива"""
    examples = {
        "crypto": {
            "btc": "0.01",
            "eth": "0.1",
            "ton": "10",
            "usdt": "100",
            "sol": "1.0",
            "default": "1.0"
        },
        "fiat": {
            "rub": "1000",
            "eur": "100",
            "usd": "100",
            "default": "100"
        },
        "precious_metal": {
            "gold": "1",
            "silver": "1",
            "default": "1"
        },
        "commodity": {
            "default": "10"
        },
        "receivable": {
            "default": "50000"
        }
    }

    if asset_type in examples:
        for key in [symbol, "default"]:
            if key in examples[asset_type]:
                return examples[asset_type][key]

    return "1.0"