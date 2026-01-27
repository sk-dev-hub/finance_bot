"""
Обработчики команд для Telegram бота.
Все команды используют новую модульную архитектуру.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.assets.registry import asset_registry
from src.services.price import price_service
#from src.database.repositories import portfolio_repo, user_repo
from src.database.simple_user_repo import user_repo
from src.database.simple_repo import portfolio_repo

from src.database.models import UserPortfolio


logger = logging.getLogger(__name__)


# ============================================================================
# Вспомогательные функции
# ============================================================================

def get_supported_assets_text() -> str:
    """Возвращает текст со списком поддерживаемых активов"""
    assets = asset_registry.get_all_assets()

    if not assets:
        return "На данный момент нет доступных активов."

    text = ""
    for asset in assets:
        text += f"{asset.display_name}\n"

    return text


def get_precious_metals_text() -> str:
    """Возвращает текст со списком драгоценных металлов"""
    precious_metals = asset_registry.get_precious_metal_assets()

    if not precious_metals:
        return "Драгоценные металлы не поддерживаются."

    text = ""
    for asset in precious_metals:
        text += f"{asset.display_name}\n"

    return text


def get_all_supported_assets_with_details() -> str:
    """Возвращает детальный текст со всеми активами"""
    crypto_assets = asset_registry.get_crypto_assets()
    fiat_assets = asset_registry.get_fiat_assets()
    precious_metals = asset_registry.get_precious_metal_assets()
    commodities = asset_registry.get_commodity_assets()
    receivables = asset_registry.get_receivable_assets()

    text = "💎 **Криптовалюты:**\n"
    for asset in crypto_assets:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol.upper()}`)\n"

    text += "\n💵 **Фиатные валюты:**\n"
    for asset in fiat_assets:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol.upper()}`)\n"

    text += "\n🥇 **Драгоценные металлы:**\n"
    for asset in precious_metals:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol}`)\n"

    text += "\n📦 **Товары:**\n"
    for asset in commodities:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol}`)\n"

    text += "\n🧾 **Дебиторская задолженность:**\n"
    for asset in receivables:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol}`)\n"

    return text


def get_supported_assets_detailed() -> str:
    """Возвращает детальный список активов с примерами"""
    assets = asset_registry.get_all_assets()

    if not assets:
        return "На данный момент нет доступных активов."

    text = ""
    for asset in assets:
        text += f"{asset.display_name}\n"

        # Пример количества в зависимости от типа актива
        if asset.asset_type.value == "crypto":
            if asset.symbol == "btc":
                example = "0.01"
            elif asset.symbol == "eth":
                example = "0.1"
            elif asset.symbol == "ton":
                example = "10"
            elif asset.symbol == "usdt":
                example = "100"
            elif asset.symbol == "sol":
                example = "1.0"
            else:
                example = "1.0"
        else:
            example = "1.0"

        text += f"   Пример: `/add {asset.symbol} {example}`\n\n"

    return text


def get_supported_fiat_text() -> str:
    """Возвращает текст со списком поддерживаемых фиатных валют"""
    fiat_assets = asset_registry.get_fiat_assets()

    if not fiat_assets:
        return "Фиатные валюты не поддерживаются."

    text = ""
    for asset in fiat_assets:
        text += f"{asset.display_name}\n"

    return text


def get_all_supported_assets_text() -> str:
    """Возвращает текст со всеми поддерживаемыми активами"""
    crypto_assets = asset_registry.get_crypto_assets()
    fiat_assets = asset_registry.get_fiat_assets()

    text = "💎 **Криптовалюты:**\n"
    for asset in crypto_assets:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol.upper()}`)\n"

    text += "\n💵 **Фиатные валюты:**\n"
    for asset in fiat_assets:
        text += f"{asset.config.emoji} {asset.config.name} (`{asset.symbol.upper()}`)\n"

    return text


def get_commodities_text() -> str:
    """Возвращает текст со списком товаров"""
    commodities = asset_registry.get_commodity_assets()

    if not commodities:
        return "Товары не поддерживаются."

    text = ""
    for asset in commodities:
        text += f"{asset.display_name}\n"

    return text


def get_receivables_text() -> str:
    """Возвращает текст со списком дебиторской задолженности"""
    receivables = asset_registry.get_receivable_assets()

    if not receivables:
        return "Дебиторская задолженность не поддерживается."

    text = ""
    for asset in receivables:
        text += f"{asset.display_name}\n"

    return text

def format_currency(value: float) -> str:
    """Форматирует денежное значение"""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Форматирует процентное значение"""
    return f"{value:.1f}%"


