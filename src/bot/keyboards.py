# src/bot/keyboards.py (обновленная версия)
"""
Клавиатуры для Telegram бота.
"""

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Optional


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает основную клавиатуру с главными командами.

    Returns:
        ReplyKeyboardMarkup: Основная клавиатура
    """
    keyboard = [
        [
            KeyboardButton("📊 Портфель"),
            KeyboardButton("📈 Цены")
        ],
        [
            KeyboardButton("💰 Крипто"),
            KeyboardButton("💵 Валюты")
        ],
        [
            KeyboardButton("🥇 Металлы"),
            KeyboardButton("📦 Товары")
        ],
        [
            KeyboardButton("📋 Помощь"),
            KeyboardButton("⚙️ Настройки")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для команды /start.

    Returns:
        ReplyKeyboardMarkup: Стартовая клавиатура
    """
    keyboard = [
        [
            KeyboardButton("🚀 Начать"),
            KeyboardButton("📊 Портфель")
        ],
        [
            KeyboardButton("📈 Цены"),
            KeyboardButton("💼 Активы")
        ],
        [
            KeyboardButton("📋 Помощь"),
            KeyboardButton("⚙️ Настройки")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Нажмите 'Начать' для продолжения..."
    )


def get_assets_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает инлайн-клавиатуру для выбора типов активов.

    Returns:
        InlineKeyboardMarkup: Клавиатура активов
    """
    keyboard = [
        [
            InlineKeyboardButton("💰 Криптовалюты", callback_data="assets_crypto"),
            InlineKeyboardButton("💵 Валюты", callback_data="assets_fiat")
        ],
        [
            InlineKeyboardButton("🥇 Металлы", callback_data="assets_metals"),
            InlineKeyboardButton("📦 Товары", callback_data="assets_products")
        ],
        [
            InlineKeyboardButton("📊 ETF", callback_data="assets_etf"),
            InlineKeyboardButton("🧾 Дебиторка", callback_data="assets_receivables")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_portfolio_actions_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для действий с портфелем.

    Returns:
        ReplyKeyboardMarkup: Клавиатура действий портфеля
    """
    keyboard = [
        [
            KeyboardButton("➕ Добавить"),
            KeyboardButton("➖ Удалить")
        ],
        [
            KeyboardButton("🧹 Очистить"),
            KeyboardButton("🔄 Обновить")
        ],
        [
            KeyboardButton("🏠 Главная"),
            KeyboardButton("📋 Помощь")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_quick_actions_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру быстрых действий.

    Returns:
        ReplyKeyboardMarkup: Клавиатура быстрых действий
    """
    keyboard = [
        [
            KeyboardButton("📊 Портфель"),
            KeyboardButton("📈 Цены")
        ],
        [
            KeyboardButton("💰 Крипто"),
            KeyboardButton("💵 Валюты")
        ],
        [
            KeyboardButton("🏠 Главная"),
            KeyboardButton("📋 Помощь")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для администраторов.

    Returns:
        ReplyKeyboardMarkup: Административная клавиатура
    """
    keyboard = [
        [
            KeyboardButton("📊 Статистика"),
            KeyboardButton("👥 Пользователи")
        ],
        [
            KeyboardButton("💎 Цены товаров"),
            KeyboardButton("🥇 Цены металлов")
        ],
        [
            KeyboardButton("🏠 Главная"),
            KeyboardButton("⚙️ Админ")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой отмены.

    Returns:
        ReplyKeyboardMarkup: Клавиатура отмены
    """
    keyboard = [
        [KeyboardButton("❌ Отмена")],
        [KeyboardButton("🏠 Главная")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_confirmation_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает инлайн-клавиатуру для подтверждения действий.

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Отмена", callback_data="confirm_no")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_navigation_inline_keyboard(back_callback: str = "back_to_main") -> InlineKeyboardMarkup:
    """
    Возвращает стандартную навигационную инлайн-клавиатуру.

    Args:
        back_callback: Callback для кнопки "Назад"

    Returns:
        InlineKeyboardMarkup: Навигационная клавиатура
    """
    keyboard = [
        [
            InlineKeyboardButton("🏠 Главная", callback_data="go_home"),
            InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_add_asset_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для быстрого добавления популярных активов.

    Returns:
        ReplyKeyboardMarkup: Клавиатура добавления активов
    """
    keyboard = [
        [
            KeyboardButton("➕ BTC 0.01"),
            KeyboardButton("➕ ETH 0.1")
        ],
        [
            KeyboardButton("➕ TON 10"),
            KeyboardButton("➕ USDT 100")
        ],
        [
            KeyboardButton("➕ SOL 1"),
            KeyboardButton("➕ RUB 10000")
        ],
        [
            KeyboardButton("❌ Отмена"),
            KeyboardButton("🏠 Главная")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )