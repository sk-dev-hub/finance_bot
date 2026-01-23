# src/assets/factory.py
from typing import Dict, Optional
from src.config.assets import AssetConfig, AssetType
from .crypto import CryptoAsset
from .base import BaseAsset


class AssetFactory:
    """Фабрика для создания объектов активов"""

    # Регистр классов активов по типу
    _asset_classes = {
        AssetType.CRYPTO: CryptoAsset,
        # AssetType.STOCK: StockAsset,  # Добавить при необходимости
        # AssetType.ETF: ETFAsset,      # Добавить при необходимости
    }

    @classmethod
    def register_asset_class(cls, asset_type: AssetType, asset_class):
        """Регистрирует новый класс актива"""
        cls._asset_classes[asset_type] = asset_class

    @classmethod
    def create_asset(cls, config: AssetConfig) -> BaseAsset:
        """Создает объект актива на основе конфигурации"""
        asset_class = cls._asset_classes.get(config.asset_type)

        if not asset_class:
            raise ValueError(f"No asset class registered for type: {config.asset_type}")

        return asset_class(config)

    @classmethod
    def create_asset_by_symbol(cls, symbol: str) -> BaseAsset:
        """Создает объект актива по символу"""
        from src.config.assets import get_asset_config
        config = get_asset_config(symbol)
        return cls.create_asset(config)


# Глобальный экземпляр фабрики
asset_factory = AssetFactory()