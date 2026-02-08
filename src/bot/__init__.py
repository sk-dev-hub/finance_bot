# src/bot/__init__.py (обновленный)
"""
Пакет команд для Telegram бота.
"""

from .handlers import setup_handlers
from .commands.basic import start_command, help_command, settings_command
from .commands.portfolio import portfolio_command, add_command, remove_command, clear_command
from .commands.assets import coins_command, currencies_command, metals_command, products_command, receivables_command, assets_command
from .commands.price import prices_command, stats_command
from .keyboards import (
    get_main_keyboard,
    get_start_keyboard,
    get_assets_keyboard,
    get_portfolio_actions_keyboard,
    get_quick_actions_keyboard,
    get_admin_keyboard,
    get_cancel_keyboard,
    get_confirmation_inline_keyboard,
    get_navigation_inline_keyboard,
    get_add_asset_keyboard
)

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
    # Keyboards
    'get_main_keyboard',
    'get_start_keyboard',
    'get_assets_keyboard',
    'get_portfolio_actions_keyboard',
    'get_quick_actions_keyboard',
    'get_admin_keyboard',
    'get_cancel_keyboard',
    'get_confirmation_inline_keyboard',
    'get_navigation_inline_keyboard',
    'get_add_asset_keyboard'
]