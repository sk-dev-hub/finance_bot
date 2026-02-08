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

    # Инициализируем CurrencyService если еще не инициализирован
    if not hasattr(currency_service, '_initialized') or not currency_service._initialized:
        await currency_service.initialize()

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
            source_line = f"Источник: {active_sources[0]}"
        else:
            source_line = f"Источники: {', '.join(active_sources)}"
    else:
        source_line = "Источники: CoinGecko API, Binance API"

    # Получаем текущее московское время
    formatted_time = format_timestamp()

    # Сортируем по популярности
    preferred_order = ["btc", "eth", "ton", "usdt", "sol"]
    sorted_symbols = sorted(
        symbols,
        key=lambda x: (preferred_order.index(x) if x in preferred_order else 999, x)
    )

    # Получаем текущий курс USD/RUB один раз (асинхронно)
    current_usd_rub_rate = await currency_service.get_real_usd_rub_rate()

    # ======================== БЛОК ДЛЯ ДРАГОЦЕННЫХ МЕТАЛЛОВ ========================

    # Получаем цены на драгоценные металлы из cbr_metals_service
    from src.services.cbr_metals_service import metal_service

    metals_message = ""
    try:
        # Получаем последние цены на металлы
        metal_prices = await metal_service.get_latest_prices()

        if metal_prices:
            latest_metal_price = metal_prices[0]  # Самая актуальная запись

            metals_message += "\n🥇 Драгоценные металлы (ЦБ РФ)\n"
            metals_message += f"Дата: {latest_metal_price.date.strftime('%d.%m.%Y')}\n\n"

            # Золото
            gold_price_rub = latest_metal_price.gold
            # Конвертируем золото из RUB в USD
            gold_price_usd = gold_price_rub / current_usd_rub_rate if current_usd_rub_rate else None

            metals_message += f"🥇 Золото (за 1 грамм)\n"
            metals_message += f"   RUB: {latest_metal_price.format_price('gold')} ₽"
            if gold_price_usd:
                metals_message += f" | USD: ${gold_price_usd:,.2f}\n"
            else:
                metals_message += "\n"

            # Серебро
            silver_price_rub = latest_metal_price.silver
            # Конвертируем серебро из RUB в USD
            silver_price_usd = silver_price_rub / current_usd_rub_rate if current_usd_rub_rate else None

            metals_message += f"🥈 Серебро (за 1 грамм)\n"
            metals_message += f"   RUB: {latest_metal_price.format_price('silver')} ₽"
            if silver_price_usd:
                metals_message += f" | USD: ${silver_price_usd:,.4f}\n"
            else:
                metals_message += "\n"

            metals_message += "─" * 30 + "\n\n"
        else:
            metals_message += "\n⚠️ Драгоценные металлы:\n"
            metals_message += "   Цены временно недоступны\n"
            metals_message += "─" * 30 + "\n\n"

    except Exception as e:
        logger.error(f"Ошибка получения цен на металлы: {e}")
        metals_message += "\n⚠️ Драгоценные металлы:\n"
        metals_message += "   Ошибка получения данных\n"
        metals_message += "─" * 30 + "\n\n"

    # ======================== КОНЕЦ БЛОКА ДЛЯ ДРАГОЦЕННЫХ МЕТАЛЛОВ ========================

    # Формируем сообщение
    message = "📈 Текущие цены криптовалют\n\n"

    for symbol in sorted_symbols:
        info = assets_info.get(symbol, {})
        emoji = info.get("emoji", "•")
        name = info.get("name", symbol.upper())
        price_usd = info.get("price_usd")
        price_rub = info.get("price_rub")
        change = info.get("change_24h")

        message += f"{emoji} {name} ({symbol.upper()})\n"

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
                # Асинхронная конвертация
                price_rub = await currency_service.usd_to_rub(price_usd)

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
        message += f"   Пример: /add {symbol} {example}\n\n"

    message += "─" * 30 + "\n"

    # Добавляем блок с металлами
    message += metals_message

    message += "💡 Подсказки:\n"
    message += "• /add <символ> <количество> — добавить актив\n"
    message += "• /portfolio — посмотреть портфель\n"
    message += "• /stats — статистика бота\n"
    message += "• /metals — подробнее о металлах\n\n"

    # Время обновления и источники
    message += f"🔄 Обновлено: {formatted_time}\n"
    message += f"{source_line}\n"

    # Асинхронный вывод курса
    one_usd_in_rub = current_usd_rub_rate  # уже есть курс
    message += f"Курс RUB: 1 USD = {currency_service.format_rub(one_usd_in_rub)}"

    await update.message.reply_text(message, parse_mode=None)


