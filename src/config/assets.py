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
    FIAT = "fiat"
    PRECIOUS_METAL = "precious_metal"
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    COMMODITY = "commodity"
    RECEIVABLE = "receivable"


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

    # Для фиатных валют и металлов
    base_currency: str = "USD"  # Базовая валюта для конвертации
    exchange_rate: float = 1.0  # Курс к базовой валюте (по умолчанию 1:1)

    # Для металлов
    weight_per_unit: float = 1.0  # Вес в граммах на одну единицу
    metal_premium: float = 1.0  # Надбавка к цене (1.10 = +10%)

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

        # Для металлов source_id должен совпадать с символами в MetalService
        if self.asset_type == AssetType.PRECIOUS_METAL and self.price_source == "cbr_metals":
            # Маппинг символов на коды в MetalService
            metal_mapping = {
                "gold": "gold",
                "silver": "silver",
                "platinum": "platinum",
                "palladium": "palladium"
            }
            if self.symbol in metal_mapping:
                self.source_id = metal_mapping[self.symbol]


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

    # ================= ФИАТНЫЕ ВАЛЮТЫ (НАЛИЧНЫЕ) =================
    "rub": AssetConfig(
        symbol="rub",
        name="Рубли",
        asset_type=AssetType.FIAT,
        emoji="₽",
        display_precision=2,
        price_source="cbr",
        base_currency="USD",
        exchange_rate=0.011,  # Примерный курс: 1 RUB = 0.011 USD
        aliases=["ruble", "rouble", "российский рубль"],
        description="Российский рубль",
        min_amount=1.0,
        max_amount=10000000
    ),

    "usd": AssetConfig(
        symbol="usd",
        name="Доллары США",
        asset_type=AssetType.FIAT,
        emoji="💵",
        display_precision=2,
        price_source="cbr",
        base_currency="USD",
        exchange_rate=1.0,
        aliases=["dollar", "us dollar", "доллар"],
        description="Доллар США",
        min_amount=0.01,
        max_amount=1000000
    ),

    "cny": AssetConfig(
        symbol="cny",
        name="Юань",
        asset_type=AssetType.FIAT,
        emoji="¥",
        display_precision=2,
        price_source="cbr",
        base_currency="USD",
        exchange_rate=0.14,  # Примерный курс: 1 CNY = 0.14 USD
        aliases=["yuan", "китайский юань"],
        description="Китайский юань",
        min_amount=1.0,
        max_amount=10000000
    ),

    "eur": AssetConfig(
        symbol="eur",
        name="Евро",
        asset_type=AssetType.FIAT,
        emoji="💶",
        display_precision=2,
        price_source="cbr",
        base_currency="USD",
        exchange_rate=1.08,  # Примерный курс: 1 EUR = 1.08 USD
        aliases=["euro", "евро"],
        description="Евро",
        min_amount=0.01,
        max_amount=1000000
    ),

    "kzt": AssetConfig(
        symbol="kzt",
        name="Тенге",
        asset_type=AssetType.FIAT,
        emoji="₸",
        display_precision=2,
        price_source="cbr",
        base_currency="USD",
        exchange_rate=0.0021,  # Примерный курс: 1 KZT = 0.0021 USD
        aliases=["tenge", "казахстанский тенге"],
        description="Казахстанский тенге",
        min_amount=1.0,
        max_amount=10000000
    ),

    "uah": AssetConfig(
        symbol="uah",
        name="Гривна",
        asset_type=AssetType.FIAT,
        emoji="₴",
        display_precision=2,
        price_source="cbr",
        base_currency="USD",
        exchange_rate=0.026,  # Примерный курс: 1 UAH = 0.026 USD
        aliases=["hryvnia", "гривна", "украинская гривна"],
        description="Украинская гривна",
        min_amount=1.0,
        max_amount=10000000
    ),

    # ================= ДРАГОЦЕННЫЕ МЕТАЛЛЫ (БАЗОВЫЕ) =================
    "gold": AssetConfig(
        symbol="gold",
        name="Золото",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="🥇",
        display_precision=4,
        price_source="cbr_metals",  # Новый источник цен
        source_id="gold",  # Сопоставляется с metal_service
        base_currency="RUB",  # Основная валюта - рубли
        exchange_rate=1.0,
        weight_per_unit=1.0,  # 1 единица = 1 грамм
        aliases=["золото", "gold_gram", "gold_1g", "au"],
        description="Золото (цена за 1 грамм). Учетная цена ЦБ РФ.",
        min_amount=0.1,
        max_amount=100000
    ),

    "silver": AssetConfig(
        symbol="silver",
        name="Серебро",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="🥈",
        display_precision=4,
        price_source="cbr_metals",
        source_id="silver",
        base_currency="RUB",
        exchange_rate=1.0,
        weight_per_unit=1.0,  # 1 единица = 1 грамм
        aliases=["серебро", "silver_gram", "silver_1g", "ag"],
        description="Серебро (цена за 1 грамм). Учетная цена ЦБ РФ.",
        min_amount=1.0,
        max_amount=1000000
    ),

    "platinum": AssetConfig(
        symbol="platinum",
        name="Платина",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="⚪",
        display_precision=4,
        price_source="cbr_metals",
        source_id="platinum",
        base_currency="RUB",
        exchange_rate=1.0,
        weight_per_unit=1.0,  # 1 единица = 1 грамм
        aliases=["платина", "platinum_gram", "platinum_1g", "pt"],
        description="Платина (цена за 1 грамм). Учетная цена ЦБ РФ.",
        min_amount=0.1,
        max_amount=100000
    ),

    "palladium": AssetConfig(
        symbol="palladium",
        name="Палладий",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="🔘",
        display_precision=4,
        price_source="cbr_metals",
        source_id="palladium",
        base_currency="RUB",
        exchange_rate=1.0,
        weight_per_unit=1.0,  # 1 единица = 1 грамм
        aliases=["палладий", "palladium_gram", "palladium_1g", "pd"],
        description="Палладий (цена за 1 грамм). Учетная цена ЦБ РФ.",
        min_amount=0.1,
        max_amount=100000
    ),

    # ================= ДРАГОЦЕННЫЕ МЕТАЛЛЫ (КОНКРЕТНЫЕ ИЗДЕЛИЯ) =================
    "gold_coin_7_78": AssetConfig(
        symbol="gold_coin_7_78",
        name="Золотая монета 7.78г",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="🥇",
        display_precision=4,
        price_source="precious_metal",
        source_id="gold",
        base_currency="RUB",
        exchange_rate=7.78,
        weight_per_unit=7.78,
        metal_premium=1.10,  # Надбавка 10% для золотых монет
        description="Золотая монета весом 7.78 грамм (1/4 тройской унции). "
                    "Цена рассчитывается как цена золота × 7.78 × 1.10",
        min_amount=0.1,
        max_amount=100,
        aliases=["золотая монета 7.78", "gold coin 7.78g", "gold_quarter_oz"]
    ),

    "gold_coin_15_55": AssetConfig(
        symbol="gold_coin_15_55",
        name="Золотая монета 15.55г",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="🏅",
        display_precision=4,
        price_source="precious_metal",
        source_id="gold",
        base_currency="RUB",
        exchange_rate=15.55,
        weight_per_unit=15.55,
        metal_premium=1.10,  # Надбавка 10% для золотых монет
        description="Золотая монета весом 15.55 грамм (1/2 тройской унции). "
                    "Цена рассчитывается как цена золота × 15.55 × 1.10",
        min_amount=0.1,
        max_amount=100,
        aliases=["золотая монета 15.55", "gold coin 15.55g", "gold_half_oz"]
    ),

    "silver_coin_31_1": AssetConfig(
        symbol="silver_coin_31_1",
        name="Серебряная монета 31.1г",
        asset_type=AssetType.PRECIOUS_METAL,
        emoji="🥈",
        display_precision=4,
        price_source="precious_metal",
        source_id="silver",
        base_currency="RUB",
        exchange_rate=31.1,
        weight_per_unit=31.1,
        metal_premium=1.20,  # Надбавка 20% для серебряных монет
        description="Серебряная монета весом 31.1 грамм (1 тройская унция). "
                    "Цена рассчитывается как цена серебра × 31.1 × 1.20",
        min_amount=0.1,
        max_amount=1000,
        aliases=["серебряная монета 31.1", "silver coin 31.1g", "silver_ounce"]
    ),

    # ================= ДЕБИТОРСКАЯ ЗАДОЛЖЕННОСТЬ =================
    "receivable_ecm": AssetConfig(
        symbol="receivable_ecm",
        name="Дебиторская задолженность (ЕЦМ)",
        asset_type=AssetType.RECEIVABLE,
        emoji="🧾",
        display_precision=2,
        price_source="static",
        description="Дебиторская задолженность компании ЕЦМ",
        min_amount=100,
        max_amount=10000000,
        aliases=["есм", "ecm", "дебиторка есм", "задолженность есм"]
    ),

    "receivable_ozon": AssetConfig(
        symbol="receivable_ozon",
        name="Дебиторская задолженность (Ozon)",
        asset_type=AssetType.RECEIVABLE,
        emoji="📦",
        display_precision=2,
        price_source="static",
        description="Дебиторская задолженность компании Ozon",
        min_amount=100,
        max_amount=10000000,
        aliases=["озон", "ozon", "дебиторка озона", "задолженность озона"]
    ),

    # ================= ТОВАРЫ =================
    "product_1": AssetConfig(
        symbol="product_1",
        name="Приборы класик 24",
        asset_type=AssetType.COMMODITY,
        emoji="⚗️",
        display_precision=0,
        price_source="static",
        description="Комплект приборов Классик 24 штуки",
        min_amount=1,
        max_amount=1000,
        aliases=["приборы_классик_24", "классик_24", "instruments_classic_24"]
    ),

    "product_2": AssetConfig(
        symbol="product_2",
        name="Приборы класик 16",
        asset_type=AssetType.COMMODITY,
        emoji="⚗️",
        display_precision=0,
        price_source="static",
        description="Комплект приборов Классик 16 штук",
        min_amount=1,
        max_amount=1000,
        aliases=["приборы_классик_16", "классик_16", "instruments_classic_16"]
    ),

    "product_3": AssetConfig(
        symbol="product_3",
        name="Приборы класик 24 зол",
        asset_type=AssetType.COMMODITY,
        emoji="⚗️",
        display_precision=0,
        price_source="static",
        description="Комплект приборов Классик 24 штуки золото",
        min_amount=1,
        max_amount=1000,
        aliases=["приборы_классик_24_зол", "классик_24_зол", "instruments_classic_24_gold"]
    ),

    "product_4": AssetConfig(
        symbol="product_4",
        name="Приборы Флора 24",
        asset_type=AssetType.COMMODITY,
        emoji="⚗️",
        display_precision=0,
        price_source="static",
        description="Комплект приборов Флора 24 штуки",
        min_amount=1,
        max_amount=1000,
        aliases=["приборы_флора_24", "флора_24", "instruments_flora_24"]
    ),

    "product_5": AssetConfig(
        symbol="product_5",
        name="Анализатор",
        asset_type=AssetType.COMMODITY,
        emoji="🔬",
        display_precision=0,
        price_source="static",
        description="Аналитический прибор анализатор",
        min_amount=1,
        max_amount=100,
        aliases=["анализатор", "analizer", "analyzer"]
    ),

    "product_6": AssetConfig(
        symbol="product_6",
        name="Гитара 1007 SN",
        asset_type=AssetType.COMMODITY,
        emoji="🎸",
        display_precision=0,
        price_source="static",
        description="Гитара модели 1007 SN",
        min_amount=1,
        max_amount=100,
        aliases=["гитара_1007", "guitar_1007_sn", "1007_sn"]
    ),

    # ================= ETF =================
    "fxgd": AssetConfig(
        symbol="fxgd",
        name="FinEx Физическое золото",
        asset_type=AssetType.ETF,
        emoji="🏅",
        display_precision=2,
        price_source="moex",
        source_id="FXGD",
        aliases=["finex_gold", "золотой_etf", "etf_золото", "физическое_золото", "fxgd_rub"],
        description="Биржевой инвестиционный фонд FinEx Физическое золото (тикер: FXGD). "
                    "Каждая акция соответствует 0.1 грамма золота. Торгуется на Московской бирже.",
        min_amount=0.01,
        max_amount=1000000,
        enabled=True
    ),
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


