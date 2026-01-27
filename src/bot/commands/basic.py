# src/bot/bot/basic.py
"""
Основные команды бота: start, help, settings.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...database.simple_user_repo import user_repo
from ..helpers.messages import (
    get_welcome_message,
    get_help_message,
    get_settings_message
)
from ..helpers.command_utils import get_user_display_name, record_user_activity

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Создаем/получаем пользователя
    user_repo.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_premium=getattr(user, 'is_premium', False)
    )

    record_user_activity(user.id, "start")

    welcome_message = get_welcome_message(get_user_display_name(update))

    await update.message.reply_text(
        welcome_message,
        parse_mode=None
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user = update.effective_user
    record_user_activity(user.id, "help")

    help_message = get_help_message(get_user_display_name(update))

    await update.message.reply_text(
        help_message,
        parse_mode=None
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    user = update.effective_user
    record_user_activity(user.id, "settings")

    settings = user_repo.get_user_settings(user.id)
    portfolio_stats = {
        "total_assets": len(getattr(settings, 'assets', {})),
        "currency": settings.get('currency', 'USD'),
        "notifications": settings.get('notifications', True)
    }

    settings_message = get_settings_message(
        get_user_display_name(update),
        settings,
        portfolio_stats
    )

    await update.message.reply_text(
        settings_message,
        parse_mode=None
    )