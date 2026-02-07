# src/tests/test_cbr_metals_service.py
"""
Тесты для сервиса учетных цен металлов ЦБ РФ
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

# Абсолютный импорт (в зависимости от структуры проекта)
from ..services.cbr_metals_service import CBRMetalsService


class TestCBRMetalsService:
    """Тесты для сервиса учетных цен драгметаллов ЦБ РФ"""

    @pytest.fixture
    def metals_service(self):
        """Создает экземпляр сервиса для тестов"""
        service = CBRMetalsService()
        yield service
        # Очистка после теста
        if service.session and not service.session.closed:
            asyncio.run(service.close())

    def test_initialization(self, metals_service):
        """Тест инициализации сервиса"""
        assert metals_service is not None
        assert hasattr(metals_service, 'CBR_METALS_URL')
        assert metals_service.CBR_METALS_URL == "https://www.cbr.ru/scripts/xml_metall.asp"
        assert 'gold' in metals_service.METAL_CODES
        assert metals_service.METAL_CODES['gold'] == '1'
        assert 'silver' in metals_service.METAL_CODES
        assert metals_service.METAL_CODES['silver'] == '2'

    def test_parse_metal_price_gold(self, metals_service):
        """Тест парсинга XML с ценой золота"""
        xml_data = '''
            <MetallCurs Date="03.02.2026">
                <Record Code="1" Date="03.02.2026">
                    <Buy>0</Buy>
                    <Sell>0</Sell>
                    <Price>7854.12</Price>
                </Record>
                <Record Code="2" Date="03.02.2026">
                    <Buy>0</Buy>
                    <Sell>0</Sell>
                    <Price>92.34</Price>
                </Record>
            </MetallCurs>
        '''

        price = metals_service._parse_metal_price(xml_data, 'gold', None)
        assert price == 7854.12

    def test_parse_metal_price_silver(self, metals_service):
        """Тест парсинга XML с ценой серебра"""
        xml_data = '''
            <MetallCurs Date="03.02.2026">
                <Record Code="2" Date="03.02.2026">
                    <Price>92.3456</Price>
                </Record>
            </MetallCurs>
        '''

        price = metals_service._parse_metal_price(xml_data, 'silver', None)
        assert price == 92.3456

    def test_parse_metal_price_not_found(self, metals_service):
        """Тест когда металл не найден в XML"""
        xml_data = '''
            <MetallCurs Date="03.02.2026">
                <Record Code="3" Date="03.02.2026">
                    <Price>4500.00</Price>
                </Record>
            </MetallCurs>
        '''

        price = metals_service._parse_metal_price(xml_data, 'gold', None)
        assert price is None

    def test_parse_metal_price_empty_xml(self, metals_service):
        """Тест парсинга пустого XML"""
        xml_data = '<MetallCurs Date="03.02.2026"></MetallCurs>'
        price = metals_service._parse_metal_price(xml_data, 'gold', None)
        assert price is None

    def test_parse_metal_price_invalid_xml(self, metals_service):
        """Тест парсинга невалидного XML"""
        xml_data = 'some broken data'
        price = metals_service._parse_metal_price(xml_data, 'gold', None)
        assert price is None

    def test_parse_metal_price_wrong_date(self, metals_service):
        """Тест когда дата в XML не совпадает с запрошенной"""
        xml_data = '''
            <MetallCurs>
                <Record Code="1" Date="01.02.2026">
                    <Price>7800.00</Price>
                </Record>
            </MetallCurs>
        '''

        requested_date = datetime(2026, 2, 3)
        price = metals_service._parse_metal_price(xml_data, 'gold', requested_date)
        assert price is None

    @pytest.mark.asyncio
    async def test_get_available_metals_implicit(self, metals_service):
        """Проверка, что основные металлы доступны через методы"""
        assert hasattr(metals_service, 'get_gold_price_rub')
        assert hasattr(metals_service, 'get_silver_price_rub')

    def test_clear_cache(self, metals_service):
        """Тест очистки кэша"""
        # Добавляем тестовые данные
        metals_service.cache['gold_20260203'] = {'rate': 7850.0, 'fetched': datetime.now()}
        metals_service.cache_time['gold_20260203'] = datetime.now()

        assert len(metals_service.cache) == 1
        assert len(metals_service.cache_time) == 1

        metals_service.clear_cache()

        assert len(metals_service.cache) == 0
        assert len(metals_service.cache_time) == 0

    @pytest.mark.asyncio
    async def test_close_session(self, metals_service):
        """Тест закрытия сессии"""
        mock_session = AsyncMock()
        mock_session.closed = False
        metals_service.session = mock_session

        await metals_service.close()

        mock_session.close.assert_called_once()
        assert metals_service.session is None

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_gold_price_rub_success(self, mock_get, metals_service):
        """Тест успешного получения цены золота (с моком)"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '''
            <MetallCurs Date="03.02.2026">
                <Record Code="1" Date="03.02.2026">
                    <Price>7854.67</Price>
                </Record>
            </MetallCurs>
        '''

        mock_get.return_value.__aenter__.return_value = mock_response

        try:
            price = await metals_service.get_gold_price_rub()
            assert price == 7854.67
            mock_get.assert_called_once()

            call_args = mock_get.call_args
            assert 'https://www.cbr.ru/scripts/xml_metall.asp' in str(call_args[0][0])
        finally:
            await metals_service.close()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_gold_price_rub_on_date(self, mock_get, metals_service):
        """Тест получения цены золота на конкретную дату"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '''
            <MetallCurs>
                <Record Code="1" Date="31.12.2025">
                    <Price>8100.25</Price>
                </Record>
            </MetallCurs>
        '''

        mock_get.return_value.__aenter__.return_value = mock_response

        test_date = datetime(2025, 12, 31)

        try:
            price = await metals_service.get_gold_price_rub(test_date)
            assert price == 8100.25
            mock_get.assert_called_once()

            # Проверяем, что были переданы параметры date_req1 и date_req2
            call_kwargs = mock_get.call_args[1]
            assert 'params' in call_kwargs
            assert call_kwargs['params']['date_req1'] == '31/12/2025'
            assert call_kwargs['params']['date_req2'] == '31/12/2025'
        finally:
            await metals_service.close()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_gold_price_rub_http_error(self, mock_get, metals_service):
        """Тест обработки HTTP ошибки"""
        mock_response = AsyncMock()
        mock_response.status = 404

        mock_get.return_value.__aenter__.return_value = mock_response

        try:
            price = await metals_service.get_gold_price_rub()
            assert price is None
        finally:
            await metals_service.close()


# Интеграционные тесты (пропускаем, если не нужен реальный запрос)
@pytest.mark.skipif(True, reason="Интеграционные тесты требуют сетевого подключения")
class TestCBRMetalsServiceIntegration:
    """Интеграционные тесты сервиса металлов"""

    @pytest.mark.asyncio
    async def test_gold_code_exists(self):
        service = CBRMetalsService()
        try:
            assert 'gold' in service.METAL_CODES
            assert service.METAL_CODES['gold'] == '1'
        finally:
            await service.close()