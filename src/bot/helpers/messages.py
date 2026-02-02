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
👋 Привет, {username}!

Я — бот для отслеживания стоимости портфеля.

📊 **Доступные команды:**
/portfolio — Посмотреть мой портфель
/add — Добавить актив
/remove — Удалить актив
/prices — Текущие цены крипто
/coins — Список криптовалют
/currencies — Список валют
/metals — Драгоценные металлы
/products — Товары
/receivables — Дебиторская задолженность
/etfs — список всех ETF
/settings — Настройки
/help — Помощь и инструкции

💰 **Бот автоматически:**
• Отслеживает текущие цены
• Конвертирует все активы в USD
• Сохраняет ваш портфель
• Показывает общую стоимость

_Начните с добавления первого актива!_
"""


def get_help_message(username: str) -> str:
    """Сообщение для команды /help"""
    return f"""
📚 **Помощь по использованию бота**

**Основные команды:**
/start — Начать работу
/portfolio — Показать текущий портфель
/add — Добавить актив в портфель
/remove — Удалить актив из портфеля
/prices — Текущие цены криптовалют
/coins — Список всех криптовалют
/currencies — Список валют
/receivables — Дебиторская задолженность
/etfs — список всех ETF
/settings — Настройки бота
/help — Эта справка

**Как добавить актив:**
`/add btc 0.5` — добавить 0.5 BTC
`/add eth 2.0` — добавить 2 ETH
`/add ton 100` — добавить 100 TON

**Как удалить актив:**
`/remove btc` — удалить весь BTC
`/remove eth 1.0` — удалить 1 ETH
`/remove ton 50` — удалить 50 TON

🔄 **Нужна помощь?** Просто напишите /start чтобы начать заново.
"""


def get_settings_message(username: str, settings: Dict, stats: Dict) -> str:
    """Сообщение для команды /settings"""
    return f"""
⚙️ **Настройки {username}**

**📊 Ваша статистика:**
• Активов в портфеле: {stats.get('total_assets', 0)}
• Валюта: {settings.get('currency', 'USD')}
• Уведомления: {'Включены' if settings.get('notifications', True) else 'Выключены'}

**🔧 Доступные настройки:**
• `/settings currency USD` — изменить валюту
• `/settings notifications on` — включить уведомления
• `/settings notifications off` — выключить уведомления

💡 _Больше настроек скоро будут доступны!_
"""


def get_empty_portfolio_message(username: str, supported_assets: str) -> str:
    """Сообщение для пустого портфеля"""
    return f"""
📭 **Портфель {username} пуст**

Используйте команду `/add` чтобы добавить активы.

**Поддерживаемые активы:**
{supported_assets}

