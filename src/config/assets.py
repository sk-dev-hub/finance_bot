# src/config/assets.py
"""
Конфигурация всех поддерживаемых активов.
Добавляйте новые активы ТОЛЬКО здесь!
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class AssetType(Enum):
    """Типы активов"""
    CRYPTO = "crypto"
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    COMMODITY = "commodity"


@dataclass
class AssetConfig:
    """Конфигурация одного актива"""

    # Основные поля
    symbol: str  # Уникальный символ (btc, eth, ton)
    name: str  # Человекочитаемое имя
    asset_type: AssetType  # Тип актива

    # Отображение
    emoji: str  # Emoji для отображения
    display_precision: int = 6  # Точность отображения количества

    # Источник данных
    price_source: str = "coingecko"  # Источник цен
    source_id: str = ""  # ID в источнике (например, "bitcoin" для CoinGecko)

    # Валидация
    min_amount: float = 0.000001  # Минимальное количество
    max_amount: float = 1000000  # Максимальное количество

    # Дополнительные поля
    enabled: bool = True  # Включен ли актив
    description: str = ""  # Описание

    # Алиасы (другие названия для этого актива)
    aliases: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []

        # Если source_id не указан, используем symbol
        if not self.source_id:
            self.source_id = self.symbol


# ============================================================================
# 🎯 ВСЕ АКТИВЫ ОПРЕДЕЛЕНЫ ЗДЕСЬ
# Для добавления нового актива добавьте запись в ASSETS_CONFIG
# ============================================================================

ASSETS_CONFIG: Dict[str, AssetConfig] = {
    # ================= КРИПТОВАЛЮТЫ =================
    "btc": AssetConfig(
        symbol="btc",
        name="Bitcoin",
        asset_type=AssetType.CRYPTO,
        emoji="₿",
        display_precision=6,
        price_source="coingecko",
        source_id="bitcoin",
        aliases=["bitcoin"],
        description="Первая и самая известная криптовалюта"
    ),

    "eth": AssetConfig(
        symbol="eth",
        name="Ethereum",
        asset_type=AssetType.CRYPTO,
        emoji="Ξ",
        display_precision=4,
        price_source="coingecko",
        source_id="ethereum",
        aliases=["ethereum"],
        description="Платформа для смарт-контрактов"
    ),

    "ton": AssetConfig(
        symbol="ton",
        name="TON",
        asset_type=AssetType.CRYPTO,
        emoji="⚡",
        display_precision=2,
        price_source="coingecko",
        source_id="the-open-network",
        aliases=["toncoin", "the-open-network"],
        description="Криптовалюта от Telegram"
    ),

    "sol": AssetConfig(
        symbol="sol",
        name="Solana",
        asset_type=AssetType.CRYPTO,
        emoji="🟣",
        display_precision=2,
        price_source="coingecko",
        source_id="solana",
        aliases=["solana"],
        description="Быстрый blockchain с низкими комиссиями"
    ),

    "usdt": AssetConfig(
        symbol="usdt",
        name="Tether",
        asset_type=AssetType.CRYPTO,
        emoji="💵",
        display_precision=2,
        price_source="coingecko",
        source_id="tether",
        aliases=["tether"],
        description="Стейблкоин привязанный к доллару США"
    ),

    # ================= АКЦИИ =================
    # Пример - раскомментируйте при необходимости
    # "aapl": AssetConfig(
    #     symbol="aapl",
    #     name="Apple Inc",
    #     asset_type=AssetType.STOCK,
    #     emoji="🍎",
    #     display_precision=2,
    #     price_source="yahoo_finance",
    #     source_id="AAPL",
    #     description="Акции Apple"
    # ),

    # ================= ETF =================
    # "spy": AssetConfig(
    #     symbol="spy",
    #     name="SPDR S&P 500 ETF",
    #     asset_type=AssetType.ETF,
    #     emoji="📈",
    #     display_precision=2,
    #     price_source="yahoo_finance",
    #     source_id="SPY",
    #     description="ETF на индекс S&P 500"
    # ),
}


# ============================================================================
# Вспомогательные функции для работы с активами
# ============================================================================

def get_asset_config(symbol: str) -> AssetConfig:
    """Получает конфигурацию актива по символу"""
    symbol_lower = symbol.lower()

    # Прямой поиск
    if symbol_lower in ASSETS_CONFIG:
        return ASSETS_CONFIG[symbol_lower]

    # Поиск по алиасам
    for asset_config in ASSETS_CONFIG.values():
        if symbol_lower in asset_config.aliases or symbol_lower == asset_config.source_id:
            return asset_config

    raise ValueError(f"Asset '{symbol}' not found in configuration")


def get_all_assets() -> List[AssetConfig]:
    """Возвращает список всех активов"""
    return list(ASSETS_CONFIG.values())


def get_enabled_assets() -> List[AssetConfig]:
    """Возвращает список включенных активов"""
    return [asset for asset in ASSETS_CONFIG.values() if asset.enabled]


def get_assets_by_type(asset_type: AssetType) -> List[AssetConfig]:
    """Возвращает активы по типу"""
    return [asset for asset in ASSETS_CONFIG.values()
            if asset.asset_type == asset_type and asset.enabled]


def get_crypto_assets() -> List[AssetConfig]:
    """Возвращает список криптовалют"""
    return get_assets_by_type(AssetType.CRYPTO)


def is_asset_supported(symbol: str) -> bool:
    """Проверяет, поддерживается ли актив"""
    try:
        get_asset_config(symbol)
        return True
    except ValueError:
        return False


def format_amount(amount: float, symbol: str) -> str:
    """Форматирует количество согласно настройкам актива"""
    config = get_asset_config(symbol)
    return f"{amount:.{config.display_precision}f}"