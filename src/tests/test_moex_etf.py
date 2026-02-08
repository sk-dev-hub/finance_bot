# src/tests/test_moex_etf.py
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
import aiohttp

from src.assets.moex_etf import MoexETFAsset
from src.config.assets import AssetConfig, AssetType


@pytest.fixture
def fxgd_config():
    """Конфигурация для FXGD ETF"""
    return AssetConfig(
        symbol="fxgd",
        name="FinEx Физическое Золото",
        asset_type=AssetType.ETF,
        emoji="🏅",
        description="ETF на физическое золото",
        price_source="moex",
        source_id="FXGD",
        min_amount=0.01,
        max_amount=1000.0,
        display_precision=2
    )


@pytest.fixture
def moex_etf(fxgd_config):
    """Экземпляр MoexETFAsset"""
    return MoexETFAsset(fxgd_config)


@pytest.fixture
def mock_session():
    """Мок сессии aiohttp"""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.closed = False
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_response():
    """Мок ответа aiohttp"""
    response = AsyncMock(spec=aiohttp.ClientResponse)
    response.status = 200
    response.text = AsyncMock()
    return response


@pytest.mark.asyncio
async def test_get_session_creates_new_session(moex_etf):
    """Тест создания новой сессии"""
    # Убедимся, что сессии нет
    assert moex_etf.session is None

    # Создаем сессию
    session = await moex_etf._get_session()

    # Проверяем, что сессия создана
    assert session is not None
    assert isinstance(session, aiohttp.ClientSession)
    assert moex_etf.session == session


@pytest.mark.asyncio
async def test_get_session_reuses_existing(moex_etf, mock_session):
    """Тест повторного использования существующей сессии"""
    moex_etf.session = mock_session

    session = await moex_etf._get_session()

    assert session == mock_session
    # Не должно быть создано новой сессии
    mock_session.assert_not_called()


@pytest.mark.asyncio
async def test_get_session_recreates_closed(moex_etf, mock_session):
    """Тест пересоздания закрытой сессии"""
    mock_session.closed = True
    moex_etf.session = mock_session

    # Патчим ClientSession, чтобы он вернул новый мок
    with patch('src.assets.moex_etf.aiohttp.ClientSession') as mock_client_session:
        mock_new_session = AsyncMock()
        mock_client_session.return_value = mock_new_session

        session = await moex_etf._get_session()

        assert session == mock_new_session
        mock_client_session.assert_called_once()


@pytest.mark.asyncio
async def test_get_price_moex_iss_success(moex_etf, mock_session, mock_response):
    """Тест успешного получения цены через MOEX ISS API"""
    # Мокаем ответ от MOEX для первого endpoint
    mock_data_first = [
        {},  # metadata
        {
            "securities": {
                "columns": ["SECID", "LAST", "LASTTOPREVPRICE"],
                "data": [["FXGD", 3500.50, 2.5]]
            }
        }
    ]

    mock_response.json = AsyncMock(return_value=mock_data_first)
    mock_session.get.return_value.__aenter__.return_value = mock_response

    # Патчим _get_session
    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        price = await moex_etf._get_price_moex_iss()

        assert price == 3500.50


@pytest.mark.asyncio
async def test_get_price_moex_iss_fallback_to_prevprice(moex_etf, mock_session, mock_response):
    """Тест получения цены через PREVPRICE, когда LAST нет"""
    # Первый endpoint возвращает None для LAST
    mock_data_first = [
        {},
        {
            "securities": {
                "columns": ["SECID", "LAST", "LASTTOPREVPRICE"],
                "data": [["FXGD", None, None]]
            }
        }
    ]

    # Второй endpoint возвращает PREVPRICE
    mock_data_second = [
        {},
        {
            "securities": {
                "columns": ["PREVPRICE"],
                "data": [[3490.00]]
            }
        }
    ]

    # Настраиваем mock чтобы первый вызов вернул первый ответ, второй - второй
    mock_response.json = AsyncMock(side_effect=[mock_data_first, mock_data_second])
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        price = await moex_etf._get_price_moex_iss()

        assert price == 3490.00
        # Проверяем что было 2 вызова
        assert mock_session.get.call_count == 2


