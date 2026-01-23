"""
Модуль базы данных для Crypto Portfolio Bot.

Основные компоненты:
- models: Модели данных
- repositories: Репозитории для работы с данными
- utils: Вспомогательные утилиты
"""

from .models import (
    UserPortfolio,
    UserAsset,
    PortfolioStats,
    AssetTransaction,
    User,
    UserSettings
)

from .repositories import (
    PortfolioRepository,
    portfolio_repo,
    AssetRepository,
    asset_repo,
    UserRepository,
    user_repo
)

__version__ = "1.2.0"
__author__ = "Crypto Portfolio Bot Team"

__all__ = [
    # Модели
    'UserPortfolio',
    'UserAsset',
    'PortfolioStats',
    'AssetTransaction',
    'User',
    'UserSettings',

    # Репозитории
    'PortfolioRepository',
    'portfolio_repo',
    'AssetRepository',
    'asset_repo',
    'UserRepository',
    'user_repo',
]

# Инициализация
import logging
logger = logging.getLogger(__name__)
logger.info(f"Database module v{__version__} initialized")