# src/main.py
import logging
import asyncio
import sys
import os
from pathlib import Path

from telegram.ext import Application

from src.config.settings import settings
from src.bot.handlers import setup_handlers
from src.assets.registry import asset_registry


def setup_directories():
    """Создает необходимые директории"""
    directories = ['logs', 'data', 'backups']

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directory '{directory}' checked")


def setup_logging():
    """Настраивает логирование"""
    setup_directories()

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый обработчик
    try:
        file_handler = logging.FileHandler(
            settings.LOG_FILE,
            encoding='utf-8',
            mode='a'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️ Could not create file logger: {e}")

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger


async def on_startup(application: Application):
    """Выполняется при запуске бота"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Starting Crypto Portfolio Bot")
    logger.info("=" * 50)

    # Загружаем активы
    assets_count = len(asset_registry.get_all_assets())
    logger.info(f"Loaded {assets_count} assets:")

    for asset in asset_registry.get_all_assets():
        logger.info(f"  • {asset.display_name}")

    logger.info("=" * 50)


async def on_shutdown(application: Application):
    """Выполняется при остановке бота"""
    logger = logging.getLogger(__name__)
    logger.info("Shutting down bot...")

    # Закрываем ресурсы активов
    await asset_registry.close_all()

    logger.info("Bot stopped")


def main():
    """Точка входа"""
    logger = setup_logging()

    try:
        # Проверяем токен
        if not settings.BOT_TOKEN or settings.BOT_TOKEN == "your_bot_token_here":
            logger.error("❌ BOT_TOKEN not set")
            print("❌ Error: BOT_TOKEN not set")
            print("Create .env file from .env.example and add your token")
            return

        # Создаем приложение
        application = Application.builder().token(settings.BOT_TOKEN).build()

        # Настраиваем обработчики
        setup_handlers(application)

        # Обработчик ошибок
        async def error_handler(update: object, context):
            logger.error(f"Update error: {context.error}", exc_info=True)

        application.add_error_handler(error_handler)

        # Запускаем бота
        application.post_init = on_startup
        application.post_stop = on_shutdown

        logger.info("Bot started. Press Ctrl+C to stop.")
        print("✅ Bot started. Open Telegram and find your bot.")
        print("📝 Use /start to begin")

        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Bot stopped")
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        print(f"❌ Critical error: {e}")


if __name__ == "__main__":
    main()