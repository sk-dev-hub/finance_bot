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
    get_receivables_assets_message,
    get_etf_assets_message
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

    # Получаем актуальные цены на металлы из ЦБ РФ ОДИН раз
    from ...services.cbr_metals_service import metal_service
    from ...services.currency_service import currency_service

    await currency_service.initialize()
    usd_to_rub_rate = currency_service.get_real_usd_rub_rate_sync()

    metal_prices_info = {}
    metal_date = ""

    try:
        metal_prices = await metal_service.get_latest_prices()
        if metal_prices:
            latest_metal_price = metal_prices[0]
            metal_date = latest_metal_price.date.strftime('%d.%m.%Y')

            # Заполняем цены для базовых металлов
            for metal_symbol in ["gold", "silver", "platinum", "palladium"]:
                price_rub = getattr(latest_metal_price, metal_symbol, None)
                if price_rub:
                    price_usd = price_rub / usd_to_rub_rate if usd_to_rub_rate > 0 else None
                    metal_prices_info[metal_symbol] = {
                        "price_usd": price_usd,
                        "price_rub": price_rub,
                        "date": metal_date
                    }
    except Exception as e:
        logger.error(f"Error getting metal prices: {e}")

    # Формируем полный prices_info для всех активов
    symbols = [asset.symbol for asset in precious_metals]
    prices_info = {}

    for symbol in symbols:
        # Для базовых металлов используем цены из ЦБ РФ
        if symbol in ["gold", "silver", "platinum", "palladium"]:
            if symbol in metal_prices_info:
                prices_info[symbol] = metal_prices_info[symbol]
            else:
                # Если нет цены, используем стандартный метод
                asset_prices = await get_asset_details_with_prices([symbol])
                if symbol in asset_prices:
                    prices_info[symbol] = asset_prices[symbol]

        # Для монет используем get_asset_details_with_prices
        # (он уже будет использовать обновленные calculate_price)
        else:
            asset_prices = await get_asset_details_with_prices([symbol])
            if symbol in asset_prices:
                prices_info[symbol] = asset_prices[symbol]

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
            "❌ Нет доступных ETF\nETF еще не добавлены.",
            parse_mode=None
        )
        return

    # Получаем цены
    symbols = [asset.symbol for asset in etf_assets]
    prices_info = await get_asset_details_with_prices(symbols)

    # Используем нашу новую функцию
    message = get_etf_assets_message(etf_assets, prices_info)

    await update.message.reply_text(message, parse_mode=None)