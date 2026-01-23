# src/assets/base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AssetPrice:
    """Цена актива"""
    symbol: str
    price: float
    currency: str = "USD"
    timestamp: datetime = None
    source: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseAsset(ABC):
    """Абстрактный базовый класс для всех активов"""

    def __init__(self, config: 'AssetConfig'):
        self.config = config
        self.symbol = config.symbol
        self.name = config.name
        self.asset_type = config.asset_type

    @abstractmethod
    async def get_price(self) -> Optional[AssetPrice]:
        """Получает текущую цену актива"""
        pass

    @abstractmethod
    def validate_amount(self, amount: float) -> bool:
        """Валидирует количество актива"""
        pass

    def format_amount(self, amount: float) -> str:
        """Форматирует количество для отображения"""
        return f"{amount:.{self.config.display_precision}f}"

    def format_value(self, amount: float, price: float) -> str:
        """Форматирует стоимость"""
        value = amount * price
        return f"${value:,.2f}"

    @property
    def display_name(self) -> str:
        """Отображаемое имя с emoji"""
        return f"{self.config.emoji} {self.name} ({self.symbol.upper()})"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "type": self.asset_type.value,
            "emoji": self.config.emoji,
            "precision": self.config.display_precision
        }