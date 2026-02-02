# src/bot/bot/portfolio.py
"""
Команды для работы с портфелем: portfolio, add, remove, clear.
"""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from ...database.simple_repo import portfolio_repo
from ...assets.registry import asset_registry
from ...services.price import price_service
from ...services.currency_service import currency_service
from ..helpers.formatters import format_currency, format_portfolio_asset, format_timestamp
from ..helpers.asset_info import get_supported_assets_detailed, get_supported_assets_text
from ..helpers.command_utils import (
    get_user_display_name,
    record_user_activity,
    validate_add_remove_args,
    get_command_usage_examples,
    get_asset_type_from_symbol
)
from ..helpers.messages import get_empty_portfolio_message, get_portfolio_message

logger = logging.getLogger(__name__)


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /portfolio"""
    user = update.effective_user
    record_user_activity(user.id, "portfolio")

    # Получаем портфель пользователя
    portfolio = portfolio_repo.get_or_create_user(user.id, user.username)
    assets = portfolio.get("assets", {})

    if not assets:
        supported_assets = get_supported_assets_text()
        message = get_empty_portfolio_message(
            get_user_display_name(update),
            supported_assets
        )
    else:
        # Получаем текущие цены для активов пользователя
        symbols = list(assets.keys())

        # Используем обновленную функцию get_asset_details_with_prices
        from ..helpers.asset_info import get_asset_details_with_prices
        assets_details = await get_asset_details_with_prices(symbols)

        # Формируем информацию об активах
        assets_info = []
        total_value_usd = 0

        for symbol, asset_data in assets.items():
            amount = asset_data.get("amount", 0)
            asset_detail = assets_details.get(symbol, {})

            # Получаем цены из деталей актива
            price_usd = asset_detail.get("price_usd")
            price_rub = asset_detail.get("price_rub")

            # Если price_rub нет в деталях, но есть price_usd, рассчитываем
            if price_usd and not price_rub:
                price_rub = currency_service.usd_to_rub(price_usd)

            # Используем обновленную функцию format_portfolio_asset с поддержкой RUB
            asset_info = format_portfolio_asset(symbol, amount, price_usd, price_rub)

            # Учитываем стоимость в общей сумме
            if asset_info.get("value_usd"):
                total_value_usd += asset_info["value_usd"]

            assets_info.append(asset_info)

        # Рассчитываем общую стоимость в рублях
        total_value_rub = currency_service.usd_to_rub(total_value_usd)

        # Получаем текущее московское время для отображения времени обновления
        current_time = format_timestamp()

        message = get_portfolio_message(
            get_user_display_name(update),
            assets_info,
            total_value_usd,
            current_time,  # Передаем текущее время вместо времени из базы
            len(assets)
        )

    await update.message.reply_text(message, parse_mode=None)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add"""
    user = update.effective_user
    record_user_activity(user.id, "add")

    # Валидируем аргументы
    is_valid, error_msg, symbol, amount = await validate_add_remove_args(
        context, expected_args=2, command_type="add"
    )

    if not is_valid:
        supported_assets = get_supported_assets_detailed()
        asset_type = get_asset_type_from_symbol(symbol) if symbol else "crypto"
        examples = get_command_usage_examples("add", asset_type)

        message = f"❌ **{error_msg}**\n\n"
        message += f"**Используйте:** `/add <символ> <количество>`\n\n"
        message += f"**Примеры:**\n{examples}\n\n"
        message += f"**Поддерживаемые активы:**\n{supported_assets}"

        await update.message.reply_text(message, parse_mode=None)
        return

    # Добавляем актив
    success, result_msg = portfolio_repo.add_asset(user.id, symbol, amount)

    if success:
        # Получаем информацию об активе и цену
        asset = asset_registry.get_asset(symbol)
        price_data = await price_service.get_price(symbol)

        message = f"✅ **Актив добавлен!**\n\n"
        message += f"**{asset.config.name if asset else symbol.upper()}**\n"
        message += f"Количество: `{asset.format_amount(amount) if asset else amount}`\n"

        if price_data and price_data.price:
            value = amount * price_data.price
            message += f"Текущая цена: {format_currency(price_data.price)}\n"
            message += f"Стоимость: {format_currency(value)}\n"
        else:
            message += f"Цена: ❌ временно недоступна\n"

        # Получаем статистику портфеля
        portfolio = portfolio_repo.get_user_assets(user.id)
        message += f"\n📊 **В вашем портфеле:** {len(portfolio)} актив(ов)\n"
        message += f"💡 Используйте `/portfolio` чтобы увидеть весь портфель"
    else:
        supported_assets = get_supported_assets_text()
        message = f"❌ **Ошибка при добавлении актива**\n\n"
        message += f"{result_msg}\n\n"
        message += f"**Поддерживаемые активы:**\n{supported_assets}"

    await update.message.reply_text(message, parse_mode=None)


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /remove"""
    user = update.effective_user
    record_user_activity(user.id, "remove")

    # Валидируем аргументы
    is_valid, error_msg, symbol, amount = await validate_add_remove_args(
        context, expected_args=1, command_type="remove"
    )

    if not is_valid:
        supported_assets = get_supported_assets_detailed()
        asset_type = get_asset_type_from_symbol(symbol) if symbol else "crypto"
        examples = get_command_usage_examples("remove", asset_type)

        message = f"❌ **{error_msg}**\n\n"
        message += f"**Используйте:** `/remove <символ> [количество]`\n\n"
        message += f"**Примеры:**\n{examples}\n\n"
        message += f"**Поддерживаемые активы:**\n{supported_assets}"

        await update.message.reply_text(message, parse_mode=None)
        return

    # Удаляем актив
    success, result_msg = portfolio_repo.remove_asset(user.id, symbol, amount)

    if success:
        asset = asset_registry.get_asset(symbol)
        message = f"✅ **{result_msg}**\n\n"

        # Проверяем, остались ли активы в портфеле
        portfolio = portfolio_repo.get_user_assets(user.id)
        if portfolio:
            message += f"📊 **Осталось активов:** {len(portfolio)}\n"
            message += f"💡 Используйте `/portfolio` чтобы увидеть обновленный портфель"
        else:
            message += f"📭 **Ваш портфель теперь пуст**\n"
            message += f"💡 Используйте `/add` чтобы добавить новые активы"
    else:
        supported_assets = get_supported_assets_text()
        message = f"❌ **Ошибка при удалении актива**\n\n"
        message += f"{result_msg}\n\n"
        message += f"**Поддерживаемые активы:**\n{supported_assets}"

    await update.message.reply_text(message, parse_mode=None)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear"""
    user = update.effective_user
    record_user_activity(user.id, "clear")

    # Проверяем подтверждение
    if not context.args or context.args[0].lower() != "confirm":
        message = "⚠️ **Внимание!**\n\n"
        message += "Эта команда полностью очистит ваш портфель.\n"
        message += "Все активы будут удалены без возможности восстановления.\n\n"
        message += "Для подтверждения введите:\n"
        message += "`/clear confirm`"

        await update.message.reply_text(message, parse_mode=None)
        return

    # Получаем текущий портфель
    portfolio = portfolio_repo.get_user_assets(user.id)

    if not portfolio:
        message = "📭 **Ваш портфель уже пуст**\n\n"
        message += "Нечего очищать!"

        await update.message.reply_text(message, parse_mode=None)
        return

    # Удаляем все активы
    cleared_count = 0
    for symbol in list(portfolio.keys()):
        success, _ = portfolio_repo.remove_asset(user.id, symbol, None)
        if success:
            cleared_count += 1

    message = f"🧹 **Портфель очищен**\n\n"
    message += f"Удалено активов: {cleared_count}\n"
    message += f"Теперь ваш портфель пуст.\n\n"
    message += f"💡 Используйте `/add` чтобы добавить новые активы."

    await update.message.reply_text(message, parse_mode=None)