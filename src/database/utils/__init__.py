"""
Утилиты для работы с базой данных.

Предоставляет:
- Функции для работы с файлами
- Хелперы для преобразования данных
- Инструменты для отладки
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'load_json_file',
    'save_json_file',
    'format_timestamp',
    'calculate_portfolio_stats',
    'export_to_csv',
    'import_from_csv'
]


def load_json_file(filepath: str, default: Any = None) -> Any:
    """Загружает данные из JSON файла"""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return default

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.debug(f"Loaded JSON from {filepath}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return default
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return default


def save_json_file(filepath: str, data: Any, indent: int = 2) -> bool:
    """Сохраняет данные в JSON файл"""
    try:
        # Создаем директорию если нужно
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        logger.debug(f"Saved JSON to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")
        return False


def format_timestamp(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматирует timestamp в читаемый вид"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp

        return dt.strftime(format_str)
    except Exception as e:
        logger.debug(f"Error formatting timestamp {timestamp}: {e}")
        return str(timestamp)


def calculate_portfolio_stats(portfolio: Dict[str, Any], prices: Dict[str, float]) -> Dict[str, Any]:
    """Рассчитывает статистику портфеля"""
    try:
        total_value = 0
        asset_values = {}

        for symbol, asset_data in portfolio.get("assets", {}).items():
            amount = asset_data.get("amount", 0)
            price = prices.get(symbol, 0)

            if price and amount:
                value = amount * price
                total_value += value
                asset_values[symbol] = {
                    "amount": amount,
                    "price": price,
                    "value": value,
                    "percentage": 0  # Заполним позже
                }

        # Рассчитываем проценты
        if total_value > 0:
            for symbol, data in asset_values.items():
                data["percentage"] = (data["value"] / total_value) * 100

        return {
            "total_value": total_value,
            "assets": asset_values,
            "asset_count": len(portfolio.get("assets", {})),
            "last_updated": portfolio.get("updated_at", "")
        }

    except Exception as e:
        logger.error(f"Error calculating portfolio stats: {e}")
        return {
            "total_value": 0,
            "assets": {},
            "asset_count": 0,
            "last_updated": "",
            "error": str(e)
        }


def export_to_csv(portfolio: Dict[str, Any], prices: Dict[str, float], output_file: str) -> bool:
    """Экспортирует портфель в CSV"""
    try:
        stats = calculate_portfolio_stats(portfolio, prices)

        csv_lines = [
            "Portfolio Export",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Value: ${stats['total_value']:,.2f}",
            "",
            "Asset,Amount,Price,Value,Percentage"
        ]

        for symbol, data in stats["assets"].items():
            csv_lines.append(
                f"{symbol.upper()},"
                f"{data['amount']:.6f},"
                f"${data['price']:.4f},"
                f"${data['value']:.2f},"
                f"{data['percentage']:.1f}%"
            )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))

        logger.info(f"Exported portfolio to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return False


def import_from_csv(filepath: str) -> Optional[Dict[str, Any]]:
    """Импортирует данные из CSV (базовый вариант)"""
    try:
        if not os.path.exists(filepath):
            logger.error(f"CSV file not found: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Простой парсинг (можно улучшить)
        assets = {}
        for line in lines[4:]:  # Пропускаем заголовок
            if line.strip() and ',' in line:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    symbol = parts[0].lower()
                    try:
                        amount = float(parts[1])
                        assets[symbol] = {"amount": amount}
                    except ValueError:
                        logger.warning(f"Invalid amount in CSV: {parts[1]}")

        return {
            "assets": assets,
            "imported_at": datetime.now().isoformat(),
            "source": filepath
        }

    except Exception as e:
        logger.error(f"Error importing from CSV: {e}")
        return None