def get_fiat_assets() -> List[AssetConfig]:
    """Возвращает список фиатных валют"""
    return get_assets_by_type(AssetType.FIAT)


def get_precious_metal_assets() -> List[AssetConfig]:
    """Возвращает список активов из драгоценных металлов"""
    return get_assets_by_type(AssetType.PRECIOUS_METAL)


def get_basic_metal_assets() -> List[AssetConfig]:
    """Возвращает список базовых металлов (без конкретных изделий)"""
    basic_metals = []
    for asset in ASSETS_CONFIG.values():
        if (asset.asset_type == AssetType.PRECIOUS_METAL and
                asset.price_source == "cbr_metals" and
                asset.symbol in ["gold", "silver", "platinum", "palladium"]):
            basic_metals.append(asset)
    return basic_metals


def get_metal_product_assets() -> List[AssetConfig]:
    """Возвращает список изделий из драгоценных металлов"""
    metal_products = []
    for asset in ASSETS_CONFIG.values():
        if (asset.asset_type == AssetType.PRECIOUS_METAL and
                asset.price_source == "precious_metal"):
            metal_products.append(asset)
    return metal_products


def get_gold_assets() -> List[AssetConfig]:
    """Возвращает список золотых активов"""
    gold_assets = []
    for asset in ASSETS_CONFIG.values():
        if asset.asset_type == AssetType.PRECIOUS_METAL and "gold" in asset.symbol:
            gold_assets.append(asset)
    return gold_assets


