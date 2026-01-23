# src/database/simple_user_repo.py
"""
Простой репозиторий для работы с пользователями.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SimpleUserRepository:
    """Простой репозиторий для работы с пользователями"""

    def __init__(self, data_file: str = None):
        # Определяем путь к файлу данных
        if data_file is None:
            # Путь относительно корня проекта
            project_root = Path(__file__).parent.parent.parent
            self.data_file = project_root / "src" / "data" / "users_data.json"
        else:
            self.data_file = Path(data_file)

        # Создаем директорию если нужно
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        # Загружаем данные
        self.data: Dict[str, Any] = self._load_data()

        logger.info(f"SimpleUserRepository initialized with {self.data_file}")
        logger.info(f"Loaded {len(self.data)} users")

    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded user data from {self.data_file}")
                return data
            else:
                logger.info(f"User data file {self.data_file} does not exist, starting fresh")
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
            logger.error(f"Failed to load user data from {self.data_file}: {e}")
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
            logger.error(f"Failed to save user data to {self.data_file}: {e}")
            return False

    def get_or_create_user(self, user_id: int, username: Optional[str] = None,
                           first_name: Optional[str] = None, last_name: Optional[str] = None,
                           language_code: Optional[str] = None, is_premium: bool = False) -> Dict[str, Any]:
        """Получает или создает пользователя"""
        user_key = str(user_id)

        if user_key not in self.data:
            now = datetime.now().isoformat()
            self.data[user_key] = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "language_code": language_code,
                "is_premium": is_premium,
                "created_at": now,
                "last_seen": now,
                "settings": {
                    "notifications": True,
                    "currency": "USD",
                    "language": language_code or "ru",
                    "daily_report": False,
                    "price_alerts": False,
                    "theme": "default"
                },
                "activity_count": 0
            }
            self._save_data()
            logger.info(f"Created new user: {user_id} ({username})")
        else:
            # Обновляем информацию если изменилась
            updated = False
            user_data = self.data[user_key]

            if username and user_data.get("username") != username:
                user_data["username"] = username
                updated = True

            if first_name and user_data.get("first_name") != first_name:
                user_data["first_name"] = first_name
                updated = True

            if last_name and user_data.get("last_name") != last_name:
                user_data["last_name"] = last_name
                updated = True

            if language_code and user_data.get("language_code") != language_code:
                user_data["language_code"] = language_code
                updated = True

            if updated:
                self._save_data()
                logger.debug(f"Updated user info for {user_id}")

        return self.data[user_key]

    def record_user_activity(self, user_id: int, activity: str):
        """Записывает активность пользователя"""
        try:
            user_key = str(user_id)

            # Убедимся, что пользователь существует
            if user_key not in self.data:
                # Создаем пользователя с минимальной информацией
                self.get_or_create_user(user_id)

            # Обновляем last_seen
            self.data[user_key]["last_seen"] = datetime.now().isoformat()

            # Увеличиваем счетчик активности
            self.data[user_key]["activity_count"] = self.data[user_key].get("activity_count", 0) + 1

            # Сохраняем
            self._save_data()

            logger.debug(f"Recorded activity '{activity}' for user {user_id}")

        except Exception as e:
            logger.error(f"Error recording activity for user {user_id}: {e}")

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получает настройки пользователя"""
        user_key = str(user_id)

        if user_key not in self.data:
            # Возвращаем настройки по умолчанию
            return {
                "notifications": True,
                "currency": "USD",
                "language": "ru",
                "daily_report": False,
                "price_alerts": False,
                "theme": "default"
            }

        return self.data[user_key].get("settings", {})

    def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Обновляет настройки пользователя"""
        try:
            user_key = str(user_id)

            if user_key not in self.data:
                return False

            # Обновляем настройки
            current_settings = self.data[user_key].get("settings", {})
            current_settings.update(settings)
            self.data[user_key]["settings"] = current_settings

            # Сохраняем
            success = self._save_data()

            if success:
                logger.info(f"Updated settings for user {user_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error updating settings for user {user_id}: {e}")
            return False

    def get_user_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по пользователям"""
        try:
            total_users = len(self.data)

            if total_users == 0:
                return {
                    "total_users": 0,
                    "active_users": 0,
                    "premium_users": 0,
                    "languages": {},
                    "registration_trend": []
                }

            # Считаем активных пользователей (последние 30 дней)
            active_users = 0
            premium_users = 0
            languages = {}

            cutoff_date = datetime.now() - datetime.timedelta(days=30)

            for user_data in self.data.values():
                # Premium пользователи
                if user_data.get("is_premium", False):
                    premium_users += 1

                # Языки
                lang = user_data.get("language_code", "unknown")
                languages[lang] = languages.get(lang, 0) + 1

                # Активные пользователи
                try:
                    last_seen = datetime.fromisoformat(user_data.get("last_seen", ""))
                    if last_seen >= cutoff_date:
                        active_users += 1
                except:
                    pass

            # Тренд регистраций (по месяцам)
            registration_trend = {}
            for user_data in self.data.values():
                try:
                    created_at = user_data.get("created_at", "")
                    if created_at:
                        # Берем только год и месяц
                        month_key = created_at[:7]  # YYYY-MM
                        registration_trend[month_key] = registration_trend.get(month_key, 0) + 1
                except:
                    pass

            return {
                "total_users": total_users,
                "active_users": active_users,
                "premium_users": premium_users,
                "premium_percentage": (premium_users / total_users * 100) if total_users > 0 else 0,
                "languages": languages,
                "registration_trend": [
                    {"month": month, "count": count}
                    for month, count in sorted(registration_trend.items())
                ]
            }

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {
                "total_users": len(self.data),
                "error": str(e)
            }

    def health_check(self) -> Dict[str, Any]:
        """Проверяет здоровье репозитория"""
        try:
            file_exists = self.data_file.exists()
            file_size = self.data_file.stat().st_size if file_exists else 0

            # Активные пользователи (последние 7 дней)
            active_users = 0
            cutoff_date = datetime.now() - datetime.timedelta(days=7)

            for user_data in self.data.values():
                try:
                    last_seen = datetime.fromisoformat(user_data.get("last_seen", ""))
                    if last_seen >= cutoff_date:
                        active_users += 1
                except:
                    pass

            return {
                "status": "healthy",
                "data_file": str(self.data_file),
                "file_exists": file_exists,
                "file_size": file_size,
                "total_users": len(self.data),
                "active_users_7d": active_users,
                "initialized": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": False
            }


# Глобальный экземпляр репозитория
user_repo = SimpleUserRepository()