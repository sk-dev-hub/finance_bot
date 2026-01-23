# src/assets/__init__.py
"""
Модуль для управления активами.
Все активы определяются в config/assets.py
"""

from .base import BaseAsset, AssetPrice
from .crypto import CryptoAsset
from .factory import AssetFactory, asset_factory
from .registry import AssetRegistry, asset_registry

__all__ = [
    'BaseAsset',
    'AssetPrice',
    'CryptoAsset',
    'AssetFactory',
    'asset_factory',
    'AssetRegistry',
    'asset_registry',
]