def get_user_display_name(update: Update) -> str:
    """Получает отображаемое имя пользователя"""
    user = update.effective_user
    if user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    else:
        return "инвестор"


# ============================================================================
# Обработчики команд
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(f"User {user.id} ({user.username}) started the bot")

    # Создаем/получаем пользователя
    user_repo.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_premium=getattr(user, 'is_premium', False)
    )

    # Записываем активность
    user_repo.record_user_activity(user.id, "start")

    # Создаем/получаем портфель
    portfolio = portfolio_repo.get_or_create_user(user.id, user.username)

    # Получаем список активов
    supported_assets = get_supported_assets_text()
    all_assets = get_all_supported_assets_with_details()

    welcome_text = f"""
    👋 Привет, {get_user_display_name(update)}!

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
    /settings — Настройки
    /help — Помощь и инструкции

    🏦 **Поддерживаемые активы:**
    {all_assets}
    **Примеры использования:**
    Криптовалюты:
    `/add btc 0.5` — добавить 0.5 Bitcoin

    Валюты:
    `/add rub 10000` — добавить 10,000 рублей

    Драгоценные металлы:
    `/add gold_coin_7_78 2` — добавить 2 золотые монеты по 7.78г
    `/add silver_coin_31_1 5` — добавить 5 серебряных монет по 31.1г

    Товары:
    `/add product_1 10` — добавить 10 единиц Товара 
    
    Дебиторская задолженность:
    `/add receivable_ecm 100000` — добавить дебиторку ЕЦМ $100,000

    💰 **Бот автоматически:**
    • Отслеживает текущие цены
    • Конвертирует все активы в USD
    • Сохраняет ваш портфель
    • Показывает общую стоимость

    _Начните с добавления первого актива!_
    """

    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_text,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user = update.effective_user
    user_repo.record_user_activity(user.id, "help")

    supported_assets = get_supported_assets_detailed()

    help_text = f"""
📚 **Помощь по использованию бота**

**Основные команды:**
/start — Начать работу
/portfolio — Показать текущий портфель
/add — Добавить актив в портфель
/remove — Удалить актив из портфеля
/prices — Текущие цены криптовалют
/coins — Список всех криптовалют
/currencies — Список валют
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

**Как посмотреть портфель:**
Просто отправьте `/portfolio` чтобы увидеть текущую стоимость всех активов

**Поддерживаемые активы:**
{supported_assets}
**Источник цен:**
Используется CoinGecko API
Цены обновляются каждую минуту

**Частые вопросы:**
• Данные сохраняются локально
• Поддерживается только USD
• Максимальная точность: 8 знаков после запятой
• Минимальная сумма: зависит от актива

🔄 **Нужна помощь?** Просто напишите /start чтобы начать заново.
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /portfolio"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(f"User {user.id} requested portfolio")

    # Получаем портфель пользователя (словарь)
    portfolio = portfolio_repo.get_or_create_user(user.id, user.username)

    # Проверяем наличие активов
    assets = portfolio.get("assets", {})

    if not assets:
        supported_assets = get_supported_assets_text()

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📭 **Ваш портфель пуст**\n\n"
                 f"Используйте команду `/add` чтобы добавить активы.\n\n"
                 f"**Поддерживаемые активы:**\n"
                 f"{supported_assets}\n"
                 f"_Пример: `/add btc 0.1` чтобы добавить 0.1 Bitcoin_",
            parse_mode="Markdown"
        )
        return

    # Получаем текущие цены для активов пользователя
    symbols = list(assets.keys())
    prices_result = await price_service.get_prices(symbols)

    # Формируем сообщение
    message = f"📊 **Портфель {get_user_display_name(update)}**\n\n"
    total_value = 0
    asset_details = []

    # Сортируем активы
    preferred_order = ["btc", "eth", "ton", "usdt", "sol"]
    sorted_assets = sorted(
        assets.items(),
        key=lambda x: (preferred_order.index(x[0]) if x[0] in preferred_order else 999, x[0])
    )

    for symbol, asset_data in sorted_assets:
        price_data = prices_result.get(symbol)

        if price_data and price_data.price:
            price = price_data.price
            amount = asset_data.get("amount", 0)
            value = amount * price
            total_value += value

            # Получаем информацию об активе
            asset_obj = asset_registry.get_asset(symbol)
            if asset_obj:
                emoji = asset_obj.config.emoji
                display_name = asset_obj.config.name
                amount_formatted = asset_obj.format_amount(amount)
            else:
                emoji = "•"
                display_name = symbol.upper()
                amount_formatted = f"{amount:.6f}"

            asset_details.append({
                "emoji": emoji,
                "name": display_name,
                "amount": amount_formatted,
                "price": format_currency(price),
                "value": format_currency(value)
            })
        else:
            # Если не удалось получить цену
            amount = asset_data.get("amount", 0)
            asset_obj = asset_registry.get_asset(symbol)
            if asset_obj:
                emoji = asset_obj.config.emoji
                display_name = asset_obj.config.name
                amount_formatted = asset_obj.format_amount(amount)
            else:
                emoji = "⚠️"
                display_name = symbol.upper()
                amount_formatted = f"{amount:.6f}"

            asset_details.append({
                "emoji": emoji,
                "name": display_name,
                "amount": amount_formatted,
                "price": "❌ недоступна",
                "value": "❌ недоступна"
            })

    # Добавляем информацию об активах
    for asset in asset_details:
        message += f"{asset['emoji']} **{asset['name']}**\n"
        message += f"   Количество: `{asset['amount']}`\n"
        message += f"   Цена: {asset['price']}\n"
        message += f"   Стоимость: {asset['value']}\n\n"

    # Добавляем общую стоимость
    message += "─" * 30 + "\n"
    message += f"💰 **Общая стоимость:** {format_currency(total_value)}\n\n"

    # Добавляем информацию об обновлении
    try:
        last_updated = portfolio.get("updated_at", "")
        if last_updated:
            from datetime import datetime
            dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            last_updated_str = dt.strftime("%H:%M:%S")
            message += f"🔄 Обновлено: {last_updated_str}\n"
    except:
        message += f"🔄 Обновлено: недавно\n"

    message += "_Цены обновляются каждую минуту_\n"
    message += "_Источник: CoinGecko API_"

    # Добавляем подсказку для управления
    if len(assets) > 0:
        message += f"\n\n💡 Используйте `/remove <символ>` чтобы удалить актив"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add"""
    user = update.effective_user
    chat_id = update.effective_chat.id



    # Проверяем аргументы
    if len(context.args) != 2:
        supported_assets = get_supported_assets_detailed()

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ **Неправильный формат команды**\n\n"
                 f"**Используйте:** `/add <символ> <количество>`\n\n"
                 f"**Примеры:**\n"
                 f"`/add btc 0.5` — добавить 0.5 BTC\n"
                 f"`/add eth 2.0` — добавить 2 ETH\n"
                 f"`/add ton 100` — добавить 100 TON\n\n"
                 f"**Поддерживаемые активы:**\n"
                 f"{supported_assets}",
            parse_mode="Markdown"
        )
        return

    symbol = context.args[0].lower()

    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError("Количество должно быть больше 0")
    except ValueError as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ **Некорректное количество**\n\n"
                 f"Количество должно быть положительным числом.\n"
                 f"**Пример:** `0.5`, `2.0`, `100`, `0.01`\n\n"
                 f"Ошибка: {str(e)}",
            parse_mode="Markdown"
        )
        return

    # Добавляем актив через репозиторий
    success, message = portfolio_repo.add_asset(user.id, symbol, amount)

    if success:
        # Получаем текущую цену для отображения
        price_data = await price_service.get_price(symbol)

        # Получаем информацию об активе
        asset = asset_registry.get_asset(symbol)
        if asset:
            emoji = asset.config.emoji
            display_name = asset.config.name
            amount_formatted = asset.format_amount(amount)
        else:
            emoji = "✅"
            display_name = symbol.upper()
            amount_formatted = f"{amount:.6f}"

        response = f"{emoji} **Актив добавлен!**\n\n"
        response += f"**{display_name}**\n"
        response += f"Количество: `{amount_formatted}`\n"

        if price_data and price_data.price:
            price = price_data.price
            value = amount * price
            response += f"Текущая цена: {format_currency(price)}\n"
            response += f"Стоимость: {format_currency(value)}\n"
        else:
            response += f"Цена: ❌ временно недоступна\n"

        # Получаем обновленный портфель для отображения статистики
        portfolio = portfolio_repo.get_user_assets(user.id)
        total_assets = len(portfolio)

        response += f"\n📊 **В вашем портфеле:** {total_assets} актив(ов)\n"
        response += f"💡 Используйте `/portfolio` чтобы увидеть весь портфель"

    else:
        supported_assets = get_supported_assets_text()
        response = f"❌ **Ошибка при добавлении актива**\n\n"
        response += f"{message}\n\n"
        response += f"**Поддерживаемые активы:**\n"
        response += f"{supported_assets}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=response,
        parse_mode="Markdown"
    )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /remove"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "remove")

    # Проверяем аргументы
    if len(context.args) < 1 or len(context.args) > 2:
        supported_assets = get_supported_assets_detailed()

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ **Неправильный формат команды**\n\n"
                 f"**Используйте:** `/remove <символ> [количество]`\n\n"
                 f"**Примеры:**\n"
                 f"`/remove btc` — удалить весь BTC\n"
                 f"`/remove eth 1.0` — удалить 1 ETH\n"
                 f"`/remove ton 50` — удалить 50 TON\n\n"
                 f"**Поддерживаемые активы:**\n"
                 f"{supported_assets}",
            parse_mode="Markdown"
        )
        return

    symbol = context.args[0].lower()

    # Проверяем количество, если указано
    amount = None
    if len(context.args) == 2:
        try:
            amount = float(context.args[1])
            if amount <= 0:
                raise ValueError("Количество должно быть больше 0")
        except ValueError as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ **Некорректное количество**\n\n"
                     f"Количество должно быть положительным числом.\n"
                     f"**Пример:** `0.5`, `2.0`, `100`, `0.01`\n\n"
                     f"Ошибка: {str(e)}",
                parse_mode="Markdown"
            )
            return

    # Удаляем актив через репозиторий
    success, message = portfolio_repo.remove_asset(user.id, symbol, amount)

    if success:
        # Получаем информацию об активе
        asset = asset_registry.get_asset(symbol)
        if asset:
            emoji = asset.config.emoji
            display_name = asset.config.name
        else:
            emoji = "✅"
            display_name = symbol.upper()

        response = f"{emoji} **{message}**\n\n"

        # Проверяем, остались ли еще активы в портфеле
        portfolio = portfolio_repo.get_user_assets(user.id)
        if portfolio:
            remaining_assets = len(portfolio)
            response += f"📊 **Осталось активов:** {remaining_assets}\n"
            response += f"💡 Используйте `/portfolio` чтобы увидеть обновленный портфель"
        else:
            response += f"📭 **Ваш портфель теперь пуст**\n"
            response += f"💡 Используйте `/add` чтобы добавить новые активы"

    else:
        supported_assets = get_supported_assets_text()
        response = f"❌ **Ошибка при удалении актива**\n\n"
        response += f"{message}\n\n"
        response += f"**Поддерживаемые активы:**\n"
        response += f"{supported_assets}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=response,
        parse_mode="Markdown"
    )


