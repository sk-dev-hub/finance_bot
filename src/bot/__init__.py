# src/bot/__init__.py
"""
Пакет команд для Telegram бота.
"""

from .handlers import setup_handlers
from .commands.basic import start_command, help_command, settings_command
from .commands.portfolio import portfolio_command, add_command, remove_command, clear_command
from .commands.assets import coins_command, currencies_command, metals_command, products_command, receivables_command, assets_command
from .commands.price import prices_command, stats_command

__all__ = [
    'setup_handlers',
    # Basic bot
    'start_command',
    'help_command',
    'settings_command',
    # Portfolio bot
    'portfolio_command',
    'add_command',
    'remove_command',
    'clear_command',
    # Asset bot
    'coins_command',
    'currencies_command',
    'metals_command',
    'products_command',
    'receivables_command',
    'assets_command',
    # Price bot
    'prices_command',
    'stats_command',
]