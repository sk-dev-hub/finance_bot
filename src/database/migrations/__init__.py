"""
Модуль миграций для базы данных.

Обеспечивает:
- Миграцию старых форматов данных
- Создание бэкапов
- Восстановление из бэкапов
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'migrate_old_data',
    'create_backup',
    'restore_backup',
    'list_backups',
    'get_migration_info'
]


def migrate_old_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Мигрирует данные из старого формата в новый.

    Старый формат (v1.0):
        {
            "123456": {
                "username": "user1",
                "assets": {
                    "btc": {"amount": 0.5, "added_at": "..."},
                    "eth": {"amount": 2.0, "added_at": "..."}
                }
            }
        }

    Новый формат (v1.1):
        {
            "123456": {
                "user_id": 123456,
                "username": "user1",
                "assets": {
                    "btc": {
                        "symbol": "btc",
                        "amount": 0.5,
                        "added_at": "...",
                        "updated_at": "..."
                    }
                },
                "created_at": "...",
                "updated_at": "..."
            }
        }
    """
    migrated = {}

    for user_key, user_data in data.items():
        try:
            # Пытаемся определить формат
            if "user_id" in user_data:
                # Уже новый формат
                migrated[user_key] = user_data
                continue

            # Мигрируем старый формат
            user_id = int(user_key)
            now = datetime.now().isoformat()

            # Мигрируем активы
            migrated_assets = {}
            for symbol, asset_data in user_data.get("assets", {}).items():
                if isinstance(asset_data, dict):
                    # Если актив уже в правильном формате
                    if "symbol" in asset_data:
                        migrated_assets[symbol] = asset_data
                    else:
                        # Конвертируем старый формат
                        migrated_assets[symbol] = {
                            "symbol": symbol,
                            "amount": asset_data.get("amount", 0),
                            "added_at": asset_data.get("added_at", now),
                            "updated_at": now
                        }
                else:
                    # Если актив - просто число (очень старый формат)
                    migrated_assets[symbol] = {
                        "symbol": symbol,
                        "amount": asset_data,
                        "added_at": now,
                        "updated_at": now
                    }

            # Создаем запись пользователя
            migrated[user_key] = {
                "user_id": user_id,
                "username": user_data.get("username"),
                "assets": migrated_assets,
                "created_at": user_data.get("created_at", now),
                "updated_at": now
            }

            logger.info(f"Migrated user {user_id} to new format")

        except Exception as e:
            logger.error(f"Error migrating user {user_key}: {e}")
            # Оставляем оригинальные данные при ошибке
            migrated[user_key] = user_data

    return migrated


def create_backup(data_file: str, backup_dir: str = "backups") -> str:
    """Создает резервную копию файла данных"""
    try:
        # Создаем директорию для бэкапов
        Path(backup_dir).mkdir(exist_ok=True)

        # Генерируем имя файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/portfolio_backup_{timestamp}.json"

        # Копируем файл
        if os.path.exists(data_file):
            shutil.copy2(data_file, backup_file)

            # Сохраняем метаданные бэкапа
            metadata = {
                "original_file": data_file,
                "backup_file": backup_file,
                "created_at": datetime.now().isoformat(),
                "size": os.path.getsize(backup_file)
            }

            metadata_file = f"{backup_file}.meta"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Backup created: {backup_file}")

            # Ограничиваем количество бэкапов (оставляем последние 10)
            backups = sorted(Path(backup_dir).glob("portfolio_backup_*.json"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
                    # Удаляем соответствующий метафайл
                    meta_file = Path(f"{old_backup}.meta")
                    if meta_file.exists():
                        meta_file.unlink()
                    logger.info(f"Deleted old backup: {old_backup}")

            return backup_file
        else:
            logger.error(f"Data file not found: {data_file}")
            return None

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None


def restore_backup(backup_file: str, target_file: str = None) -> bool:
    """Восстанавливает данные из бэкапа"""
    try:
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False

        # Если target_file не указан, используем оригинальное имя из метаданных
        if target_file is None:
            meta_file = f"{backup_file}.meta"
            if os.path.exists(meta_file):
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    target_file = metadata.get("original_file", "data/user_data.json")
            else:
                target_file = "data/user_data.json"

        # Создаем бэкап текущих данных перед восстановлением
        if os.path.exists(target_file):
            emergency_backup = f"{backup_file}.emergency"
            shutil.copy2(target_file, emergency_backup)
            logger.info(f"Created emergency backup: {emergency_backup}")

        # Восстанавливаем данные
        shutil.copy2(backup_file, target_file)
        logger.info(f"Restored backup {backup_file} to {target_file}")
        return True

    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return False


def list_backups(backup_dir: str = "backups") -> list:
    """Возвращает список доступных бэкапов"""
    try:
        backups = []

        for backup_file in Path(backup_dir).glob("portfolio_backup_*.json"):
            meta_file = Path(f"{backup_file}.meta")

            backup_info = {
                "file": str(backup_file),
                "size": backup_file.stat().st_size,
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime)
            }

            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        backup_info.update(metadata)
                except:
                    pass

            backups.append(backup_info)

        # Сортируем по дате изменения (новые сначала)
        backups.sort(key=lambda x: x.get("modified", datetime.min), reverse=True)

        return backups

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return []


def get_migration_info() -> dict:
    """Возвращает информацию о миграциях"""
    return {
        "current_version": "1.1.0",
        "supported_formats": ["1.0.0", "1.1.0"],
        "description": "Migration from old asset format to new unified format"
    }