async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /prices"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(f"User {user.id} requested prices")
    user_repo.record_user_activity(user.id, "prices")

    # Получаем цены для всех поддерживаемых активов
    crypto_assets = asset_registry.get_crypto_assets()
    symbols = [asset.symbol for asset in crypto_assets]

    # Получаем цены
    prices_result = await price_service.get_prices(symbols)

    # Формируем сообщение
    message = "📈 **Текущие цены криптовалют**\n\n"

    # Сортируем активы по популярности
    sorted_assets = sorted(
        crypto_assets,
        key=lambda x: (["btc", "eth", "ton", "usdt", "sol"].index(x.symbol)
                       if x.symbol in ["btc", "eth", "ton", "usdt", "sol"] else 999)
    )

    for asset in sorted_assets:
        price_data = prices_result.get(asset.symbol)

        message += f"{asset.config.emoji} **{asset.config.name} ({asset.symbol.upper()})**\n"

        if price_data and price_data.price:
            price = price_data.price

            # Форматируем цену в зависимости от стоимости
            if asset.symbol == "btc" or asset.symbol == "eth":
                price_formatted = format_currency(price)
            elif asset.symbol == "ton" or asset.symbol == "sol":
                price_formatted = f"${price:,.4f}"
            elif asset.symbol == "usdt":
                price_formatted = f"${price:,.2f}"
            else:
                price_formatted = f"${price:,.4f}"

            message += f"   Цена: {price_formatted}\n"

            # Добавляем изменение за 24ч (если есть в данных)
            if hasattr(price_data, 'change_24h'):
                change = price_data.change_24h
                if change is not None:
                    change_emoji = "📈" if change >= 0 else "📉"
                    change_formatted = f"{change:+.2f}%"
                    message += f"   24ч: {change_emoji} {change_formatted}\n"
        else:
            message += f"   Цена: ❌ временно недоступна\n"

        message += "\n"

    message += "─" * 30 + "\n"
    message += "💡 **Подсказки:**\n"
    message += "• Используйте `/add <символ> <количество>` чтобы купить\n"
    message += "• Используйте `/portfolio` чтобы увидеть свой портфель\n\n"
    message += "_Цены обновляются каждую минуту_\n"
    message += "_Источник: CoinGecko API_"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /coins - показывает список криптовалют"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "coins")

    # Получаем все крипто активы
    crypto_assets = asset_registry.get_crypto_assets()

    if not crypto_assets:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Нет доступных криптовалют**\n\n"
                 "Пожалуйста, попробуйте позже.",
            parse_mode="Markdown"
        )
        return

    message = "🏦 **Доступные криптовалюты:**\n\n"

    # Группируем по типам или популярности
    major_coins = ["btc", "eth", "ton", "usdt", "sol"]
    other_coins = [asset for asset in crypto_assets if asset.symbol not in major_coins]

    # Основные криптовалюты
    message += "**💰 Основные:**\n"
    for asset in crypto_assets:
        if asset.symbol in major_coins:
            message += f"{asset.config.emoji} **{asset.config.name}**\n"
            message += f"   Символ: `{asset.symbol.upper()}`\n"
            message += f"   Пример: `/add {asset.symbol} "

            # Примерное количество в зависимости от цены
            if asset.symbol == "btc":
                message += "0.01`\n"
            elif asset.symbol == "eth":
                message += "0.1`\n"
            elif asset.symbol == "ton":
                message += "10`\n"
            elif asset.symbol == "usdt":
                message += "100`\n"
            elif asset.symbol == "sol":
                message += "1.0`\n"
            else:
                message += "1.0`\n"

            message += "\n"

    # Другие криптовалюты
    if other_coins:
        message += "**🔹 Другие:**\n"
        for asset in other_coins:
            message += f"{asset.config.emoji} **{asset.config.name}** (`{asset.symbol.upper()}`)\n"

    message += "\n" + "─" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add btc 0.1` — купить 0.1 Bitcoin\n"
    message += "2. `/portfolio` — посмотреть портфель\n"
    message += "3. `/prices` — текущие цены\n"
    message += "4. `/remove btc` — продать весь Bitcoin\n\n"
    message += "💡 **Совет:** Начните с Bitcoin (BTC) или Ethereum (ETH)"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def currencies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /currencies - показывает список фиатных валют"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(f"User {user.id} requested currencies")
    user_repo.record_user_activity(user.id, "currencies")

    # Получаем все фиатные активы
    fiat_assets = asset_registry.get_fiat_assets()

    if not fiat_assets:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Нет доступных фиатных валют**\n\n"
                 "Пожалуйста, попробуйте позже.",
            parse_mode="Markdown"
        )
        return

    message = "💵 **Доступные фиатные валюты:**\n\n"

    # Получаем текущие цены (курсы валют к USD)
    symbols = [asset.symbol for asset in fiat_assets]
    prices_result = await price_service.get_prices(symbols)

    for asset in fiat_assets:
        price_data = prices_result.get(asset.symbol)

        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Символ: `{asset.symbol.upper()}`\n"

        if price_data and price_data.price:
            price = price_data.price
            # Для валют показываем курс к USD (1 USD = X валюта)
            if asset.symbol == "usd":
                message += f"   Курс: 1 USD = 1.0000 {asset.symbol.upper()}\n"
            else:
                message += f"   Курс: 1 USD = {1 / price:.4f} {asset.symbol.upper()}\n"
                message += f"   (1 {asset.symbol.upper()} = ${price:.4f})\n"
        else:
            message += f"   Курс: ❌ временно недоступен\n"

        # Пример добавления
        if asset.symbol == "rub":
            message += f"   Пример: `/add rub 1000`\n\n"
        elif asset.symbol == "eur":
            message += f"   Пример: `/add eur 100`\n\n"
        elif asset.symbol == "usd":
            message += f"   Пример: `/add usd 100`\n\n"
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

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /products - показывает товары"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "products")

    # Получаем товары
    commodities = asset_registry.get_commodity_assets()

    if not commodities:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Нет доступных товаров**\n\n"
                 "Товары еще не добавлены.",
            parse_mode="Markdown"
        )
        return

    # Получаем цены
    symbols = [asset.symbol for asset in commodities]
    prices = await price_service.get_prices(symbols)

    message = "📦 **Доступные товары:**\n\n"

    for asset in commodities:
        price_data = prices.get(asset.symbol)

        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Код: `{asset.symbol}`\n"

        if price_data and price_data.price:
            message += f"   Цена: ${price_data.price:.2f}\n"
        else:
            message += f"   Цена: не установлена\n"

        message += f"   Пример: `/add {asset.symbol} 10`\n\n"

    message += "─" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add product_1 5` — добавить 5 единиц Товара 1\n"
    message += "2. `/portfolio` — посмотреть общую стоимость\n"
    message += "3. `/remove product_1 2` — удалить 2 единицы\n\n"

    message += "💡 **Примечание:** Цены товаров статические, можно обновить через администратора."

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def receivables_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /receivables - показывает дебиторскую задолженность"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "receivables")

    # Получаем дебиторскую задолженность
    receivables = asset_registry.get_receivable_assets()

    if not receivables:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Нет доступной дебиторской задолженности**",
            parse_mode="Markdown"
        )
        return

    message = "🧾 **Дебиторская задолженность:**\n\n"

    for asset in receivables:
        # Для задолженности получаем информацию о дисконте
        discount = getattr(asset, 'discount_factor', {}).get(asset.symbol, 1.0)
        discount_percent = (1 - discount) * 100

        message += f"{asset.config.emoji} **{asset.config.name}**\n"
        message += f"   Код: `{asset.symbol}`\n"
        message += f"   Дисконт: {discount_percent:.1f}%\n"
        message += f"   Пример: `/add {asset.symbol} 50000` — добавить задолженность $50,000\n\n"

    message += "─" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add receivable_ecm 100000` — добавить дебиторку ЕЦМ $100,000\n"
    message += "2. `/portfolio` — посмотреть в портфеле\n"
    message += "3. `/remove receivable_ecm 50000` — списать $50,000\n\n"

    message += "💡 **Примечание:** Стоимость может учитывать дисконт (риск непогашения)."

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )

async def assets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /assets - альтернативное название для /coins"""
    await coins_command(update, context)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "settings")

    # Получаем настройки пользователя
    settings = user_repo.get_user_settings(user.id)

    # Получаем статистику пользователя
    portfolio = portfolio_repo.get_user_assets(user.id)
    total_assets = len(portfolio)

    # Формируем сообщение
    message = f"⚙️ **Настройки {get_user_display_name(update)}**\n\n"

    message += "**📊 Ваша статистика:**\n"
    message += f"• Активов в портфеле: {total_assets}\n"
    message += f"• Валюта: {settings.get('currency', 'USD')}\n"
    message += f"• Уведомления: {'Включены' if settings.get('notifications', True) else 'Выключены'}\n\n"

    message += "**🔧 Доступные настройки:**\n"
    message += "• `/settings currency USD` — изменить валюту\n"
    message += "• `/settings notifications on` — включить уведомления\n"
    message += "• `/settings notifications off` — выключить уведомления\n\n"

    message += "**📈 Информация о боте:**\n"
    message += f"• Поддерживаемых активов: {len(asset_registry.get_all_assets())}\n"
    message += f"• Обновление цен: каждую минуту\n"
    message += f"• Источник данных: CoinGecko API\n\n"

    message += "💡 _Больше настроек скоро будут доступны!_"

    # Обработка аргументов для изменения настроек
    if len(context.args) >= 2:
        setting_key = context.args[0].lower()
        setting_value = context.args[1].lower()

        if setting_key == "currency":
            if setting_value.upper() in ["USD", "EUR", "RUB"]:
                success = user_repo.update_user_settings(user.id, {"currency": setting_value.upper()})
                if success:
                    message += f"\n\n✅ Валюта изменена на {setting_value.upper()}"
                else:
                    message += f"\n\n❌ Не удалось изменить валюту"
            else:
                message += f"\n\n❌ Поддерживаются: USD, EUR, RUB"

        elif setting_key == "notifications":
            if setting_value in ["on", "yes", "true", "1"]:
                success = user_repo.update_user_settings(user.id, {"notifications": True})
                if success:
                    message += f"\n\n✅ Уведомления включены"
                else:
                    message += f"\n\n❌ Не удалось включить уведомления"
            elif setting_value in ["off", "no", "false", "0"]:
                success = user_repo.update_user_settings(user.id, {"notifications": False})
                if success:
                    message += f"\n\n✅ Уведомления выключены"
                else:
                    message += f"\n\n❌ Не удалось выключить уведомления"
            else:
                message += f"\n\n❌ Используйте: on/off"

        else:
            message += f"\n\n❌ Неизвестная настройка: {setting_key}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def update_product_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /update_product_price - обновляет цену товара"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Простая проверка (можно улучшить)
    if user.id != 123456789:  # Замените на ваш ID
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Доступ запрещен**\n\n"
                 "Эта команда только для администраторов.",
            parse_mode="Markdown"
        )
        return

    # Проверяем аргументы
    if len(context.args) != 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Неправильный формат**\n\n"
                 "Используйте: `/update_product_price <код_товара> <цена>`\n"
                 "Примеры:\n"
                 "`/update_product_price product_1 120.5`\n"
                 "`/update_product_price product_2 300`",
            parse_mode="Markdown"
        )
        return

    product_code = context.args[0].lower()
    try:
        new_price = float(context.args[1])
        if new_price <= 0:
            raise ValueError
    except ValueError:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Некорректная цена**\n\n"
                 "Цена должна быть положительным числом.",
            parse_mode="Markdown"
        )
        return

    # Обновляем цену
    asset = asset_registry.get_asset(product_code)
    if not asset or not hasattr(asset, 'update_price'):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ **Товар не найден**\n\n"
                 f"Товар с кодом `{product_code}` не существует.",
            parse_mode="Markdown"
        )
        return

    # Обновляем цену
    asset.update_price(new_price)

    # Очищаем кэш цен
    price_service.clear_cache()

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ **Цена обновлена**\n\n"
             f"Товар: {asset.config.name}\n"
             f"Новая цена: ${new_price:.2f}\n\n"
             f"💡 Используйте `/products` чтобы увидеть изменения.",
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats - статистика бота"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "stats")

    # Получаем статистику
    user_stats = user_repo.get_user_statistics()
    portfolio_stats = portfolio_repo.health_check()

    # Формируем сообщение
    message = "📊 **Статистика бота**\n\n"

    message += "**👥 Пользователи:**\n"
    message += f"• Всего пользователей: {user_stats.get('total_users', 0)}\n"
    message += f"• Активных (30 дней): {user_stats.get('active_users', 0)}\n"
    message += f"• Premium: {user_stats.get('premium_users', 0)}\n\n"

    message += "📈 **Портфели:**\n"
    message += f"• Всего активов: {portfolio_stats.get('total_assets', 0)}\n"
    message += f"• Уникальных символов: {portfolio_stats.get('asset_count', 0)}\n\n"

    message += "💎 **Активы:**\n"
    message += f"• Поддерживается: {len(asset_registry.get_all_assets())} криптовалют\n"

    # Показываем самые популярные активы
    popular_assets = ["BTC", "ETH", "TON", "USDT", "SOL"]
    message += f"• Основные: {', '.join(popular_assets)}\n\n"

    message += "🔄 **Система:**\n"
    message += f"• Версия базы данных: {portfolio_stats.get('version', '1.0')}\n"
    message += f"• Размер данных: {portfolio_stats.get('file_size', 0) // 1024} KB\n"
    message += f"• Статус: {portfolio_stats.get('status', 'unknown')}\n\n"

    message += "💡 _Статистика обновляется в реальном времени_"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear - очистить портфель"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "clear")

    # Проверяем подтверждение
    if len(context.args) == 0:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ **Внимание!**\n\n"
                 "Эта команда полностью очистит ваш портфель.\n"
                 "Все активы будут удалены без возможности восстановления.\n\n"
                 "Для подтверждения введите:\n"
                 "`/clear confirm`",
            parse_mode="Markdown"
        )
        return

    if context.args[0].lower() != "confirm":
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Отменено**\n\n"
                 "Для очистки портфеля необходимо подтверждение.\n"
                 "Используйте: `/clear confirm`",
            parse_mode="Markdown"
        )
        return

    # Получаем текущий портфель
    portfolio = portfolio_repo.get_user_assets(user.id)

    if not portfolio:
        await context.bot.send_message(
            chat_id=chat_id,
            text="📭 **Ваш портфель уже пуст**\n\n"
                 "Нечего очищать!",
            parse_mode="Markdown"
        )
        return

    # Удаляем все активы по одному
    cleared_count = 0
    for symbol in list(portfolio.keys()):
        success, _ = portfolio_repo.remove_asset(user.id, symbol, None)
        if success:
            cleared_count += 1

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🧹 **Портфель очищен**\n\n"
             f"Удалено активов: {cleared_count}\n"
             f"Теперь ваш портфель пуст.\n\n"
             f"💡 Используйте `/add` чтобы добавить новые активы.",
        parse_mode="Markdown"
    )


async def metals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /metals - показывает драгоценные металлы"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    user_repo.record_user_activity(user.id, "metals")

    # Получаем драгоценные металлы
    precious_metals = asset_registry.get_precious_metal_assets()

    if not precious_metals:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Нет доступных драгоценных металлов**\n\n"
                 "Пожалуйста, попробуйте позже.",
            parse_mode="Markdown"
        )
        return

    # Получаем текущие цены
    symbols = [asset.symbol for asset in precious_metals]
    prices = await price_service.get_prices(symbols)

    message = "🥇 **Драгоценные металлы:**\n\n"

    # Золотые монеты
    gold_assets = [asset for asset in precious_metals if "gold" in asset.symbol]
    if gold_assets:
        message += "**💰 Золотые монеты:**\n"
        for asset in gold_assets:
            price_data = prices.get(asset.symbol)

            message += f"{asset.config.emoji} **{asset.config.name}**\n"

            if hasattr(asset, 'get_metal_info'):
                info = asset.get_metal_info()
                message += f"   Вес: {info['weight_g']}g ({info['weight_oz']:.2f} oz)\n"
                message += f"   Чистота: {info['purity'] * 100:.2f}%\n"

            if price_data and price_data.price:
                message += f"   Цена: ${price_data.price:.2f}\n"

            message += f"   Пример: `/add {asset.symbol} 1`\n\n"

    # Серебряные монеты
    silver_assets = [asset for asset in precious_metals if "silver" in asset.symbol]
    if silver_assets:
        message += "**🥈 Серебряные монеты:**\n"
        for asset in silver_assets:
            price_data = prices.get(asset.symbol)

            message += f"{asset.config.emoji} **{asset.config.name}**\n"

            if hasattr(asset, 'get_metal_info'):
                info = asset.get_metal_info()
                message += f"   Вес: {info['weight_g']}g ({info['weight_oz']:.2f} oz)\n"
                message += f"   Чистота: {info['purity'] * 100:.2f}%\n"

            if price_data and price_data.price:
                message += f"   Цена: ${price_data.price:.2f}\n"

            message += f"   Пример: `/add {asset.symbol} 1`\n\n"

    message += "─" * 30 + "\n"
    message += "📝 **Как использовать:**\n"
    message += "1. `/add gold_coin_7_78 2` — добавить 2 золотые монеты по 7.78г\n"
    message += "2. `/add silver_coin_31_1 5` — добавить 5 серебряных монет по 31.1г\n"
    message += "3. `/portfolio` — посмотреть общую стоимость в USD\n\n"

    message += "💡 **Примечание:** Цены рассчитываются на основе текущих биржевых котировок золота и серебра с учетом премии за чеканку."

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )

    async def update_metal_prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /update_metal_prices - обновляет цены на металлы"""
        user = update.effective_user
        chat_id = update.effective_chat.id

        # Проверяем права (можно сделать для админов)
        if len(context.args) != 2:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ **Неправильный формат команды**\n\n"
                     "Используйте: `/update_metal_prices <металл> <цена>`\n"
                     "Примеры:\n"
                     "`/update_metal_prices gold 65.5` — установить цену золота $65.5/г\n"
                     "`/update_metal_prices silver 0.88` — установить цену серебра $0.88/г",
                parse_mode="Markdown"
            )
            return

        metal_type = context.args[0].lower()
        try:
            price = float(context.args[1])
            if price <= 0:
                raise ValueError
        except ValueError:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ **Некорректная цена**\n\n"
                     "Цена должна быть положительным числом.",
                parse_mode="Markdown"
            )
            return

        # Обновляем цены у всех активов из драгметаллов
        updated_count = 0
        precious_metals = asset_registry.get_precious_metal_assets()

        for asset in precious_metals:
            if hasattr(asset, 'update_metal_price'):
                # Проверяем тип металла
                if metal_type == "gold" and "gold" in asset.symbol:
                    asset.update_metal_price("gold", price)
                    updated_count += 1
                elif metal_type == "silver" and "silver" in asset.symbol:
                    asset.update_metal_price("silver", price)
                    updated_count += 1

        # Очищаем кэш цен
        price_service.clear_cache()

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ **Цены обновлены**\n\n"
                 f"Установлена цена {metal_type}: ${price:.2f} за грамм\n"
                 f"Обновлено активов: {updated_count}\n\n"
                 f"💡 Используйте `/portfolio` чтобы увидеть новые стоимости.",
            parse_mode="Markdown"
        )


# ============================================================================
# Функция для получения всех обработчиков
# ============================================================================

def get_all_commands() -> Dict[str, callable]:
    """Возвращает словарь всех команд и их обработчиков"""
    return {
        "start": start_command,
        "help": help_command,
        "portfolio": portfolio_command,
        "add": add_command,
        "remove": remove_command,
        "prices": prices_command,
        "coins": coins_command,
        "currencies": currencies_command,
        "metals": metals_command,
        "products": products_command,
        "receivables": receivables_command,
        "assets": assets_command,
        "settings": settings_command,
        "stats": stats_command,
        "clear": clear_command,
    }