def get_silver_assets() -> List[AssetConfig]:
    """Возвращает список серебряных активов"""
    silver_assets = []
    for asset in ASSETS_CONFIG.values():
        if asset.asset_type == AssetType.PRECIOUS_METAL and "silver" in asset.symbol:
            silver_assets.append(asset)
    return silver_assets


def is_asset_supported(symbol: str) -> bool:
    """Проверяет, поддерживается ли актив"""
    try:
        get_asset_config(symbol)
        return True
    except ValueError:
        return False


def get_commodity_assets() -> List[AssetConfig]:
    """Возвращает список товаров"""
    return get_assets_by_type(AssetType.COMMODITY)


def get_receivable_assets() -> List[AssetConfig]:
    """Возвращает список дебиторской задолженности"""
    return get_assets_by_type(AssetType.RECEIVABLE)


def get_etf_assets() -> List[AssetConfig]:
    """Возвращает список ETF"""
    return get_assets_by_type(AssetType.ETF)


def format_amount(amount: float, symbol: str) -> str:
    """Форматирует количество согласно настройкам актива"""
    config = get_asset_config(symbol)
    return f"{amount:.{config.display_precision}f}"


def get_metal_price_multiplier(symbol: str) -> float:
    """Возвращает множитель цены для металлических изделий"""
    config = get_asset_config(symbol)
    if config.asset_type == AssetType.PRECIOUS_METAL:
        return config.weight_per_unit
    return 1.0