# src/bot/bot/price.py
"""
Команды для работы с ценами: prices, stats.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...assets.registry import asset_registry
from ...services.price import price_service
from ..helpers.asset_info import get_asset_details_with_prices
from ..helpers.command_utils import record_user_activity
from ..helpers.formatters import format_currency, format_percentage

logger = logging.getLogger(__name__)


async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /prices"""
    user = update.effective_user
    record_user_activity(user.id, "prices")

    crypto_assets = asset_registry.get_crypto_assets()
    symbols = [asset.symbol for asset in crypto_assets]

    # Получаем информацию об активах с ценами
    assets_info = await get_asset_details_with_prices(symbols)

    # Сортируем по популярности
    preferred_order = ["btc", "eth", "ton", "usdt", "sol"]
    sorted_symbols = sorted(
        symbols,
        key=lambda x: (preferred_order.index(x) if x in preferred_order else 999, x)
    )

    # Формируем сообщение
    message = "📈 **Текущие цены криптовалют**\n\n"

    for symbol in sorted_symbols:
        info = assets_info.get(symbol, {})
        emoji = info.get("emoji", "•")
        name = info.get("name", symbol.upper())
        price = info.get("price")
        change = info.get("change_24h")

        message += f"{emoji} **{name} ({symbol.upper()})**\n"

        if price:
            # Форматируем цену в зависимости от стоимости
            if symbol in ["btc", "eth"]:
                price_formatted = format_currency(price)
            elif symbol in ["ton", "sol"]:
                price_formatted = f"${price:,.4f}"
            elif symbol == "usdt":
                price_formatted = f"${price:.2f}"
            else:
                price_formatted = f"${price:,.4f}"

            message += f"   Цена: {price_formatted}\n"

            # Добавляем изменение за 24ч
            if change is not None:
                change_emoji = "📈" if change >= 0 else "📉"
                message += f"   24ч: {change_emoji} {format_percentage(change)}\n"
        else:
            message += f"   Цена: ❌ временно недоступна\n"

        message += "\n"

    message += "─" * 30 + "\n"
    message += "💡 **Подсказки:**\n"
    message += "• Используйте `/add <символ> <количество>` чтобы купить\n"
    message += "• Используйте `/portfolio` чтобы увидеть свой портфель\n\n"
    message += "_Цены обновляются каждую минуту_\n"
    message += "_Источник: CoinGecko API_"

    await update.message.reply_text(message, parse_mode=None)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats - статистика бота"""
    user = update.effective_user
    record_user_activity(user.id, "stats")

    # Формируем сообщение
    message = "📊 **Статистика бота**\n\n"

    # Статистика активов
    all_assets = asset_registry.get_all_assets()
    crypto_count = len(asset_registry.get_crypto_assets())
    fiat_count = len(asset_registry.get_fiat_assets())
    metals_count = len(asset_registry.get_precious_metal_assets())
    commodities_count = len(asset_registry.get_commodity_assets())
    receivables_count = len(asset_registry.get_receivable_assets())

    message += "💎 **Активы:**\n"
    message += f"• Всего активов: {len(all_assets)}\n"
    message += f"• Криптовалюты: {crypto_count}\n"
    message += f"• Фиатные валюты: {fiat_count}\n"
    message += f"• Драгоценные металлы: {metals_count}\n"
    message += f"• Товары: {commodities_count}\n"
    message += f"• Дебиторка: {receivables_count}\n\n"

    # Популярные активы
    message += "🌟 **Популярные активы:**\n"
    popular_assets = ["BTC", "ETH", "TON", "USDT", "SOL"]
    message += f"• {', '.join(popular_assets)}\n\n"

    message += "🔄 **Система:**\n"
    message += f"• Статус: ✅ Работает\n"
    message += f"• Источник цен: CoinGecko API\n"
    message += f"• Обновление цен: каждую минуту\n\n"

    message += "💡 _Статистика обновляется в реальном времени_"

    await update.message.reply_text(message, parse_mode=None)