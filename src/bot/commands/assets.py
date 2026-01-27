# src/bot/bot/assets.py
"""
Команды для работы с активами: coins, currencies, metals, products, receivables, assets.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...assets.registry import asset_registry
from ...services.price import price_service
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

    crypto_assets = get_crypto_assets()
    message = get_crypto_assets_message(crypto_assets)

    await update.message.reply_text(message, parse_mode=None)


async def currencies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /currencies - показывает список фиатных валют"""
    user = update.effective_user
    record_user_activity(user.id, "currencies")

    fiat_assets = get_fiat_assets()
    symbols = [asset.symbol for asset in fiat_assets]
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