@pytest.mark.asyncio
async def test_get_price_moex_iss_no_data(moex_etf, mock_session):
    """Тест, когда оба endpoint возвращают пустые данные"""
    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        # Мокаем ответы без данных
        mock_response1 = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response1.status = 200
        mock_response1.json = AsyncMock(return_value=[{}, {"securities": {"data": []}}])

        mock_response2 = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response2.status = 200
        mock_response2.json = AsyncMock(return_value=[{}, {"securities": {"data": []}}])

        # Настраиваем последовательные вызовы
        mock_session.get.return_value.__aenter__.side_effect = [mock_response1, mock_response2]

        price = await moex_etf._get_price_moex_iss()

        assert price is None


@pytest.mark.asyncio
async def test_get_price_moex_iss_http_error(moex_etf, mock_session):
    """Тест ошибки HTTP при запросе к MOEX"""
    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        mock_session.get.return_value.__aenter__.side_effect = aiohttp.ClientError("Connection error")

        price = await moex_etf._get_price_moex_iss()

        assert price is None


@pytest.mark.asyncio
async def test_get_price_with_cache(moex_etf):
    """Тест получения цены из кэша"""
    from src.assets.base import AssetPrice

    # Создаем мок кэшированной цены
    cached_price = AssetPrice(
        symbol="fxgd",
        price=3500.50,
        source="moex",
        timestamp=datetime.now()
    )

    # Помещаем в кэш
    moex_etf._cache["fxgd"] = cached_price
    moex_etf._cache_time["fxgd"] = datetime.now()

    # Получаем цену
    price = await moex_etf.get_price()

    # Должен вернуться кэшированный результат
    assert price == cached_price


@pytest.mark.asyncio
async def test_get_price_with_expired_cache(moex_etf):
    """Тест, когда кэш устарел"""
    from src.assets.base import AssetPrice

    # Создаем устаревший кэш
    old_price = AssetPrice(
        symbol="fxgd",
        price=3400.00,
        source="moex",
        timestamp=datetime.now() - timedelta(minutes=2)
    )

    moex_etf._cache["fxgd"] = old_price
    moex_etf._cache_time["fxgd"] = datetime.now() - timedelta(minutes=2)

    # Мокаем получение новой цены
    with patch.object(moex_etf, '_get_price_moex_iss', return_value=3500.50):
        price = await moex_etf.get_price()

        # Должна вернуться новая цена
        assert price.price == 3500.50
        assert price.symbol == "fxgd"


@pytest.mark.asyncio
async def test_get_price_success_flow(moex_etf):
    """Тест полного потока успешного получения цены"""
    # Мокаем все методы
    with patch.object(moex_etf, '_get_price_moex_iss', return_value=3500.50):
        price = await moex_etf.get_price()

        assert price is not None
        assert price.price == 3500.50
        assert price.symbol == "fxgd"
        assert price.source == "moex"

        # Проверяем, что цена закэширована
        assert "fxgd" in moex_etf._cache
        assert "fxgd" in moex_etf._cache_time


@pytest.mark.asyncio
async def test_get_price_fallback_flow(moex_etf):
    """Тест потока с резервными методами"""
    # Мокаем все методы, чтобы они возвращали None
    with patch.object(moex_etf, '_get_price_moex_iss', return_value=None):
        with patch.object(moex_etf, '_get_price_investing', return_value=None):
            price = await moex_etf.get_price()

            # Должен вернуться fallback price
            assert price is not None
            assert price.price == 35.0  # Из fallback_prices
            assert price.symbol == "fxgd"


@pytest.mark.asyncio
async def test_get_price_all_methods_failed(moex_etf):
    """Тест, когда все методы получения цены провалились"""
    with patch.object(moex_etf, '_get_price_moex_iss', return_value=None):
        with patch.object(moex_etf, '_get_price_investing', return_value=None):
            with patch.object(moex_etf, '_get_fallback_price', return_value=None):
                price = await moex_etf.get_price()

                assert price is None


