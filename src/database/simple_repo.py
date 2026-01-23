"""
Простой рабочий репозиторий для портфелей.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SimplePortfolioRepository:
    """Простой репозиторий для работы с портфелями"""

    def __init__(self, data_file: str = None):
        # Определяем путь к файлу данных
        if data_file is None:
            # Путь относительно корня проекта
            project_root = Path(__file__).parent.parent.parent
            self.data_file = project_root / "src" / "data" / "user_data.json"
        else:
            self.data_file = Path(data_file)

        # Создаем директорию если нужно
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        # Загружаем данные
        self.data: Dict[str, Any] = self._load_data()

        logger.info(f"SimplePortfolioRepository initialized with {self.data_file}")
        logger.info(f"Loaded {len(self.data)} users")

    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded data from {self.data_file}")
                return data
            else:
                logger.info(f"Data file {self.data_file} does not exist, starting fresh")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.data_file}: {e}")
            # Создаем backup поврежденного файла
            backup_file = self.data_file.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            if self.data_file.exists():
                import shutil
                shutil.copy2(self.data_file, backup_file)
                logger.error(f"Created backup of corrupted file: {backup_file}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load data from {self.data_file}: {e}")
            return {}

    def _save_data(self) -> bool:
        """Сохраняет данные в JSON файл"""
        try:
            # Создаем временный файл для безопасной записи
            temp_file = self.data_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            # Заменяем старый файл новым
            if self.data_file.exists():
                temp_file.replace(self.data_file)
            else:
                temp_file.rename(self.data_file)

            logger.debug(f"Saved {len(self.data)} users to {self.data_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save data to {self.data_file}: {e}")
            return False

    def save(self) -> bool:
        """Публичный метод для сохранения данных"""
        return self._save_data()

    def get_or_create_user(self, user_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает или создает пользователя.
        Возвращает словарь с данными пользователя.
        """
        user_key = str(user_id)

        if user_key not in self.data:
            now = datetime.now().isoformat()
            self.data[user_key] = {
                "user_id": user_id,
                "username": username,
                "assets": {},
                "created_at": now,
                "updated_at": now
            }
            self._save_data()
            logger.info(f"Created new user: {user_id} ({username})")
        else:
            # Обновляем username если изменился
            if username and self.data[user_key].get("username") != username:
                self.data[user_key]["username"] = username
                self.data[user_key]["updated_at"] = datetime.now().isoformat()
                self._save_data()
                logger.debug(f"Updated username for user {user_id}: {username}")

        return self.data[user_key]

    def add_asset(self, user_id: int, symbol: str, amount: float) -> Tuple[bool, str]:
        """Добавляет актив пользователю"""
        try:
            user_key = str(user_id)

            if user_key not in self.data:
                return False, "Пользователь не найден"

            # Нормализуем символ
            symbol = symbol.lower()

            # Проверяем количество
            if amount <= 0:
                return False, "Количество должно быть больше 0"

            # Получаем текущие активы
            assets = self.data[user_key].get("assets", {})
            now = datetime.now().isoformat()

            if symbol in assets:
                # Обновляем существующий актив
                current_amount = assets[symbol].get("amount", 0)
                assets[symbol]["amount"] = current_amount + amount
                assets[symbol]["updated_at"] = now
                logger.debug(f"Updated asset {symbol}: {current_amount} -> {current_amount + amount}")
            else:
                # Создаем новый актив
                assets[symbol] = {
                    "symbol": symbol,
                    "amount": amount,
                    "added_at": now,
                    "updated_at": now
                }
                logger.debug(f"Created new asset {symbol}: {amount}")

            # Обновляем данные пользователя
            self.data[user_key]["assets"] = assets
            self.data[user_key]["updated_at"] = now

            # Сохраняем
            success = self._save_data()

            if success:
                logger.info(f"Successfully added {amount} {symbol.upper()} to user {user_id}")
                return True, f"Успешно добавлено {amount} {symbol.upper()}"
            else:
                return False, "Ошибка при сохранении данных"

        except Exception as e:
            logger.error(f"Error adding asset for user {user_id}: {e}", exc_info=True)
            return False, f"Внутренняя ошибка: {str(e)}"

    def get_user_assets(self, user_id: int) -> Dict[str, Any]:
        """Получает активы пользователя"""
        user_key = str(user_id)

        if user_key not in self.data:
            return {}

        return self.data[user_key].get("assets", {})

    def get_portfolio(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает весь портфель пользователя"""
        user_key = str(user_id)

        if user_key not in self.data:
            return None

        return self.data[user_key]

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей"""
        users = []

        for user_key, user_data in self.data.items():
            users.append({
                "user_id": user_data.get("user_id", int(user_key)),
                "username": user_data.get("username"),
                "asset_count": len(user_data.get("assets", {})),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at")
            })

        return users

    def remove_asset(self, user_id: int, symbol: str, amount: Optional[float] = None) -> Tuple[bool, str]:
        """Удаляет актив у пользователя"""
        try:
            user_key = str(user_id)

            if user_key not in self.data:
                return False, "Пользователь не найден"

            assets = self.data[user_key].get("assets", {})
            symbol = symbol.lower()

            if symbol not in assets:
                return False, "У вас нет такого актива"

            current_amount = assets[symbol].get("amount", 0)
            now = datetime.now().isoformat()

            if amount is None:
                # Удаляем полностью
                del assets[symbol]
                message = f"Весь {symbol.upper()} удален"
            elif amount > current_amount:
                return False, f"Недостаточно {symbol.upper()}. Доступно: {current_amount}"
            elif amount == current_amount:
                # Удаляем полностью, если количество совпадает
                del assets[symbol]
                message = f"Весь {symbol.upper()} удален"
            else:
                # Уменьшаем количество
                assets[symbol]["amount"] = current_amount - amount
                assets[symbol]["updated_at"] = now
                message = f"Удалено {amount} {symbol.upper()}"

            # Обновляем данные
            self.data[user_key]["assets"] = assets
            self.data[user_key]["updated_at"] = now

            # Сохраняем
            success = self._save_data()

            if success:
                logger.info(f"Successfully removed asset {symbol} from user {user_id}")
                return True, message
            else:
                return False, "Ошибка при сохранении данных"

        except Exception as e:
            logger.error(f"Error removing asset for user {user_id}: {e}")
            return False, f"Внутренняя ошибка: {str(e)}"

    def clear_portfolio(self, user_id: int) -> Tuple[bool, str]:
        """Полностью очищает портфель пользователя"""
        try:
            user_key = str(user_id)

            if user_key not in self.data:
                return False, "Пользователь не найден"

            assets_count = len(self.data[user_key].get("assets", {}))

            if assets_count == 0:
                return False, "Портфель уже пуст"

            # Очищаем активы
            self.data[user_key]["assets"] = {}
            self.data[user_key]["updated_at"] = datetime.now().isoformat()

            # Сохраняем
            success = self._save_data()

            if success:
                logger.info(f"Cleared portfolio for user {user_id} ({assets_count} assets)")
                return True, f"Портфель очищен. Удалено активов: {assets_count}"
            else:
                return False, "Ошибка при сохранении данных"

        except Exception as e:
            logger.error(f"Error clearing portfolio for user {user_id}: {e}")
            return False, f"Внутренняя ошибка: {str(e)}"

    def health_check(self) -> Dict[str, Any]:
        """Проверяет здоровье репозитория"""
        try:
            file_exists = self.data_file.exists()
            file_size = self.data_file.stat().st_size if file_exists else 0

            # Статистика пользователей
            total_users = len(self.data)
            total_assets = 0

            for user_data in self.data.values():
                total_assets += len(user_data.get("assets", {}))

            return {
                "status": "healthy",
                "data_file": str(self.data_file),
                "file_exists": file_exists,
                "file_size": file_size,
                "total_users": total_users,
                "total_assets": total_assets,
                "initialized": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": False
            }


# Глобальный экземпляр репозитория
portfolio_repo = SimplePortfolioRepository()