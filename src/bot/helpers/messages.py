# src/bot/helpers/messages.py
"""
Готовые текстовые сообщения для команд.
"""

from typing import List, Dict, Any, Optional
from ..helpers.formatters import format_currency, format_timestamp
from ...services.currency_service import currency_service


def get_welcome_message(username: str) -> str:
    """Сообщение для команды /start"""
    return f"""
👋 Добро пожаловать, {username}!

Я — ваш инвестиционный помощник. Отслеживайте стоимость активов, управляйте портфелем и будьте в курсе рыночных тенденций.

🚀 Быстрый старт:
/add btc 0.1 — добавить Bitcoin
/portfolio — посмотреть портфель
/prices — текущие цены

📊 Управление портфелем:
/portfolio — Ваши активы
/add — Добавить актив
/remove — Удалить актив
/clear — Очистить всё

📈 Информация:
/coins — Криптовалюты
/currencies — Валюты
/metals — Драгоценные металлы
/products — Товары
/etfs — ETF фонды

⚙️ Система:
/stats — Статистика
/settings — Настройки
/help — Помощь

💡 Начните с добавления первого актива!
"""


def get_help_message(username: str) -> str:
    """Сообщение для команды /help"""
    return f"""
📚 Центр помощи, {username}

📋 Основные команды:
/portfolio — Показать мой портфель
/prices — Текущие цены крипто
/stats — Статистика бота

💼 Управление активами:
/add <символ> <количество> — Добавить актив
/remove <символ> [количество] — Удалить актив
/clear confirm — Очистить портфель

📊 Списки активов:
/coins — Криптовалюты
/currencies — Валюты
/metals — Драгоценные металлы
/products — Товары
/etfs — ETF фонды
/receivables — Дебиторская задолженность

⚙️ Настройки:
/settings — Настройки профиля
/start — Перезапустить бота

💡 Примеры использования:
/add btc 0.5 — купить 0.5 BTC
/add eth 2.0 — добавить 2 ETH
/remove ton 50 — продать 50 TON
/add rub 10000 — добавить 10,000 рублей

"""


def get_settings_message(username: str, settings: Dict, stats: Dict) -> str:
    """Сообщение для команды /settings"""
    return f"""
⚙️ Настройки {username}

📊 Статистика:
Активов в портфеле: {stats.get('total_assets', 0)}
Валюта: {settings.get('currency', 'USD')}
Уведомления: {'✅ Вкл' if settings.get('notifications', True) else '❌ Выкл'}

🔧 Функции настроек пока в разработке.

💡 Скоро здесь можно будет:
• Изменить валюту отображения
• Настроить уведомления
• Выбрать тему оформления
• И другие настройки
"""

def get_empty_portfolio_message(username: str, supported_assets: str) -> str:
    """Сообщение для пустого портфеля"""
    return f"""
📭 Портфель {username} пуст

✨ Используйте /add чтобы начать инвестировать!

📋 Поддерживаемые активы:
{supported_assets}

💡 Примеры:
/add btc 0.1 — добавить Bitcoin
/add eth 2.0 — добавить Ethereum
/add rub 10000 — добавить рубли

🚀 Начните с самого простого — добавьте немного криптовалюты или валюты!
"""


def get_portfolio_message(
        username: str,
        assets_info: List[Dict],
        total_value: float,
        last_updated: str,
        assets_count: int,
        total_value_rub: float = None
) -> str:
    """Сообщение для портфеля с активами"""
    from ...services.currency_service import currency_service

    # Рассчитываем RUB если не передано
    if total_value_rub is None:
        total_value_rub = currency_service.usd_to_rub_real_sync(total_value)

    # Получаем курсы
    real_rate = currency_service.get_real_usd_rub_rate_sync()
    cbr_rate = currency_service.get_cbr_usd_rub_rate_sync()

    message = f"📊 Портфель {username}\n\n"

    # Активы
    for asset in assets_info:
        message += f"{asset.get('emoji', '•')} {asset.get('name', asset.get('symbol', ''))}\n"
        message += f"  Количество: {asset.get('amount_formatted', '0')}\n"

        if asset.get('price_usd'):
            message += f"  Цена: ${asset['price_usd']:.2f} | {currency_service.format_rub(asset.get('price_rub', 0))}\n"
            message += f"  Стоимость: ${asset.get('value_usd', 0):.2f} | {currency_service.format_rub(asset.get('value_rub', 0))}\n"
        else:
            message += f"  Цена: ❌ недоступна\n"
            message += f"  Стоимость: ❌ недоступна\n"

        message += "\n"

    # Итог
    message += "─" * 25 + "\n"
    message += f"💰 Общая стоимость:\n"
    message += f"  USD: ${total_value:,.2f}\n"
    message += f"  RUB: {currency_service.format_rub(total_value_rub)}\n\n"

    # Курсы как в /currencies
    message += f"💱 Курсы:\n"
    message += f"  1 USD = {real_rate:.2f} ₽ (реальный)\n"
    message += f"  1 USD = {cbr_rate:.2f} ₽ (ЦБ РФ)\n\n"

    # Инфо
    message += f"📈 Активов: {assets_count}\n"
    if last_updated:
        message += f"🔄 Обновлено: {last_updated}\n\n"

    message += "💡 /remove <символ> — удалить актив"

    return message