@pytest.mark.asyncio
async def test_get_price_exception_handling(moex_etf):
    """Тест обработки исключений"""
    # Исключение при получении цены
    with patch.object(moex_etf, '_get_price_moex_iss', side_effect=Exception("Test error")):
        price = await moex_etf.get_price()

        # Метод должен вернуть None при любой ошибке
        assert price is None


def test_get_fallback_price(moex_etf):
    """Тест получения резервной цены"""
    # Для fxgd
    price = moex_etf._get_fallback_price()
    assert price == 35.0

    # Для другого тикера
    moex_etf.symbol = "tbrd"
    price = moex_etf._get_fallback_price()
    assert price == 1500.0

    # Для неизвестного тикера
    moex_etf.symbol = "unknown"
    price = moex_etf._get_fallback_price()
    assert price is None


def test_validate_amount(moex_etf):
    """Тест валидации количества"""
    # Корректные значения
    assert moex_etf.validate_amount(1.0) is True
    assert moex_etf.validate_amount(0.01) is True  # Минимальное
    assert moex_etf.validate_amount(1000.0) is True  # Максимальное

    # Некорректные значения
    assert moex_etf.validate_amount(0.0) is False  # Меньше минимального
    assert moex_etf.validate_amount(0.005) is False
    assert moex_etf.validate_amount(1000.01) is False  # Больше максимального


def test_get_etf_info(moex_etf):
    """Тест получения информации об ETF"""
    info = moex_etf.get_etf_info()

    assert isinstance(info, dict)
    assert info["name"] == "FinEx Физическое Золото"
    assert info["currency"] == "RUB"
    assert info["exchange"] == "MOEX"
    assert info["ticker"] == "FXGD"
    assert info["expense_ratio"] == 0.45
    assert info["gold_per_share"] == 0.1


def test_get_etf_info_with_price(moex_etf):
    """Тест получения информации об ETF с ценой в кэше"""
    from src.assets.base import AssetPrice

    # Добавляем цену в кэш
    cached_price = AssetPrice(
        symbol="fxgd",
        price=3500.50,
        source="moex",
        timestamp=datetime.now()
    )
    moex_etf._cache["fxgd"] = cached_price

    info = moex_etf.get_etf_info()

    assert "current_price" in info
    assert info["current_price"] == 3500.50


@pytest.mark.asyncio
async def test_close_session(moex_etf, mock_session):
    """Тест закрытия сессии"""
    moex_etf.session = mock_session

    await moex_etf.close()

    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_no_session(moex_etf):
    """Тест закрытия, когда сессии нет"""
    # Не должно быть исключения
    await moex_etf.close()


@pytest.mark.asyncio
async def test_get_price_investing_success(moex_etf, mock_session, mock_response):
    """Тест получения цены через Investing.com"""
    # Мокаем HTML ответ с ценой в одном из форматов
    html_content = '''
    <span data-test="instrument-price-last">3,500.50</span>
    '''
    mock_response.text = AsyncMock(return_value=html_content)
    mock_response.status = 200

    # Мокаем два URL
    mock_session.get.return_value.__aenter__.return_value = mock_response

    # Патчим _get_session
    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        # Пробуем получить цену
        price = await moex_etf._get_price_investing()

        # Цена должна быть найдена
        assert price == 3500.50


@pytest.mark.asyncio
async def test_get_price_investing_no_price_found(moex_etf, mock_session, mock_response):
    """Тест, когда цена не найдена на Investing.com"""
    # HTML без цены
    html_content = '''
    <div class="some-class">Some text</div>
    <span>No price here</span>
    '''
    mock_response.text = AsyncMock(return_value=html_content)
    mock_response.status = 200

    mock_session.get.return_value.__aenter__.return_value = mock_response

    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        price = await moex_etf._get_price_investing()

        # Цена не должна быть найдена
        assert price is None


