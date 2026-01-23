"""
Модели данных для базы данных.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List
from datetime import datetime

__all__ = [
    'UserPortfolio',
    'UserAsset',
    'PortfolioStats',
    'AssetTransaction',
    'User',
    'UserSettings'
]

# ============================================================================
# Основные модели
# ============================================================================

@dataclass
class UserAsset:
    """Модель актива пользователя"""
    symbol: str
    amount: float
    added_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserAsset':
        return cls(**data)

@dataclass
class UserPortfolio:
    """Портфель пользователя"""
    user_id: int
    username: Optional[str]
    assets: Dict[str, UserAsset]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "assets": {k: v.to_dict() for k, v in self.assets.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPortfolio':
        assets = {}
        for symbol, asset_data in data.get("assets", {}).items():
            assets[symbol] = UserAsset.from_dict(asset_data)

        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            assets=assets,
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )

@dataclass
class PortfolioStats:
    """Статистика портфеля"""
    total_value: float
    asset_count: int
    last_updated: str
    assets: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioStats':
        return cls(**data)

@dataclass
class AssetTransaction:
    """Транзакция актива"""
    id: Optional[str] = None
    user_id: int = 0
    symbol: str = ""
    amount: float = 0
    price: Optional[float] = None
    transaction_type: str = ""  # buy, sell, transfer
    timestamp: str = ""
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id:
            self.id = f"tx_{hash(self)}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssetTransaction':
        return cls(**data)

@dataclass
class UserSettings:
    """Настройки пользователя"""
    notifications: bool = True
    currency: str = "USD"
    language: str = "ru"
    daily_report: bool = False
    price_alerts: bool = False
    theme: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        return cls(**data)

@dataclass
class User:
    """Модель пользователя"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    created_at: str = ""
    last_seen: str = ""
    settings: Optional[UserSettings] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_seen:
            self.last_seen = datetime.now().isoformat()
        if self.settings is None:
            self.settings = UserSettings()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.settings:
            data["settings"] = self.settings.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        settings_data = data.pop("settings", {})
        settings = UserSettings.from_dict(settings_data) if settings_data else UserSettings()

        return cls(**data, settings=settings)