# Измененный метод stats_command в price.py
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

    # Инициализируем CurrencyService если нужно
    if not hasattr(currency_service, '_initialized') or not currency_service._initialized:
        await currency_service.initialize()

    # Получаем курс USD/RUB асинхронно
    usd_rub_rate = await currency_service.get_real_usd_rub_rate()
    usd_rub_formatted = currency_service.format_rub(usd_rub_rate)

    # Формируем сообщение
    message = "📊 Статистика бота\n\n"

    # Статистика активов
    all_assets = asset_registry.get_all_assets()
    crypto_count = len(asset_registry.get_crypto_assets())
    fiat_count = len(asset_registry.get_fiat_assets())
    metals_count = len(asset_registry.get_precious_metal_assets())
    commodities_count = len(asset_registry.get_commodity_assets())
    receivables_count = len(asset_registry.get_receivable_assets())
    etf_count = len(asset_registry.get_etf_assets())

    message += "💎 Активы:\n"
    message += f"• Всего активов: {len(all_assets)}\n"
    message += f"• Криптовалюты: {crypto_count}\n"
    message += f"• Фиатные валюты: {fiat_count}\n"
    message += f"• Драгоценные металлы: {metals_count}\n"
    message += f"• Товары: {commodities_count}\n"
    message += f"• Дебиторка: {receivables_count}\n"
    message += f"• ETF: {etf_count}\n\n"

    # Популярные активы
    message += "🌟 Популярные активы:\n"

    # Получаем информацию о популярных активах
    popular_symbols = ["btc", "eth", "ton", "usdt", "sol"]
    try:
        from ..helpers.asset_info import get_asset_details_with_prices
        popular_info = await get_asset_details_with_prices(popular_symbols)

        for symbol in popular_symbols:
            info = popular_info.get(symbol, {})
            name = info.get("name", symbol.upper())
            emoji = info.get("emoji", "•")
            price_usd = info.get("price_usd")

            if price_usd is not None:
                # Асинхронная конвертация
                price_rub = await currency_service.usd_to_rub(price_usd)
                rub_formatted = currency_service.format_rub(price_rub)
                message += f"• {emoji} {name}: ${price_usd:,.4f} | {rub_formatted}\n"
            else:
                message += f"• {emoji} {name}: ❌ недоступно\n"
    except Exception as e:
        # Fallback если не удалось получить цены
        for symbol in popular_symbols:
            asset = asset_registry.get_asset(symbol)
            if asset:
                message += f"• {asset.config.emoji} {asset.config.name}\n"

    message += "\n"

    message += "🔄 Система:\n"
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

    # Показываем оба курса USD/RUB (ЦБ и реальный)
    cbr_rate = currency_service.get_cbr_usd_rub_rate_sync()
    real_rate = currency_service.get_real_usd_rub_rate_sync()

    message += f"• Курс USD/RUB (ЦБ): {currency_service.format_rub(cbr_rate)}\n"
    message += f"• Курс USD/RUB (реальный): {currency_service.format_rub(real_rate)}\n"

    # Информация о CurrencyService
    if currency_service.last_update:
        last_update_str = currency_service.last_update.strftime("%d.%m.%Y %H:%M")
        message += f"• Курсы обновлены: {last_update_str}\n"

    message += f"• Московское время: {formatted_time}\n\n"

    message += "📈 Команды:\n"
    message += "• /coins — список криптовалют\n"
    message += "• /currencies — список валют\n"
    message += "• /metals — драгоценные металлы\n"
    message += "• /prices — текущие цены\n"
    message += "• /portfolio — ваш портфель\n\n"

    message += "💡 Статистика обновляется в реальном времени"

    await update.message.reply_text(message, parse_mode=None)