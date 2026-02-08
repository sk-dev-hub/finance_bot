# src/bot/handlers.py
"""
Регистрация всех обработчиков команд.
"""

import logging
from typing import Dict, Callable
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters

from .keyboards import (
    get_main_keyboard,
    get_start_keyboard,
    get_portfolio_actions_keyboard,
    get_quick_actions_keyboard,
    get_cancel_keyboard,
    get_add_asset_keyboard
)
from ..database.simple_user_repo import user_repo
from .helpers.command_utils import record_user_activity, get_user_display_name

logger = logging.getLogger(__name__)


def get_all_commands() -> Dict[str, Callable]:
    """Возвращает словарь всех команд и их обработчиков"""

    from .commands.basic import start_command, help_command, settings_command
    from .commands.portfolio import portfolio_command, add_command, remove_command, clear_command
    from .commands.assets import coins_command, currencies_command, metals_command, products_command, \
        receivables_command, assets_command, etfs_command
    from .commands.price import prices_command, stats_command
    from .commands.admin import stats_command as admin_stats_command, update_product_price_command, \
        update_metal_prices_command

    commands = {
        # Основные команды
        "start": start_command,
        "help": help_command,
        "settings": settings_command,

        # Портфель
        "portfolio": portfolio_command,
        "add": add_command,
        "remove": remove_command,
        "clear": clear_command,

        # Цены и информация
        "prices": prices_command,
        "stats": stats_command,

        # Активы
        "coins": coins_command,
        "currencies": currencies_command,
        "metals": metals_command,
        "products": products_command,
        "receivables": receivables_command,
        "assets": assets_command,
        "etfs": etfs_command,

        # Административные команды (только для админов)
        "admin_stats": admin_stats_command,
        "update_product_price": update_product_price_command,
        "update_metal_prices": update_metal_prices_command,
    }

    logger.info(f"Loaded {len(commands)} command handlers")
    return commands


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения от кнопок клавиатуры"""
    text = update.message.text
    user = update.effective_user

    logger.info(f"User {user.id} sent text: {text}")

    # Регистрируем активность
    record_user_activity(user.id, f"button_{text}")

    # Обрабатываем нажатия на кнопки
    if text == "🚀 Начать":
        # Вызываем команду /start через ее обработчик
        from .commands.basic import start_command
        await start_command(update, context)

    elif text == "📊 Портфель":
        from .commands.portfolio import portfolio_command
        await portfolio_command(update, context)

    elif text == "📈 Цены":
        from .commands.price import prices_command
        await prices_command(update, context)

    elif text == "💰 Крипто":
        from .commands.assets import coins_command
        await coins_command(update, context)

    elif text == "💵 Валюты":
        from .commands.assets import currencies_command
        await currencies_command(update, context)

    elif text == "🥇 Металлы":
        from .commands.assets import metals_command
        await metals_command(update, context)

    elif text == "📦 Товары":
        from .commands.assets import products_command
        await products_command(update, context)

    elif text == "⚙️ Настройки":
        from .commands.basic import settings_command
        await settings_command(update, context)

    elif text == "📋 Помощь":
        from .commands.basic import help_command
        await help_command(update, context)

    elif text == "💼 Активы":
        from .commands.assets import assets_command
        await assets_command(update, context)

    elif text == "➕ Добавить":
        await update.message.reply_text(
            f"Для добавления актива, {get_user_display_name(update)}!\n\n"
            "Используйте команду:\n"
            "`/add <символ> <количество>`\n\n"
            "📋 **Примеры:**\n"
            "`/add btc 0.1` — добавить 0.1 BTC\n"
            "`/add eth 2.0` — добавить 2 ETH\n"
            "`/add rub 10000` — добавить 10,000 ₽\n\n"
            "Или используйте быстрые кнопки ниже:",
            parse_mode=None,
            reply_markup=get_add_asset_keyboard()
        )

    elif text == "➖ Удалить":
        await update.message.reply_text(
            f"Для удаления актива, {get_user_display_name(update)}!\n\n"
            "Используйте команду:\n"
            "`/remove <символ>` — удалить весь актив\n"
            "`/remove <символ> <количество>` — удалить часть\n\n"
            "📋 **Примеры:**\n"
            "`/remove btc` — удалить весь BTC\n"
            "`/remove eth 1.0` — удалить 1 ETH\n"
            "`/remove rub 5000` — удалить 5000 ₽",
            parse_mode=None,
            reply_markup=get_cancel_keyboard()
        )

    elif text == "🧹 Очистить":
        await update.message.reply_text(
            f"⚠️ **Внимание, {get_user_display_name(update)}!**\n\n"
            "Эта команда полностью очистит ваш портфель.\n"
            "Все активы будут удалены без возможности восстановления.\n\n"
            "Для подтверждения введите:\n"
            "`/clear confirm`\n\n"
            "❌ Для отмены нажмите кнопку ниже:",
            parse_mode=None,
            reply_markup=get_cancel_keyboard()
        )

    elif text == "🔄 Обновить":
        from .commands.portfolio import portfolio_command
        await update.message.reply_text(
            "🔄 Обновляю портфель...",
            parse_mode=None
        )
        await portfolio_command(update, context)

    elif text == "🏠 Главная":
        await update.message.reply_text(
            f"🏠 Возвращаемся в главное меню, {get_user_display_name(update)}!\n\n"
            "Выберите действие:",
            parse_mode=None,
            reply_markup=get_main_keyboard()
        )

    elif text == "❌ Отмена":
        await update.message.reply_text(
            "❌ Действие отменено.\n\n"
            "Возвращаюсь в главное меню...",
            parse_mode=None,
            reply_markup=get_main_keyboard()
        )

    elif text == "🔙 Основное меню":
        await update.message.reply_text(
            "🔙 Возвращаюсь в главное меню...",
            parse_mode=None,
            reply_markup=get_main_keyboard()
        )

    # Обработка быстрых кнопок добавления активов
    elif text.startswith("➕ "):
        # Парсим текст кнопки: "➕ BTC 0.01"
        parts = text.split()
        if len(parts) >= 3:
            symbol = parts[1].lower()  # BTC -> btc
            amount = parts[2]  # 0.01

            # Проверяем корректность количества
            try:
                float_amount = float(amount)
                if float_amount <= 0:
                    raise ValueError

                # Вызываем команду add с аргументами
                context.args = [symbol, amount]
                from .commands.portfolio import add_command

                await update.message.reply_text(
                    f"🔄 Добавляю {amount} {symbol.upper()}...",
                    parse_mode=None
                )
                await add_command(update, context)

            except ValueError:
                await update.message.reply_text(
                    f"❌ Некорректное количество: {amount}\n\n"
                    "Количество должно быть положительным числом.\n"
                    "Пример правильного формата: `➕ BTC 0.01`",
                    parse_mode=None,
                    reply_markup=get_add_asset_keyboard()
                )
        else:
            await update.message.reply_text(
                "❌ Неправильный формат кнопки.\n\n"
                "Используйте формат: `➕ <символ> <количество>`\n"
                "Пример: `➕ BTC 0.01`",
                parse_mode=None,
                reply_markup=get_add_asset_keyboard()
            )

    # Обработка быстрых команд из кнопок портфеля
    elif text == "📊 Статистика":
        from .commands.price import stats_command
        await stats_command(update, context)

    elif text == "👥 Пользователи":
        # Это админская команда, проверяем права
        from .commands.admin import is_admin
        if is_admin(user.id):
            from .commands.admin import stats_command as admin_stats_command
            await admin_stats_command(update, context)
        else:
            await update.message.reply_text(
                "❌ Доступ запрещен\n\nЭта функция только для администраторов.",
                parse_mode=None
            )

    elif text == "💎 Цены товаров":
        from .commands.admin import is_admin
        if is_admin(user.id):
            await update.message.reply_text(
                "Для обновления цены товара используйте:\n\n"
                "`/update_product_price <код_товара> <цена>`\n\n"
                "Пример:\n"
                "`/update_product_price product_1 120.5`",
                parse_mode=None
            )
        else:
            await update.message.reply_text(
                "❌ Доступ запрещен\n\nЭта функция только для администраторов.",
                parse_mode=None
            )

    elif text == "🥇 Цены металлов":
        from .commands.admin import is_admin
        if is_admin(user.id):
            await update.message.reply_text(
                "Для обновления цен на металлы используйте:\n\n"
                "`/update_metal_prices <металл> <цена>`\n\n"
                "Примеры:\n"
                "`/update_metal_prices gold 65.5`\n"
                "`/update_metal_prices silver 0.88`",
                parse_mode=None
            )
        else:
            await update.message.reply_text(
                "❌ Доступ запрещен\n\nЭта функция только для администраторов.",
                parse_mode=None
            )

    elif text == "⚙️ Админ":
        from .commands.admin import is_admin
        if is_admin(user.id):
            from .keyboards import get_admin_keyboard
            await update.message.reply_text(
                "⚙️ **Панель администратора**\n\n"
                "Доступные функции:\n"
                "• Просмотр статистики бота\n"
                "• Обновление цен товаров\n"
                "• Обновление цен металлов\n"
                "• Управление пользователями\n\n"
                "Выберите действие:",
                parse_mode=None,
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Доступ запрещен\n\nЭта функция только для администраторов.",
                parse_mode=None
            )

    elif text == "📊 ETF":
        from .commands.assets import etfs_command
        await etfs_command(update, context)

    elif text == "🧾 Дебиторка":
        from .commands.assets import receivables_command
        await receivables_command(update, context)

    else:
        # Если текст не распознан как команда кнопки
        # Проверяем, не является ли это скрытой командой
        if text.startswith('/'):
            # Если это команда, она уже обработается CommandHandler
            # Просто игнорируем
            pass
        else:
            # Показываем основную клавиатуру и подсказку
            await update.message.reply_text(
                f"🤔 Не понимаю команду: {text}\n\n"
                f"Привет, {get_user_display_name(update)}!\n"
                "Используйте кнопки на клавиатуре или введите одну из команд:\n\n"
                "📍 **Основные команды:**\n"
                "`/start` — перезапустить бота\n"
                "`/help` — помощь по командам\n"
                "`/portfolio` — ваш портфель\n\n"
                "📍 **Управление активами:**\n"
                "`/add` — добавить актив\n"
                "`/remove` — удалить актив\n\n"
                "📍 **Информация:**\n"
                "`/prices` — текущие цены\n"
                "`/coins` — криптовалюты\n"
                "`/metals` — драгоценные металлы",
                parse_mode=None,
                reply_markup=get_main_keyboard()
            )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает callback-запросы от инлайн-кнопок"""
    query = update.callback_query
    await query.answer()  # Обязательно отвечаем на callback

    callback_data = query.data
    user = query.from_user

    logger.info(f"User {user.id} pressed inline button: {callback_data}")

    # Регистрируем активность
    record_user_activity(user.id, f"inline_{callback_data}")

    # Обрабатываем callback-данные
    if callback_data == "assets_crypto":
        from .commands.assets import coins_command
        await coins_command(update, context)

    elif callback_data == "assets_fiat":
        from .commands.assets import currencies_command
        await currencies_command(update, context)

    elif callback_data == "assets_metals":
        from .commands.assets import metals_command
        await metals_command(update, context)

    elif callback_data == "assets_products":
        from .commands.assets import products_command
        await products_command(update, context)

    elif callback_data == "assets_etf":
        from .commands.assets import etfs_command
        await etfs_command(update, context)

    elif callback_data == "assets_receivables":
        from .commands.assets import receivables_command
        await receivables_command(update, context)

    elif callback_data == "portfolio_add":
        await query.edit_message_text(
            text=f"Для добавления актива, {get_user_display_name(update)}!\n\n"
                 "Используйте команду:\n"
                 "`/add <символ> <количество>`\n\n"
                 "📋 **Примеры:**\n"
                 "`/add btc 0.1` — добавить 0.1 BTC\n"
                 "`/add eth 2.0` — добавить 2 ETH\n"
                 "`/add rub 10000` — добавить 10,000 ₽",
            parse_mode=None
        )

    elif callback_data == "portfolio_remove":
        await query.edit_message_text(
            text=f"Для удаления актива, {get_user_display_name(update)}!\n\n"
                 "Используйте команду:\n"
                 "`/remove <символ>` — удалить весь актив\n"
                 "`/remove <символ> <количество>` — удалить часть\n\n"
                 "📋 **Примеры:**\n"
                 "`/remove btc` — удалить весь BTC\n"
                 "`/remove eth 1.0` — удалить 1 ETH",
            parse_mode=None
        )

    elif callback_data == "portfolio_clear":
        await query.edit_message_text(
            text=f"⚠️ **Внимание, {get_user_display_name(update)}!**\n\n"
                 "Эта команда полностью очистит ваш портфель.\n"
                 "Все активы будут удалены без возможности восстановления.\n\n"
                 "Для подтверждения введите:\n"
                 "`/clear confirm`",
            parse_mode=None
        )

    elif callback_data == "portfolio_refresh":
        from .commands.portfolio import portfolio_command
        await portfolio_command(update, context)

    elif callback_data == "back_to_main":
        await query.edit_message_text(
            text=f"🔙 Возвращаемся в главное меню, {get_user_display_name(update)}!\n\n"
                 "Выберите действие:",
            parse_mode=None
        )

    elif callback_data == "go_home":
        await query.edit_message_text(
            text=f"🏠 Добро пожаловать в главное меню, {get_user_display_name(update)}!\n\n"
                 "Выберите действие из меню ниже:",
            parse_mode=None
        )
        # Показываем основную клавиатуру
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Используйте кнопки для навигации:",
            reply_markup=get_main_keyboard()
        )

    elif callback_data.startswith("confirm_"):
        action = callback_data.split("_")[1]
        if action == "yes":
            await query.edit_message_text(
                text="✅ Действие подтверждено\n\n"
                     "Выполняю операцию...",
                parse_mode=None
            )
            # Здесь можно добавить логику подтверждения
        elif action == "no":
            await query.edit_message_text(
                text="❌ Действие отменено",
                parse_mode=None
            )


def setup_handlers(application: Application):
    """Настраивает все обработчики команд в приложении"""

    commands = get_all_commands()

    # Регистрируем обработчики команд
    for command_name, handler in commands.items():
        application.add_handler(CommandHandler(command_name, handler))
        logger.debug(f"Registered /{command_name}")

    # Регистрируем обработчик текстовых сообщений (для кнопок ReplyKeyboard)
    # Обрабатываем все текстовые сообщения, кроме команд
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            handle_text_messages
        )
    )
    logger.debug(f"Registered text message handler for keyboard buttons")

    # Регистрируем обработчик callback-запросов (для инлайн-кнопок)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    logger.debug(f"Registered callback query handler for inline buttons")

    # Регистрируем обработчик для неизвестных команд
    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            f"❌ Неизвестная команда\n\n"
            f"Привет, {get_user_display_name(update)}!\n"
            "Используйте /help чтобы увидеть список доступных команд.",
            parse_mode=None,
            reply_markup=get_main_keyboard()
        )

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    logger.debug(f"Registered unknown command handler")

    logger.info(f"Successfully registered {len(commands)} command handlers + text handler + callback handler")
    return len(commands)