@pytest.mark.asyncio
async def test_get_price_investing_first_url_fails(moex_etf, mock_session):
    """Тест, когда первый URL падает, но второй работает"""
    # Создаем два разных ответа
    mock_response_fail = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response_fail.status = 404
    mock_response_fail.text = AsyncMock(return_value='Not found')

    mock_response_success = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response_success.status = 200
    # Цена в формате с кавычками
    mock_response_success.text = AsyncMock(return_value='{"last":"3500.50"}')

    # Первый вызов падает, второй успешен
    mock_session.get.return_value.__aenter__.side_effect = [
        mock_response_fail,
        mock_response_success
    ]

    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        price = await moex_etf._get_price_investing()

        # Цена должна быть найдена со второго URL
        assert price == 3500.50


@pytest.mark.asyncio
async def test_get_price_investing_http_error(moex_etf, mock_session):
    """Тест ошибки HTTP при запросе к Investing.com"""
    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        mock_session.get.return_value.__aenter__.side_effect = Exception("HTTP Error")

        price = await moex_etf._get_price_investing()

        assert price is None


@pytest.mark.asyncio
async def test_integration_flow(moex_etf):
    """Интеграционный тест полного потока"""
    # Мокаем цепочку вызовов
    with patch.object(moex_etf, '_get_price_moex_iss') as mock_moex:
        with patch.object(moex_etf, '_get_price_investing') as mock_investing:
            with patch.object(moex_etf, '_get_fallback_price') as mock_fallback:
                # Тест 1: MOEX успешен
                mock_moex.return_value = 3500.50
                mock_investing.return_value = None
                mock_fallback.return_value = 35.0

                price1 = await moex_etf.get_price()
                assert price1.price == 3500.50

                # Очищаем кэш
                moex_etf._cache.clear()
                moex_etf._cache_time.clear()

                # Тест 2: MOEX неуспешен, Investing успешен
                mock_moex.return_value = None
                mock_investing.return_value = 3490.00

                price2 = await moex_etf.get_price()
                assert price2.price == 3490.00

                # Очищаем кэш
                moex_etf._cache.clear()
                moex_etf._cache_time.clear()

                # Тест 3: Все неуспешно, используем fallback
                mock_moex.return_value = None
                mock_investing.return_value = None

                price3 = await moex_etf.get_price()
                assert price3.price == 35.0


def test_symbol_uppercase_conversion(moex_etf):
    """Тест преобразования символа в верхний регистр"""
    # Проверяем, что тикер преобразуется правильно
    moex_etf.symbol = "fxgd"
    assert moex_etf.symbol == "fxgd"

    # В методе _get_price_moex_iss используется self.config.source_id
    assert moex_etf.config.source_id == "FXGD"


# Дополнительные тесты для проверки структуры ответов MOEX
@pytest.mark.asyncio
async def test_get_price_moex_iss_different_data_structures(moex_etf, mock_session):
    """Тест обработки разных структур данных от MOEX"""
    with patch.object(moex_etf, '_get_session', return_value=mock_session):
        # Тест 1: data есть, но список пустой
        mock_response1 = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response1.status = 200
        mock_response1.json = AsyncMock(return_value=[
            {},
            {"securities": {"columns": ["SECID", "LAST"], "data": []}}
        ])

        # Тест 2: securities нет в ответе
        mock_response2 = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response2.status = 200
        mock_response2.json = AsyncMock(return_value=[{}, {"other": "data"}])

        # Тест 3: неправильная структура ответа
        mock_response3 = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response3.status = 200
        mock_response3.json = AsyncMock(return_value=[{}])  # Только один элемент

        # Тест с первым случаем
        mock_session.get.return_value.__aenter__.return_value = mock_response1
        price1 = await moex_etf._get_price_moex_iss()
        assert price1 is None

        # Тест со вторым случаем
        mock_session.get.return_value.__aenter__.return_value = mock_response2
        price2 = await moex_etf._get_price_moex_iss()
        assert price2 is None

        # Тест с третьим случаем
        mock_session.get.return_value.__aenter__.return_value = mock_response3
        price3 = await moex_etf._get_price_moex_iss()
        assert price3 is None


if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v"])