_Пример: `/add btc 0.1` чтобы добавить 0.1 Bitcoin_
"""


def get_portfolio_message(
        username: str,
        assets_info: List[Dict],
        total_value: float,
        last_updated: str,
        assets_count: int
) -> str:
    """Сообщение для портфеля с активами"""
    message = f"📊 **Портфель {username}**\n\n"

    # Добавляем информацию об активах
    for asset in assets_info:
        message += f"{asset.get('emoji', '•')} **{asset.get('name', asset.get('symbol', ''))}**\n"
        message += f"   Количество: `{asset.get('amount_formatted', '0')}`\n"
        message += f"   Цена USD: {asset.get('price_usd_formatted', '❌ недоступна')}\n"
        message += f"   Цена RUB: {asset.get('price_rub_formatted', '❌ недоступна')}\n"
        message += f"   Стоимость USD: {asset.get('value_usd_formatted', '❌ недоступна')}\n"
        message += f"   Стоимость RUB: {asset.get('value_rub_formatted', '❌ недоступна')}\n\n"

    # Добавляем общую стоимость
    message += "-" * 30 + "\n"
    message += f"💰 **Общая стоимость:**\n"
    message += f"• USD: {format_currency(total_value)}\n"

    # Рассчитываем общую стоимость в рублях
    rub_total = currency_service.usd_to_rub(total_value)
    message += f"• RUB: {currency_service.format_rub(rub_total)}\n\n"

    # Добавляем информацию об обновлении
    if last_updated:
        message += f"🔄 Обновлено: {last_updated}\n"

    # Добавляем подсказку для управления
    if assets_count > 0:
        message += f"\n\n💡 Используйте `/remove <символ>` чтобы удалить актив"

    return message


def get_crypto_assets_message(assets: List, prices_info: Dict) -> str:  # Добавлен параметр prices_info
    """Сообщение со списком криптовалют"""
    if not assets:
        return "❌ **Нет доступных криптовалют**\n\nПожалуйста, попробуйте позже."

    message = "🏦 **Доступные криптовалюты:**\n\n"

    # Группируем по популярности
    major_coins = ["btc", "eth", "ton", "usdt", "sol"]
    major_assets = [a for a in assets if a.symbol in major_coins]
    other_assets = [a for a in assets if a.symbol not in major_coins]

    if major_assets:
        message += "**💰 Основные:**\n"
        for asset in major_assets:
            price_info = prices_info.get(asset.symbol, {})
            message += f"{asset.config.emoji} **{asset.config.name}**\n"
            message += f"   Символ: `{asset.symbol.upper()}`\n"

            # Показываем цены в USD и RUB
            if price_info.get("price_usd"):
                price_usd = price_info["price_usd"]
                price_rub = price_info.get("price_rub", currency_service.usd_to_rub(price_usd))

                message += f"   Цена USD: ${price_usd:,.4f}\n"
                message += f"   Цена RUB: {currency_service.format_rub(price_rub)}\n"

            # Примерное количество
            if asset.symbol == "btc":
                message += "   Пример: `/add btc 0.01`\n"
            elif asset.symbol == "eth":
                message += "   Пример: `/add eth 0.1`\n"
            elif asset.symbol == "ton":
                message += "   Пример: `/add ton 10`\n"
            elif asset.symbol == "usdt":
                message += "   Пример: `/add usdt 100`\n"
            elif asset.symbol == "sol":
                message += "   Пример: `/add sol 1.0`\n"
            else:
                message += "   Пример: `/add {symbol} 1.0`\n".format(symbol=asset.symbol)

            message += "\n"

    if other_assets:
        message += "**🔹 Другие:**\n"
        for asset in other_assets:
            price_info = prices_info.get(asset.symbol, {})
            message += f"{asset.config.emoji} **{asset.config.name}** (`{asset.symbol.upper()}`)"

            if price_info.get("price_usd"):
                price_usd = price_info["price_usd"]
                price_rub = price_info.get("price_rub", currency_service.usd_to_rub(price_usd))
                message += f" — ${price_usd:.4f} | {currency_service.format_rub(price_rub)}"

            message += "\n"
        message += "\n"

    message += "-" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add btc 0.1` — купить 0.1 Bitcoin\n"
    message += "2. `/portfolio` — посмотреть портфель\n"
    message += "3. `/prices` — текущие цены\n"
    message += "4. `/remove btc` — продать весь Bitcoin\n\n"
    message += "💡 **Совет:** Начните с Bitcoin (BTC) или Ethereum (ETH)"

    return message


def get_fiat_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком фиатных валют"""
    if not assets:
        return "❌ **Нет доступных фиатных валют**\n\nПожалуйста, попробуйте позже."

    message = "💵 **Доступные фиатные валюты:**\n\n"

    for asset in assets:
        price_info = prices_info.get(asset.symbol, {})
        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Символ: `{asset.symbol.upper()}`\n"

        if price_info.get("price"):
            price = price_info["price"]
            if asset.symbol == "usd":
                message += "   Курс: 1 USD = 1.0000 USD\n"
            else:
                message += f"   Курс: 1 USD = {1 / price:.4f} {asset.symbol.upper()}\n"
                message += f"   (1 {asset.symbol.upper()} = ${price:.4f})\n"
        else:
            message += "   Курс: ❌ временно недоступен\n"

        # Пример добавления
        if asset.symbol == "rub":
            message += "   Пример: `/add rub 1000`\n\n"
        elif asset.symbol == "eur":
            message += "   Пример: `/add eur 100`\n\n"
        elif asset.symbol == "usd":
            message += "   Пример: `/add usd 100`\n\n"
        else:
            message += f"   Пример: `/add {asset.symbol} 100`\n\n"

    message += "-" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add rub 10000` — добавить 10,000 рублей\n"
    message += "2. `/add eur 500` — добавить 500 евро\n"
    message += "3. `/portfolio` — посмотреть общую стоимость в USD\n\n"

    message += "💡 **Примечание:**\n"
    message += "• Все валюты конвертируются в USD по текущему курсу\n"
    message += "• Цены обновляются каждую минуту\n"
    message += "• Источник: CoinGecko API"

    return message


def get_metals_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком драгоценных металлов"""
    message = "🥇 **Драгоценные металлы:**\n\n"

    # Золотые монеты
    gold_assets = [a for a in assets if "gold" in a.symbol]
    if gold_assets:
        message += "**💰 Золотые монеты:**\n"
        for asset in gold_assets:
            price_info = prices_info.get(asset.symbol, {})
            message += f"{asset.config.emoji} **{asset.config.name}**\n"

            if hasattr(asset, 'get_metal_info'):
                info = asset.get_metal_info()
                message += f"   Вес: {info['weight_g']}g ({info['weight_oz']:.2f} oz)\n"
                message += f"   Чистота: {info['purity'] * 100:.2f}%\n"

            if price_info.get("price"):
                message += f"   Цена: ${price_info['price']:.2f}\n"

            message += f"   Пример: `/add {asset.symbol} 1`\n\n"

    # Серебряные монеты
    silver_assets = [a for a in assets if "silver" in a.symbol]
    if silver_assets:
        message += "**🥈 Серебряные монеты:**\n"
        for asset in silver_assets:
            price_info = prices_info.get(asset.symbol, {})
            message += f"{asset.config.emoji} **{asset.config.name}**\n"

            if hasattr(asset, 'get_metal_info'):
                info = asset.get_metal_info()
                message += f"   Вес: {info['weight_g']}g ({info['weight_oz']:.2f} oz)\n"
                message += f"   Чистота: {info['purity'] * 100:.2f}%\n"

            if price_info.get("price"):
                message += f"   Цена: ${price_info['price']:.2f}\n"

            message += f"   Пример: `/add {asset.symbol} 1`\n\n"

    message += "-" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add gold_coin_7_78 2` — добавить 2 золотые монеты\n"
    message += "2. `/add silver_coin_31_1 5` — добавить 5 серебряных монет\n"
    message += "3. `/portfolio` — посмотреть общую стоимость\n\n"

    message += "💡 **Примечание:** Цены на основе биржевых котировок с учетом премии за чеканку."

    return message


