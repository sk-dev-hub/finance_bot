# src/tests/test_cbr_service.py
"""
Тесты для CBR сервиса
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

# Абсолютный импорт
from ..services.cbr_service import CBRService


class TestCBRService:
    """Тесты для сервиса ЦБ РФ"""

    @pytest.fixture
    def cbr_service(self):
        """Создает экземпляр сервиса для тестов"""
        service = CBRService()
        yield service
        # Очистка после теста
        if service.session and not service.session.closed:
            asyncio.run(service.close())

    def test_initialization(self, cbr_service):
        """Тест инициализации сервиса"""
        assert cbr_service is not None
        assert hasattr(cbr_service, 'CBR_API_URL')
        assert cbr_service.CBR_API_URL == "https://www.cbr.ru/scripts/XML_daily.asp"
        assert 'usd' in cbr_service.CURRENCY_CODES
        assert cbr_service.CURRENCY_CODES['usd'] == 'R01235'

    def test_parse_daily_rates(self, cbr_service):
        """Тест парсинга XML данных"""
        xml_data = '''
            <ValCurs Date="03.02.2026" name="Foreign Currency Market">
                <Valute ID="R01235">
                    <CharCode>USD</CharCode>
                    <Nominal>1</Nominal>
                    <Value>91,2345</Value>
                </Valute>
                <Valute ID="R01239">
                    <CharCode>EUR</CharCode>
                    <Nominal>1</Nominal>
                    <Value>99,8765</Value>
                </Valute>
                <Valute ID="R01375">
                    <CharCode>CNY</CharCode>
                    <Nominal>10</Nominal>
                    <Value>127,5432</Value>
                </Valute>
            </ValCurs>
        '''

        rates = cbr_service._parse_daily_rates(xml_data)

        assert 'usd' in rates
        assert 'eur' in rates
        assert 'cny' in rates
        assert rates['usd'] == 91.2345
        assert rates['eur'] == 99.8765
        assert rates['cny'] == 12.75432  # 127.5432 / 10

    def test_parse_daily_rates_empty_xml(self, cbr_service):
        """Тест парсинга пустого XML"""
        xml_data = '<ValCurs Date="03.02.2026"></ValCurs>'

        rates = cbr_service._parse_daily_rates(xml_data)

        assert isinstance(rates, dict)
        assert len(rates) == 0

    def test_parse_daily_rates_invalid_xml(self, cbr_service):
        """Тест парсинга невалидного XML"""
        xml_data = 'invalid xml data'

        rates = cbr_service._parse_daily_rates(xml_data)

        assert isinstance(rates, dict)
        assert len(rates) == 0

    def test_parse_dynamic_rate(self, cbr_service):
        """Тест парсинга динамики курса"""
        xml_data = '''
            <ValCurs ID="R01235" DateRange1="01.02.2026" DateRange2="03.02.2026" name="Foreign Currency Market">
                <Record Date="01.02.2026" Id="R01235">
                    <Nominal>1</Nominal>
                    <Value>90,1234</Value>
                </Record>
                <Record Date="02.02.2026" Id="R01235">
                    <Nominal>1</Nominal>
                    <Value>91,2345</Value>
                </Record>
            </ValCurs>
        '''

        rate = cbr_service._parse_dynamic_rate(xml_data, 'usd')

        assert rate == 91.2345  # Последняя запись

    def test_parse_dynamic_rate_empty(self, cbr_service):
        """Тест парсинга пустой динамики"""
        xml_data = '''
            <ValCurs ID="R01235" DateRange1="01.02.2026" DateRange2="03.02.2026" name="Foreign Currency Market">
            </ValCurs>
        '''

        rate = cbr_service._parse_dynamic_rate(xml_data, 'usd')

        assert rate is None

    @pytest.mark.asyncio
    async def test_get_available_currencies(self, cbr_service):
        """Тест получения списка доступных валют"""
        currencies = await cbr_service.get_available_currencies()

        assert isinstance(currencies, list)
        assert len(currencies) > 0
        assert 'usd' in currencies
        assert 'eur' in currencies
        assert 'cny' in currencies

    def test_clear_cache(self, cbr_service):
        """Тест очистки кэша"""
        # Добавляем тестовые данные в кэш
        cbr_service.cache['test_key'] = {'rate': 100.0}
        cbr_service.cache_time['test_key'] = datetime.now()

        assert len(cbr_service.cache) == 1
        assert len(cbr_service.cache_time) == 1

        # Очищаем кэш
        cbr_service.clear_cache()

        assert len(cbr_service.cache) == 0
        assert len(cbr_service.cache_time) == 0

    @pytest.mark.asyncio
    async def test_close_session(self, cbr_service):
        """Тест закрытия сессии"""
        # Создаем мок сессии
        mock_session = AsyncMock()
        mock_session.closed = False
        cbr_service.session = mock_session

        await cbr_service.close()

        mock_session.close.assert_called_once()
        assert cbr_service.session is None

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_usd_rub_rate_success(self, mock_get):
        """Тест успешного получения курса USD/RUB (с моком)"""
        # Создаем мок ответа
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '''
            <ValCurs Date="03.02.2026" name="Foreign Currency Market">
                <Valute ID="R01235">
                    <CharCode>USD</CharCode>
                    <Nominal>1</Nominal>
                    <Value>91,2345</Value>
                </Valute>
            </ValCurs>
        '''

        # Настраиваем мок
        mock_get.return_value.__aenter__.return_value = mock_response

        # Создаем сервис
        service = CBRService()

        try:
            # Вызываем метод
            rate = await service.get_usd_rub_rate()

            # Проверяем результат
            assert rate == 91.2345
            mock_get.assert_called_once()

            # Проверяем, что был вызван правильный URL
            call_args = mock_get.call_args
            assert 'https://www.cbr.ru/scripts/XML_daily.asp' in str(call_args[0])
        finally:
            # Закрываем сессию
            await service.close()

    @pytest.mark.asyncio
    async def test_convert_currency_same(self, cbr_service):
        """Тест конвертации в ту же валюту"""
        result = await cbr_service.convert_currency(100, 'usd', 'usd')

        assert result == 100.0

    @pytest.mark.asyncio
    async def test_convert_currency_different(self):
        """Тест конвертации между разными валютами"""
        # Создаем сервис
        service = CBRService()

        # Создаем моки для get_currency_rate
        mock_get_rate = AsyncMock()

        # Настраиваем возвращаемые значения
        mock_get_rate.side_effect = lambda currency, date=None: {
            'usd': 90.0,
            'eur': 100.0
        }.get(currency.lower())

        # Заменяем метод в сервисе
        service.get_currency_rate = mock_get_rate

        try:
            # Конвертируем 100 USD в EUR
            result = await service.convert_currency(100, 'usd', 'eur')

            # Проверяем: 100 USD * (90 RUB/USD / 100 RUB/EUR) = 90 EUR
            assert result == 90.0
            assert mock_get_rate.call_count == 2
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_convert_currency_with_none_rate(self):
        """Тест конвертации когда один из курсов None"""
        # Создаем сервис
        service = CBRService()

        # Создаем моки для get_currency_rate
        mock_get_rate = AsyncMock()

        # Настраиваем возвращаемые значения (один курс None)
        mock_get_rate.side_effect = lambda currency, date=None: {
            'usd': 90.0,
            'eur': None  # Этот курс не будет найден
        }.get(currency.lower())

        # Заменяем метод в сервисе
        service.get_currency_rate = mock_get_rate

        try:
            # Конвертируем 100 USD в EUR
            result = await service.convert_currency(100, 'usd', 'eur')

            # Должно вернуться None, так как один из курсов None
            assert result is None
            assert mock_get_rate.call_count == 2
        finally:
            await service.close()


# Простые интеграционные тесты (без моков)
@pytest.mark.skipif(True, reason="Интеграционные тесты требуют сетевого подключения")
class TestCBRServiceIntegration:
    """Интеграционные тесты CBR сервиса"""

    @pytest.mark.asyncio
    async def test_currency_codes_exist(self):
        """Тест что коды валют определены"""
        service = CBRService()
        try:
            assert 'usd' in service.CURRENCY_CODES
            assert 'eur' in service.CURRENCY_CODES
            assert 'cny' in service.CURRENCY_CODES
            assert service.CURRENCY_CODES['usd'] == 'R01235'
        finally:
            await service.close()

    def test_parse_xml_structure(self):
        """Тест парсинга XML структуры"""
        service = CBRService()

        xml_data = '''
            <ValCurs Date="03.02.2026" name="Foreign Currency Market">
                <Valute ID="R01235">
                    <CharCode>USD</CharCode>
                    <Nominal>1</Nominal>
                    <Value>91,2345</Value>
                </Valute>
            </ValCurs>
        '''

        rates = service._parse_daily_rates(xml_data)

        assert 'usd' in rates
        assert rates['usd'] == 91.2345