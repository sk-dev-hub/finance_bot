"""
Модуль бота для обработки команд Telegram.
"""

from .handlers import setup_handlers
from .commands import (
    start_command,
    help_command,
    portfolio_command,
    add_command,
    remove_command,
    prices_command,
    coins_command,
    assets_command,
    settings_command,
    stats_command,
    clear_command
)

__all__ = [
    'setup_handlers',
    'start_command',
    'help_command',
    'portfolio_command',
    'add_command',
    'remove_command',
    'prices_command',
    'coins_command',
    'assets_command',
    'settings_command',
    'stats_command',
    'clear_command'
]

__version__ = "1.0.0"