def get_crypto_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком криптовалют"""
    if not assets:
        return "❌ Нет доступных криптовалют\nПожалуйста, попробуйте позже."

    # Группировка по популярности
    major_coins = ["btc", "eth", "ton", "usdt", "sol"]
    major_assets = [a for a in assets if a.symbol in major_coins]
    other_assets = [a for a in assets if a.symbol not in major_coins]

    message = "🏦 Криптовалюты\n\n"

    # Основные криптовалюты
    if major_assets:
        message += "💰 Основные:\n"
        for asset in major_assets:
            price_info = prices_info.get(asset.symbol, {})
            price_usd = price_info.get("price_usd")
            price_rub = price_info.get("price_rub")

            message += f"{asset.config.emoji} {asset.config.name} ({asset.symbol.upper()})\n"

            if price_usd:
                if not price_rub:
                    price_rub = currency_service.usd_to_rub(price_usd)

                message += f"  Цена: ${price_usd:,.4f} | {currency_service.format_rub(price_rub)}\n"
                if change := price_info.get("change_24h"):
                    arrow = "📈" if change >= 0 else "📉"
                    message += f"  24ч: {arrow} {change:+.1f}%\n"

            message += f"  Пример: /add {asset.symbol} "

            # Примерные количества
            examples = {
                "btc": "0.01", "eth": "0.1", "ton": "10",
                "usdt": "100", "sol": "1.0"
            }
            message += f"{examples.get(asset.symbol, '1.0')}\n\n"

    # Другие криптовалюты
    if other_assets:
        message += "🔹 Другие:\n"
        for asset in other_assets:
            price_info = prices_info.get(asset.symbol, {})
            price_usd = price_info.get("price_usd")

            line = f"{asset.config.emoji} {asset.config.name} ({asset.symbol.upper()})"
            if price_usd:
                price_rub = price_info.get("price_rub", currency_service.usd_to_rub(price_usd))
                line += f" — ${price_usd:.4f} | {currency_service.format_rub(price_rub)}"

            message += f"{line}\n"

    # Разделитель и подсказки
    message += "─" * 25 + "\n"
    message += "💡 Примеры:\n"
    message += "/add btc 0.1 — купить Bitcoin\n"
    message += "/portfolio — посмотреть портфель\n"
    message += "/prices — текущие цены\n"
    message += "/stats — статистика бота\n\n"

    return message


def get_fiat_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком фиатных валют"""
    if not assets:
        return "❌ Нет доступных фиатных валют\nПожалуйста, попробуйте позже."

    # Получаем курсы
    real_rate = currency_service.get_real_usd_rub_rate_sync()
    cbr_rate = currency_service.get_cbr_usd_rub_rate_sync()

    message = "💵 Валюты\n\n"

    for asset in assets:
        price_info = prices_info.get(asset.symbol, {})
        price_usd = price_info.get("price_usd")

        message += f"{asset.config.emoji} {asset.config.name} ({asset.symbol.upper()})\n"

        if asset.symbol.lower() == "usd":
            # Особый случай для USD
            message += f"  1 USD = 1.0000 USD\n"
            message += f"  1 USD = {cbr_rate:.2f} ₽ (ЦБ РФ)\n"
            message += f"  1 USD = {real_rate:.2f} ₽ (реальный +2 ₽)\n"
        elif price_usd:
            # Другие валюты
            price_rub = currency_service.usd_to_rub_real_sync(price_usd)
            message += f"  1 {asset.symbol.upper()} = ${price_usd:.4f}\n"
            message += f"  1 {asset.symbol.upper()} = {currency_service.format_rub(price_rub)}\n"

            # Прямой курс от ЦБ если доступен
            if hasattr(currency_service, 'get_currency_to_rub_rate_sync'):
                direct_rate = currency_service.get_currency_to_rub_rate_sync(asset.symbol.lower())
                if direct_rate:
                    message += f"  1 {asset.symbol.upper()} = {currency_service.format_rub(direct_rate)} (ЦБ РФ)\n"
        else:
            message += "  Курс: ❌ временно недоступен\n"

        # Пример добавления
        examples = {"rub": "1000", "eur": "100", "usd": "100"}
        example = examples.get(asset.symbol.lower(), "100")
        message += f"  Пример: /add {asset.symbol} {example}\n\n"

    # Информация о курсах
    message += "─" * 25 + "\n"
    message += "💱 Курсы обмена:\n"
    message += f"  ЦБ РФ: 1 USD = {cbr_rate:.2f} ₽\n"
    message += f"  Реальный: 1 USD = {real_rate:.2f} ₽ (+2 ₽ к ЦБ)\n\n"

    message += "💡 Как использовать:\n"
    message += "/add rub 10000 — добавить рубли\n"
    message += "/add eur 500 — добавить евро\n"
    message += "/portfolio — общая стоимость в USD\n\n"

    return message


