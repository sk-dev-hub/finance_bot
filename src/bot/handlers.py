"""
Настройка обработчиков команд для бота.
"""

import logging
from telegram.ext import Application, CommandHandler

from .commands import get_all_commands

logger = logging.getLogger(__name__)


def setup_handlers(application: Application):
    """Настраивает все обработчики команд"""

    commands = get_all_commands()

    for command_name, handler in commands.items():
        application.add_handler(CommandHandler(command_name, handler))
        logger.debug(f"Registered handler for /{command_name}")

    logger.info(f"Registered {len(commands)} command handlers")

    # Обработчик для неизвестных команд
    async def unknown_command(update, context):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "❌ Неизвестная команда. Используйте /help для списка команд.",
            parse_mode="Markdown"
        )

    # Добавляем обработчик для любых сообщений, которые не являются командами
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))

    return len(commands)