def get_products_assets_message(assets: List) -> str:
    """Сообщение со списком товаров"""
    if not assets:
        return "❌ **Нет доступных товаров**\n\nТовары еще не добавлены."

    message = "📦 **Доступные товары:**\n\n"

    for asset in assets:
        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Код: `{asset.symbol}`\n"
        message += f"   Пример: `/add {asset.symbol} 10`\n\n"

    message += "-" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add product_1 5` — добавить 5 единиц Товара 1\n"
    message += "2. `/portfolio` — посмотреть общую стоимость\n"
    message += "3. `/remove product_1 2` — удалить 2 единицы\n\n"

    message += "💡 **Примечание:** Цены товаров статические."

    return message


def get_receivables_assets_message(assets: List) -> str:
    """Сообщение со списком дебиторской задолженности"""
    if not assets:
        return "❌ **Нет доступной дебиторской задолженности**"

    message = "🧾 **Дебиторская задолженность:**\n\n"

    for asset in assets:
        discount = getattr(asset, 'discount_factor', {}).get(asset.symbol, 1.0)
        discount_percent = (1 - discount) * 100

        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Код: `{asset.symbol}`\n"
        message += f"   Дисконт: {discount_percent:.1f}%\n"
        message += f"   Пример: `/add {asset.symbol} 50000` — добавить задолженность $50,000\n\n"

    message += "-" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add receivable_ecm 100000` — добавить дебиторку $100,000\n"
    message += "2. `/portfolio` — посмотреть в портфеле\n"
    message += "3. `/remove receivable_ecm 50000` — списать $50,000\n\n"

    message += "💡 **Примечание:** Стоимость учитывает дисконт (риск непогашения)."

    return message


def get_etf_assets_message(assets: List, prices_info: Dict) -> str:
    """Сообщение со списком ETF"""
    if not assets:
        return "❌ **Нет доступных ETF**\n\nETF еще не добавлены."

    message = "📊 **Доступные ETF:**\n\n"

    for asset in assets:
        price_info = prices_info.get(asset.symbol, {})

        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Символ: `{asset.symbol.upper()}`\n"

        if price_info.get("price"):
            price = price_info["price"]
            # Определяем валюту по тикеру
            if asset.symbol == "fxgd":
                message += f"   Цена: {price:,.2f} ₽\n"
            else:
                message += f"   Цена: ${price:.2f}\n"

        # Информация о комиссии для FXGD
        if asset.symbol == "fxgd":
            message += f"   Комиссия: 0.45%\n"
            message += f"   1 акция ≈ 0.1g золота\n"

        message += f"   Пример: `/add {asset.symbol} 10`\n\n"

    message += "─" * 30 + "\n"
    message += "💡 **ETF (Exchange Traded Fund)** — биржевой инвестиционный фонд,\n"
    message += "акции которого торгуются на бирже как обычные акции.\n\n"

    message += "📈 **Преимущества FXGD:**\n"
    message += "• Ликвидность (торгуется на MOEX)\n"
    message += "• Низкий порог входа\n"
    message += "• Прозрачная структура\n"
    message += "• Физическое обеспечение золотом\n"

    return message