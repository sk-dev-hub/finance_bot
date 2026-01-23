# src/assets/registry.py
from typing import Dict, List, Optional
from .factory import asset_factory
from .base import BaseAsset
from src.config.assets import get_all_assets, get_enabled_assets, get_crypto_assets


class AssetRegistry:
    """Реестр всех активов в системе"""

    def __init__(self):
        self._assets: Dict[str, BaseAsset] = {}
        self._load_assets()

    def _load_assets(self):
        """Загружает все активы из конфигурации"""
        for config in get_enabled_assets():
            asset = asset_factory.create_asset(config)
            self._assets[config.symbol] = asset

    def get_asset(self, symbol: str) -> Optional[BaseAsset]:
        """Получает актив по символу"""
        symbol_lower = symbol.lower()

        # Прямой поиск
        if symbol_lower in self._assets:
            return self._assets[symbol_lower]

        # Поиск по алиасам
        for asset in self._assets.values():
            if symbol_lower in asset.config.aliases:
                return asset

        return None

    def get_all_assets(self) -> List[BaseAsset]:
        """Возвращает все активы"""
        return list(self._assets.values())

    def get_crypto_assets(self) -> List[BaseAsset]:
        """Возвращает крипто активы"""
        return [asset for asset in self._assets.values()
                if asset.asset_type.value == "crypto"]

    def get_assets_by_type(self, asset_type: str) -> List[BaseAsset]:
        """Возвращает активы по типу"""
        return [asset for asset in self._assets.values()
                if asset.asset_type.value == asset_type]

    def is_supported(self, symbol: str) -> bool:
        """Проверяет, поддерживается ли актив"""
        return self.get_asset(symbol) is not None

    def get_supported_symbols(self) -> List[str]:
        """Возвращает список поддерживаемых символов"""
        return list(self._assets.keys())

    async def close_all(self):
        """Закрывает все ресурсы активов"""
        for asset in self._assets.values():
            if hasattr(asset, 'close'):
                await asset.close()


# Глобальный экземпляр реестра
asset_registry = AssetRegistry()