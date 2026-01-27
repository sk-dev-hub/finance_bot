# src/bot/handlers.py
"""
Регистрация всех обработчиков команд.
"""

import logging
from typing import Dict, Callable
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler

logger = logging.getLogger(__name__)


def get_all_commands() -> Dict[str, Callable]:
    """Возвращает словарь всех команд и их обработчиков"""

    from .commands.basic import start_command, help_command, settings_command
    from .commands.portfolio import portfolio_command, add_command, remove_command, clear_command
    from .commands.assets import coins_command, currencies_command, metals_command, products_command, \
        receivables_command, assets_command
    from .commands.price import prices_command, stats_command

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
    }

    logger.info(f"Loaded {len(commands)} command handlers")
    return commands


def setup_handlers(application: Application):
    """Настраивает все обработчики команд в приложении"""

    commands = get_all_commands()

    for command_name, handler in commands.items():
        application.add_handler(CommandHandler(command_name, handler))
        logger.debug(f"Registered /{command_name}")

    logger.info(f"Successfully registered {len(commands)} command handlers")
    return len(commands)