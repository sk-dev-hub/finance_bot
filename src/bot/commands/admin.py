# src/bot/bot/admin.py
"""
Административные команды бота.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...assets.registry import asset_registry
from ...services.price import price_service
from ...database.simple_user_repo import user_repo
from ..helpers.command_utils import record_user_activity

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    # Здесь можно добавить проверку по ID или другим критериям
    admin_ids = [123456789]  # Замените на реальные ID администраторов
    return user_id in admin_ids


# src/bot/bot/admin.py
async def update_product_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /update_product_price - обновляет цену товара"""
    user = update.effective_user
    record_user_activity(user.id, "update_product_price")

    # Проверяем права администратора
    if not is_admin(user.id):
        await update.message.reply_text(
            "❌ Доступ запрещен\n\nЭта команда только для администраторов.",
            parse_mode=None
        )
        return

    # Проверяем аргументы
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Неправильный формат\n\n"
            "Используйте: /update_product_price <код_товара> <цена>\n"
            "Примеры:\n"
            "/update_product_price product_1 120.5\n"
            "/update_product_price product_2 300",
            parse_mode=None
        )
        return

    product_code = context.args[0].lower()

    try:
        new_price = float(context.args[1])
        if new_price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Некорректная цена\n\n"
            "Цена должна быть положительным числом.",
            parse_mode=None
        )
        return

    # Проверяем существование товара
    asset = asset_registry.get_asset(product_code)
    if not asset:
        await update.message.reply_text(
            f"❌ Товар не найден\n\n"
            f"Товар с кодом {product_code} не существует.",
            parse_mode=None
        )
        return

    # Проверяем что это товар
    if asset.asset_type.value != "commodity":
        await update.message.reply_text(
            f"❌ Не товар\n\n"
            f"{asset.config.name} не является товаром.",
            parse_mode=None
        )
        return

    # Обновляем цену в настройках
    from src.config.settings import settings
    if product_code in settings.PRODUCTS_PRICES:
        old_price = settings.PRODUCTS_PRICES[product_code]
        settings.PRODUCTS_PRICES[product_code] = new_price

        # Очищаем кэш цен
        price_service.clear_cache()

        await update.message.reply_text(
            f"✅ Цена обновлена\n\n"
            f"Товар: {asset.config.name}\n"
            f"Старая цена: {currency_service.format_rub(old_price)}\n"
            f"Новая цена: {currency_service.format_rub(new_price)}\n\n"
            f"💡 Используйте /products чтобы увидеть изменения.",
            parse_mode=None
        )
    else:
        await update.message.reply_text(
            f"❌ Ошибка\n\n"
            f"Не удалось обновить цену для {product_code}.",
            parse_mode=None
        )


async def update_metal_prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /update_metal_prices - обновляет цены на металлы"""
    user = update.effective_user
    record_user_activity(user.id, "update_metal_prices")

    # Проверяем права администратора
    if not is_admin(user.id):
        await update.message.reply_text(
            "❌ **Доступ запрещен**\n\nЭта команда только для администраторов.",
            parse_mode=None
        )
        return

    # Проверяем аргументы
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ **Неправильный формат команды**\n\n"
            "Используйте: `/update_metal_prices <металл> <цена>`\n"
            "Примеры:\n"
            "`/update_metal_prices gold 65.5` — установить цену золота $65.5/г\n"
            "`/update_metal_prices silver 0.88` — установить цену серебра $0.88/г",
            parse_mode=None
        )
        return

    metal_type = context.args[0].lower()

    try:
        price = float(context.args[1])
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ **Некорректная цена**\n\n"
            "Цена должна быть положительным числом.",
            parse_mode=None
        )
        return

    # Обновляем цены у всех активов из драгметаллов
    updated_count = 0
    precious_metals = asset_registry.get_precious_metal_assets()

    for asset in precious_metals:
        if hasattr(asset, 'update_metal_price'):
            # Проверяем тип металла
            if metal_type == "gold" and "gold" in asset.symbol:
                asset.update_metal_price("gold", price)
                updated_count += 1
            elif metal_type == "silver" and "silver" in asset.symbol:
                asset.update_metal_price("silver", price)
                updated_count += 1

    # Очищаем кэш цен
    price_service.clear_cache()

    await update.message.reply_text(
        f"✅ **Цены обновлены**\n\n"
        f"Установлена цена {metal_type}: ${price:.2f} за грамм\n"
        f"Обновлено активов: {updated_count}\n\n"
        f"💡 Используйте `/portfolio` чтобы увидеть новые стоимости.",
        parse_mode=None
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats - статистика бота"""
    user = update.effective_user
    record_user_activity(user.id, "stats")

    # Получаем статистику
    user_stats = user_repo.get_user_statistics()

    # Формируем сообщение
    message = "📊 **Статистика бота**\n\n"

    message += "**👥 Пользователи:**\n"
    message += f"• Всего пользователей: {user_stats.get('total_users', 0)}\n"
    message += f"• Активных (30 дней): {user_stats.get('active_users', 0)}\n"
    message += f"• Premium: {user_stats.get('premium_users', 0)}\n\n"

    message += "💎 **Активы:**\n"
    message += f"• Поддерживается: {len(asset_registry.get_all_assets())} активов\n\n"

    message += "🔄 **Система:**\n"
    message += f"• Статус: ✅ Работает\n\n"

    message += "💡 _Статистика обновляется в реальном времени_"

    await update.message.reply_text(message, parse_mode=None)