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
from ..helpers.formatters import format_currency, format_percentage, format_timestamp, format_price_for_asset
from ...services.currency_service import currency_service
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /prices"""
    user = update.effective_user
    record_user_activity(user.id, "prices")

    crypto_assets = asset_registry.get_crypto_assets()
    symbols = [asset.symbol for asset in crypto_assets]

    # Получаем информацию об активах с ценами
    assets_info = await get_asset_details_with_prices(symbols)

    # Анализируем источники цен
    sources_summary = {"coingecko": 0, "binance": 0, "other": 0}
    for info in assets_info.values():
        source = info.get("source")
        if source == "coingecko":
            sources_summary["coingecko"] += 1
        elif source == "binance":
            sources_summary["binance"] += 1
        elif source:
            sources_summary["other"] += 1

    # Формируем строку с источниками
    active_sources = []
    if sources_summary["coingecko"] > 0:
        active_sources.append(f"CoinGecko: {sources_summary['coingecko']}")
    if sources_summary["binance"] > 0:
        active_sources.append(f"Binance: {sources_summary['binance']}")

    if active_sources:
        if len(active_sources) == 1:
            source_line = f"_Источник: {active_sources[0]}_"
        else:
            source_line = f"_Источники: {', '.join(active_sources)}_"
    else:
        source_line = "_Источники: CoinGecko API, Binance API_"

    # Получаем текущее московское время
    formatted_time = format_timestamp()

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
        price_usd = info.get("price_usd")
        price_rub = info.get("price_rub")
        change = info.get("change_24h")

        message += f"{emoji} **{name} ({symbol.upper()})**\n"

        if price_usd is not None:
            # Форматируем цену
            if symbol in ["btc", "eth"]:
                price_usd_formatted = f"${price_usd:,.2f}"
            elif symbol in ["ton", "sol"]:
                price_usd_formatted = f"${price_usd:,.4f}"
            elif symbol == "usdt":
                price_usd_formatted = f"${price_usd:.2f}"
            else:
                price_usd_formatted = f"${price_usd:,.4f}"

            # Цена в рублях
            if price_rub is None:
                price_rub = currency_service.usd_to_rub(price_usd)
            price_rub_formatted = currency_service.format_rub(price_rub)

            message += f"   USD: {price_usd_formatted} | RUB: {price_rub_formatted}\n"

            # Источник для каждого актива
            source = info.get("source")
            if source:
                source_name = "CoinGecko" if source == "coingecko" else "Binance" if source == "binance" else source
                message += f"   Источник: {source_name}\n"

            # Изменение за 24ч
            if change is not None:
                change_emoji = "📈" if change >= 0 else "📉"
                message += f"   24ч: {change_emoji} {format_percentage(change)}\n"
        else:
            message += f"   Цена: ❌ временно недоступна\n"

        # Пример команды
        example_amounts = {
            "btc": "0.01", "eth": "0.1", "ton": "10",
            "usdt": "100", "sol": "1.0"
        }
        example = example_amounts.get(symbol, "1.0")
        message += f"   Пример: `/add {symbol} {example}`\n\n"

    message += "─" * 30 + "\n"
    message += "💡 **Подсказки:**\n"
    message += "• `/add <символ> <количество>` — добавить актив\n"
    message += "• `/portfolio` — посмотреть портфель\n"
    message += "• `/stats` — статистика бота\n\n"

    # Время обновления и источники
    message += f"🔄 Обновлено: {formatted_time}\n"
    message += f"{source_line}\n"
    message += f"_Курс RUB: 1 USD = {currency_service.format_rub(currency_service.usd_to_rub(1))}_"

    await update.message.reply_text(message, parse_mode=None)


# src/bot/bot/price.py
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats - статистика бота"""
    user = update.effective_user
    record_user_activity(user.id, "stats")

    # Получаем статистику по источникам из сервиса цен
    sources_stats = price_service.get_price_sources_stats()

    # Определяем активный источник на основе статистики
    active_source = "не определен"
    if sources_stats:
        # Находим источник с максимальным количеством запросов
        max_source = max(sources_stats.items(), key=lambda x: x[1])
        source, count = max_source

        if source == "coingecko":
            active_source = f"CoinGecko API ({count} запросов)"
        elif source == "binance":
            active_source = f"Binance API ({count} запросов)"
        else:
            active_source = f"{source} ({count} запросов)"
    else:
        # Если статистики нет, проверяем конфигурацию первого актива
        crypto_assets = asset_registry.get_crypto_assets()
        if crypto_assets:
            asset = crypto_assets[0]
            if hasattr(asset, 'config') and hasattr(asset.config, 'price_source'):
                source = asset.config.price_source
                if source == "coingecko":
                    active_source = "CoinGecko API (основной)"
                elif source == "binance":
                    active_source = "Binance API (основной)"

    # Получаем текущее московское время
    formatted_time = format_timestamp()

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
    message += f"• Источник цен: {active_source}\n"

    # Добавляем детальную статистику по источникам
    if sources_stats:
        message += f"• Статистика запросов:\n"
        for source, count in sources_stats.items():
            source_name = "CoinGecko" if source == "coingecko" else "Binance" if source == "binance" else source
            message += f"  - {source_name}: {count}\n"
    else:
        message += f"• Статистика: данные еще собираются\n"

    message += f"• Курс USD/RUB: {currency_service.format_rub(currency_service.usd_to_rub(1))}\n"
    message += f"• Московское время: {formatted_time}\n\n"

    message += "💡 _Статистика обновляется в реальном времени_"

    await update.message.reply_text(message, parse_mode=None)