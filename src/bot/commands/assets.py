# src/bot/bot/assets.py
"""
Команды для работы с активами: coins, currencies, metals, products, receivables, assets.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...assets.registry import asset_registry
from ...services.price import price_service
from ... services.currency_service import currency_service
from ..helpers.asset_info import (
    get_crypto_assets,
    get_fiat_assets,
    get_precious_metal_assets,
    get_commodity_assets,
    get_receivable_assets,
    generate_asset_list_message,
    get_asset_details_with_prices
)
from ..helpers.command_utils import record_user_activity, get_user_display_name
from ..helpers.messages import (
    get_crypto_assets_message,
    get_fiat_assets_message,
    get_metals_assets_message,
    get_products_assets_message,
    get_receivables_assets_message
)

logger = logging.getLogger(__name__)


async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /coins - показывает список криптовалют"""
    user = update.effective_user
    record_user_activity(user.id, "coins")

    crypto_assets = asset_registry.get_crypto_assets()

    # Получаем цены для крипто активов
    symbols = [asset.symbol for asset in crypto_assets]
    from ..helpers.asset_info import get_asset_details_with_prices
    prices_info = await get_asset_details_with_prices(symbols)

    # Используем обновленную функцию с prices_info
    message = get_crypto_assets_message(crypto_assets, prices_info)

    await update.message.reply_text(message, parse_mode=None)


async def currencies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /currencies - список валют"""
    user = update.effective_user
    record_user_activity(user.id, "currencies")

    # ПРИНУДИТЕЛЬНО обновляем курсы перед показом
    await currency_service.update_rates_from_cbr()

    fiat_assets = asset_registry.get_fiat_assets()

    # Получаем цены для фиатных валют
    symbols = [asset.symbol for asset in fiat_assets]
    from ..helpers.asset_info import get_asset_details_with_prices
    prices_info = await get_asset_details_with_prices(symbols)

    message = get_fiat_assets_message(fiat_assets, prices_info)

    await update.message.reply_text(message, parse_mode=None)

async def metals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /metals - показывает драгоценные металлы"""
    user = update.effective_user
    record_user_activity(user.id, "metals")

    precious_metals = get_precious_metal_assets()

    if not precious_metals:
        await update.message.reply_text(
            "❌ **Нет доступных драгоценных металлов**\n\nПожалуйста, попробуйте позже.",
            parse_mode=None
        )
        return

    symbols = [asset.symbol for asset in precious_metals]
    prices_info = await get_asset_details_with_prices(symbols)

    message = get_metals_assets_message(precious_metals, prices_info)

    await update.message.reply_text(message, parse_mode=None)


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /products - показывает товары"""
    user = update.effective_user
    record_user_activity(user.id, "products")

    commodities = get_commodity_assets()
    message = get_products_assets_message(commodities)

    await update.message.reply_text(message, parse_mode=None)


async def receivables_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /receivables - показывает дебиторскую задолженность"""
    user = update.effective_user
    record_user_activity(user.id, "receivables")

    receivables = get_receivable_assets()
    message = get_receivables_assets_message(receivables)

    await update.message.reply_text(message, parse_mode=None)


async def assets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /assets - альтернативное название для /coins"""
    await coins_command(update, context)


async def etfs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /etfs - показывает ETF"""
    user = update.effective_user
    record_user_activity(user.id, "etfs")

    etf_assets = asset_registry.get_etf_assets()

    if not etf_assets:
        await update.message.reply_text(
            "❌ **Нет доступных ETF**\n\nETF еще не добавлены.",
            parse_mode=None
        )
        return

    # Получаем цены
    symbols = [asset.symbol for asset in etf_assets]
    prices_info = await get_asset_details_with_prices(symbols)

    message = "📊 **Доступные ETF:**\n\n"

    for asset in etf_assets:
        price_info = prices_info.get(asset.symbol, {})

        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Символ: `{asset.symbol.upper()}`\n"

        if price_info.get("price"):
            price = price_info["price"]
            message += f"   Цена: {price:,.2f} ₽\n"  # FXGD торгуется в рублях

        # Получаем дополнительную информацию для ETF
        if hasattr(asset, 'get_etf_info'):
            etf_info = asset.get_etf_info()
            if etf_info.get('expense_ratio'):
                message += f"   Комиссия: {etf_info['expense_ratio']:.2f}%\n"

        message += f"   Пример: `/add {asset.symbol} 10`\n\n"

    message += "─" * 30 + "\n"
    message += "📝 **О ETF FXGD:**\n"
    message += "• Торгуется на Московской бирже\n"
    message += "• Каждая акция соответствует 0.1 грамма золота\n"
    message += "• Комиссия управления: 0.45% годовых\n"
    message += "• Валюта торгов: Российский рубль (₽)\n\n"
    message += "💡 **Как использовать:**\n"
    message += "1. `/add fxgd 10` — купить 10 акций FXGD\n"
    message += "2. `/portfolio` — посмотреть в портфеле\n"
    message += "3. `/remove fxgd 5` — продать 5 акций\n\n"
    message += "_Данные с Yahoo Finance, обновляются в реальном времени_"

    await update.message.reply_text(message, parse_mode=None)