def get_metals_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком драгоценных металлов"""
    if not assets:
        return "❌ Нет доступных драгоценных металлов\nПожалуйста, попробуйте позже."

    message = "🥇 Драгоценные металлы\n\n"

    # Группируем по типу металла
    gold_assets = [a for a in assets if "gold" in a.symbol]
    silver_assets = [a for a in assets if "silver" in a.symbol]

    # Золото
    if gold_assets:
        message += "💰 Золото:\n"
        for asset in gold_assets:
            price_info = prices_info.get(asset.symbol, {})

            message += f"{asset.config.emoji} {asset.config.name}\n"

            if hasattr(asset, 'get_metal_info'):
                info = asset.get_metal_info()
                message += f"  Вес: {info['weight_g']}g ({info['weight_oz']:.2f} oz)\n"
                message += f"  Чистота: {info['purity'] * 100:.1f}%\n"

            if price := price_info.get("price"):
                message += f"  Цена: ${price:.2f}\n"
                if price_rub := price_info.get("price_rub"):
                    message += f"  Цена: {currency_service.format_rub(price_rub)}\n"

            message += f"  Пример: /add {asset.symbol} 1\n\n"

    # Серебро
    if silver_assets:
        message += "🥈 Серебро:\n"
        for asset in silver_assets:
            price_info = prices_info.get(asset.symbol, {})

            message += f"{asset.config.emoji} {asset.config.name}\n"

            if hasattr(asset, 'get_metal_info'):
                info = asset.get_metal_info()
                message += f"  Вес: {info['weight_g']}g ({info['weight_oz']:.2f} oz)\n"
                message += f"  Чистота: {info['purity'] * 100:.1f}%\n"

            if price := price_info.get("price"):
                message += f"  Цена: ${price:.2f}\n"
                if price_rub := price_info.get("price_rub"):
                    message += f"  Цена: {currency_service.format_rub(price_rub)}\n"

            message += f"  Пример: /add {asset.symbol} 1\n\n"

    # Разделитель и информация
    message += "─" * 25 + "\n"
    message += "💡 Как использовать:\n"
    message += "/add gold_coin_7_78 2 — добавить 2 золотые монеты\n"
    message += "/add silver_coin_31_1 5 — добавить 5 серебряных\n"
    message += "/portfolio — посмотреть общую стоимость\n\n"

    message += "📊 Особенности:\n"
    message += "• Цены на основе биржевых котировок\n"
    message += "• Вес указан в граммах и унциях\n"

    return message


def get_products_assets_message(assets: List, prices_info: Dict = None) -> str:
    """Сообщение со списком товаров"""
    from src.config.settings import settings  # Импортируем settings

    if not assets:
        return "❌ Нет доступных товаров\nТовары еще не добавлены."

    message = "📦 Товары\n\n"

    for asset in assets:
        # Получаем цену в рублях из настроек
        price_rub = settings.PRODUCTS_PRICES.get(asset.symbol)

        message += f"{asset.config.emoji} {asset.config.name}\n"
        message += f"  Код: {asset.symbol}\n"

        if price_rub:
            # Показываем цену в рублях (исходная валюта)
            message += f"  Цена: {currency_service.format_rub(price_rub)}\n"

            # Конвертируем в USD
            price_usd = currency_service.convert_to_usd_sync(price_rub, "rub")
            if price_usd is None:
                usd_to_rub_rate = currency_service.get_real_usd_rub_rate_sync()
                price_usd = price_rub / usd_to_rub_rate if usd_to_rub_rate > 0 else 0

            message += f"  Цена: ${price_usd:,.2f}\n"
        else:
            message += f"  Цена: уточняется\n"

        message += f"  Пример: /add {asset.symbol} 1\n\n"

    # Разделитель
    message += "─" * 25 + "\n"

    # Информация
    message += "💡 Как работать с товарами:\n"
    message += "/add product_1 5 — добавить 5 комплектов приборов\n"
    message += "/add product_5 1 — добавить анализатор\n"
    message += "/portfolio — общая стоимость\n\n"

    message += "📊 Особенности:\n"
    message += "• Цены в рублях (из настроек)\n"
    message += "• Количество в натуральных единицах\n"
    message += "• Автоматическая конвертация в USD/RUB\n"
    message += "• Для обновления цен: /update_product_price\n"

    return message


def get_receivables_assets_message(assets: List) -> str:
    """Сообщение со списком дебиторской задолженности"""
    if not assets:
        return "❌ Нет доступной дебиторской задолженности"

    message = "🧾 Дебиторская задолженность\n\n"

    for asset in assets:
        # Получаем дисконт
        discount = getattr(asset, 'discount_factor', {}).get(asset.symbol, 1.0)
        discount_percent = (1 - discount) * 100

        message += f"{asset.config.emoji} {asset.config.name}\n"
        message += f"  Код: {asset.symbol}\n"
        message += f"  Дисконт: {discount_percent:.1f}%\n"

        # Базовая стоимость (номинал)
        if hasattr(asset, 'config') and hasattr(asset.config, 'nominal_value'):
            nominal = asset.config.nominal_value
            discounted = nominal * discount

            message += f"  Номинал: ${nominal:,.0f}\n"
            message += f"  С учетом дисконта: ${discounted:,.0f}\n"

            # В рублях
            rub_value = currency_service.usd_to_rub_real_sync(discounted)
            message += f"  Стоимость: {currency_service.format_rub(rub_value)}\n"

        message += f"  Пример: /add {asset.symbol} 50000\n\n"

    # Разделитель
    message += "─" * 25 + "\n"

    # Объяснение
    message += "💡 Что такое дебиторская задолженность:\n"
    message += "• Долги, которые вам должны вернуть\n"
    message += "• Учитываются с дисконтом (риск непогашения)\n"
    message += "• Отображаются в портфеле по дисконтированной стоимости\n\n"

    message += "📊 Как использовать:\n"
    message += "/add receivable_ecm 100000 — добавить $100,000\n"
    message += "/portfolio — стоимость с учетом дисконта\n"
    message += "/remove receivable_ecm 50000 — списать $50,000\n\n"

    message += "⚠️  Риски:\n"
    message += "• Возможность неполного погашения\n"
    message += "• Изменение дисконта со временем\n"

    return message


def get_etf_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком ETF"""
    if not assets:
        return "❌ Нет доступных ETF\nETF еще не добавлены."

    message = "📊 ETF (биржевые фонды)\n\n"

    for asset in assets:
        price_info = prices_info.get(asset.symbol, {})
        price = price_info.get("price")

        message += f"{asset.config.emoji} {asset.config.name}\n"
        message += f"  Тикер: {asset.symbol.upper()}\n"

        if price:
            # Определяем валюту и форматируем
            if asset.symbol == "fxgd":
                message += f"  Цена: {price:,.2f} ₽\n"
                price_rub = price  # FXGD уже в рублях
            else:
                message += f"  Цена: ${price:.2f}\n"
                price_rub = currency_service.usd_to_rub_real_sync(price)
                message += f"  Цена: {currency_service.format_rub(price_rub)}\n"

        # Специфичная информация
        if asset.symbol == "fxgd":
            message += f"  Комиссия: 0.45% годовых\n"
            message += f"  1 акция ≈ 0.1g золота\n"
            message += f"  Биржа: MOEX (Москва)\n"

        message += f"  Пример: /add {asset.symbol} 10\n\n"

    # Разделитель
    message += "─" * 25 + "\n"

    # Объяснение ETF
    message += "💡 Что такое ETF:\n"
    message += "• Биржевой инвестиционный фонд\n"
    message += "• Торгуется как обычные акции\n"
    message += "• Следует за индексом или активом\n"
    message += "• Низкий порог входа\n\n"

    message += "📈 Преимущества FXGD:\n"
    message += "• Ликвидность (торгуется на MOEX)\n"
    message += "• Физическое обеспечение золотом\n"
    message += "• Прозрачная структура\n"
    message += "• Низкие комиссии (0.45%)\n\n"

    message += "🚀 Как инвестировать:\n"
    message += "/add fxgd 10 — купить 10 акций\n"
    message += "/portfolio — отслеживать стоимость\n"
    message += "/prices — текущие котировки\n"

    return message