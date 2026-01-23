"""
Репозитории для работы с данными.

Реализует паттерн Repository для доступа к данным:
- PortfolioRepository: работа с портфелями пользователей
- AssetRepository: работа с отдельными активами
- UserRepository: работа с пользователями
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = [
    # Базовый класс
    'BaseRepository',

    # Репозитории
    'PortfolioRepository',
    'portfolio_repo',
    'AssetRepository',
    'asset_repo',
    'UserRepository',
    'user_repo',
]

# ============================================================================
# Базовый класс репозитория
# ============================================================================

class BaseRepository:
    """Базовый класс для всех репозиториев"""

    def __init__(self, data_file: str):
        self.data_file = data_file

    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из файла"""
        raise NotImplementedError

    def _save_data(self):
        """Сохраняет данные в файл"""
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        """Проверяет здоровье репозитория"""
        return {
            "status": "unknown",
            "repository": self.__class__.__name__,
            "data_file": self.data_file
        }

# ============================================================================
# Заглушки для репозиториев
# ============================================================================

class PortfolioRepository(BaseRepository):
    """Репозиторий для работы с портфелями пользователей"""

    def __init__(self, data_file: str = "data/user_data.json"):
        super().__init__(data_file)
        self.data: Dict[str, Any] = {}
        logger.info(f"Initialized PortfolioRepository with {data_file}")

    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        logger.warning("PortfolioRepository._load_data() is a stub")
        return {}

    def _save_data(self):
        """Сохраняет данные в JSON файл"""
        logger.warning("PortfolioRepository._save_data() is a stub")

    def get_or_create_user(self, user_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        """Получает или создает пользователя"""
        logger.warning(f"PortfolioRepository.get_or_create_user({user_id}, {username}) is a stub")
        return {
            "user_id": user_id,
            "username": username,
            "assets": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def add_asset(self, user_id: int, symbol: str, amount: float) -> tuple[bool, str]:
        """Добавляет актив пользователю"""
        logger.warning(f"PortfolioRepository.add_asset({user_id}, {symbol}, {amount}) is a stub")
        return True, f"Stub: Added {amount} {symbol}"

    def remove_asset(self, user_id: int, symbol: str, amount: Optional[float] = None) -> tuple[bool, str]:
        """Удаляет актив у пользователя"""
        logger.warning(f"PortfolioRepository.remove_asset({user_id}, {symbol}, {amount}) is a stub")
        return True, f"Stub: Removed {amount if amount else 'all'} {symbol}"

    def get_user_assets(self, user_id: int) -> Dict[str, Any]:
        """Получает активы пользователя"""
        logger.warning(f"PortfolioRepository.get_user_assets({user_id}) is a stub")
        return {}

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей"""
        logger.warning("PortfolioRepository.get_all_users() is a stub")
        return []

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        logger.warning(f"PortfolioRepository.delete_user({user_id}) is a stub")
        return True

# Глобальный экземпляр
portfolio_repo = PortfolioRepository()

class AssetRepository(BaseRepository):
    """Репозиторий для работы с отдельными активами"""

    def __init__(self, data_file: str = "data/assets_data.json"):
        super().__init__(data_file)
        logger.info(f"Initialized AssetRepository with {data_file}")

    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        logger.warning("AssetRepository._load_data() is a stub")
        return {}

    def _save_data(self):
        """Сохраняет данные в JSON файл"""
        logger.warning("AssetRepository._save_data() is a stub")

    def get_asset_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Получает историю цены актива"""
        logger.warning(f"AssetRepository.get_asset_history({symbol}, {days}) is a stub")
        return []

    def get_asset_stats(self, symbol: str) -> Dict[str, Any]:
        """Получает статистику актива"""
        logger.warning(f"AssetRepository.get_asset_stats({symbol}) is a stub")
        return {
            "symbol": symbol,
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "volume": 0
        }

    def record_price(self, symbol: str, price: float, timestamp: str = None):
        """Записывает цену актива в историю"""
        logger.warning(f"AssetRepository.record_price({symbol}, {price}) is a stub")

    def get_popular_assets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает самые популярные активы"""
        logger.warning(f"AssetRepository.get_popular_assets({limit}) is a stub")
        return []

# Глобальный экземпляр
asset_repo = AssetRepository()

class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""

    def __init__(self, data_file: str = "data/users_data.json"):
        super().__init__(data_file)
        logger.info(f"Initialized UserRepository with {data_file}")

    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        logger.warning("UserRepository._load_data() is a stub")
        return {}

    def _save_data(self):
        """Сохраняет данные в JSON файл"""
        logger.warning("UserRepository._save_data() is a stub")

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по ID"""
        logger.warning(f"UserRepository.get_user({user_id}) is a stub")
        return {
            "user_id": user_id,
            "username": f"user_{user_id}",
            "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }

    def create_user(self, user_id: int, username: str = None) -> Dict[str, Any]:
        """Создает нового пользователя"""
        logger.warning(f"UserRepository.create_user({user_id}, {username}) is a stub")
        return {
            "user_id": user_id,
            "username": username,
            "created_at": datetime.now().isoformat(),
            "settings": {}
        }

    def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Обновляет настройки пользователя"""
        logger.warning(f"UserRepository.update_user_settings({user_id}, {settings}) is a stub")
        return True

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получает настройки пользователя"""
        logger.warning(f"UserRepository.get_user_settings({user_id}) is a stub")
        return {
            "notifications": True,
            "currency": "USD",
            "language": "ru"
        }

    def record_user_activity(self, user_id: int, activity: str):
        """Записывает активность пользователя"""
        logger.warning(f"UserRepository.record_user_activity({user_id}, {activity}) is a stub")

    def get_active_users(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получает активных пользователей"""
        logger.warning(f"UserRepository.get_active_users({days}) is a stub")
        return []

# Глобальный экземпляр
user_repo = UserRepository()

# ============================================================================
# Вспомогательные функции
# ============================================================================

def init_repositories(data_file: str = None) -> Dict[str, Any]:
    """Инициализирует все репозитории"""
    logger.info("Initializing all repositories...")

    # Обновляем PortfolioRepository если указан файл
    if data_file:
        portfolio_repo.data_file = data_file

    return {
        "portfolio": portfolio_repo,
        "asset": asset_repo,
        "user": user_repo,
        "status": "initialized",
        "timestamp": datetime.now().isoformat()
    }

def close_repositories():
    """Закрывает все репозитории и сохраняет данные"""
    logger.info("Closing all repositories...")

    # Сохраняем данные
    try:
        portfolio_repo._save_data()
        asset_repo._save_data()
        user_repo._save_data()
    except:
        pass

    logger.info("All repositories closed")

# Инициализация при импорте
logger.info(f"Repositories module loaded")