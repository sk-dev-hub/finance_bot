# src/tests/test_simple_repo.py
"""
Тесты для simple_repo
"""
import pytest
import tempfile
import os

# Абсолютный импорт
from ..database.simple_repo import SimplePortfolioRepository


class TestPortfolioRepository:
    """Тесты для репозитория портфеля"""

    @pytest.fixture
    def repo(self):
        """Создает временный репозиторий для тестов"""
        # Создаем временный файл БД
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            db_file = f.name

        # Создаем репозиторий с временным файлом
        repo = SimplePortfolioRepository(db_file)
        yield repo

        # Очистка после теста
        repo._save_data()
        os.unlink(db_file)

    def test_initialization(self, repo):
        """Тест инициализации репозитория"""
        assert repo is not None
        assert hasattr(repo, 'data_file')
        assert hasattr(repo, 'data')
        assert isinstance(repo.data, dict)

    def test_get_or_create_user_new(self, repo):
        """Тест создания нового пользователя"""
        user_id = 12345
        username = "test_user"

        portfolio = repo.get_or_create_user(user_id, username)

        assert portfolio is not None
        assert 'user_id' in portfolio
        assert 'username' in portfolio
        assert 'assets' in portfolio
        assert portfolio['user_id'] == user_id
        assert portfolio['username'] == username
        assert isinstance(portfolio['assets'], dict)
        assert len(portfolio['assets']) == 0

    def test_get_or_create_user_existing(self, repo):
        """Тест получения существующего пользователя"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя
        portfolio1 = repo.get_or_create_user(user_id, username)
        portfolio1['assets']['btc'] = {'amount': 1.0}

        # Получаем того же пользователя
        portfolio2 = repo.get_or_create_user(user_id, username)

        assert portfolio2['assets']['btc']['amount'] == 1.0

    def test_add_asset_new(self, repo):
        """Тест добавления нового актива"""
        user_id = 12345
        username = "test_user"
        symbol = 'btc'
        amount = 0.5

        # Сначала создаем пользователя
        repo.get_or_create_user(user_id, username)

        # Теперь добавляем актив
        success, message = repo.add_asset(user_id, symbol, amount)

        assert success is True
        assert 'добавлено' in message.lower() or 'успешно' in message.lower()

        # Проверяем что актив добавлен
        portfolio = repo.get_or_create_user(user_id, username)
        assert symbol in portfolio['assets']
        assert portfolio['assets'][symbol]['amount'] == amount

    def test_add_asset_existing(self, repo):
        """Тест добавления к существующему активу"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя
        repo.get_or_create_user(user_id, username)

        # Добавляем актив первый раз
        repo.add_asset(user_id, 'btc', 0.5)

        # Добавляем еще
        success, message = repo.add_asset(user_id, 'btc', 0.3)

        assert success is True
        assert 'добавлено' in message.lower() or 'успешно' in message.lower()

        # Проверяем что сумма правильная
        portfolio = repo.get_or_create_user(user_id, username)
        assert portfolio['assets']['btc']['amount'] == 0.8

    def test_add_asset_invalid_amount(self, repo):
        """Тест добавления с невалидным количеством"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя
        repo.get_or_create_user(user_id, username)

        success, message = repo.add_asset(user_id, 'btc', -1.0)

        assert success is False
        assert 'должно' in message.lower() or 'больше 0' in message.lower()

    def test_add_asset_zero_amount(self, repo):
        """Тест добавления с нулевым количеством"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя
        repo.get_or_create_user(user_id, username)

        success, message = repo.add_asset(user_id, 'btc', 0.0)

        assert success is False
        assert 'должно' in message.lower() or 'больше 0' in message.lower()

    def test_remove_asset_completely(self, repo):
        """Тест полного удаления актива"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем актив
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.5)

        # Удаляем весь актив
        success, message = repo.remove_asset(user_id, 'btc', None)

        assert success is True
        assert 'удален' in message.lower()

        # Проверяем что актив удален
        portfolio = repo.get_or_create_user(user_id, username)
        assert 'btc' not in portfolio['assets']

    def test_remove_asset_partially(self, repo):
        """Тест частичного удаления актива"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем актив
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.5)

        # Удаляем часть
        success, message = repo.remove_asset(user_id, 'btc', 0.2)

        assert success is True
        assert 'удалено' in message.lower()

        # Проверяем остаток
        portfolio = repo.get_or_create_user(user_id, username)
        assert portfolio['assets']['btc']['amount'] == 0.3

    def test_remove_asset_not_found(self, repo):
        """Тест удаления несуществующего актива"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя
        repo.get_or_create_user(user_id, username)

        success, message = repo.remove_asset(user_id, 'btc', 0.5)

        assert success is False
        assert 'нет такого' in message.lower() or 'не найден' in message.lower()

    def test_remove_asset_insufficient(self, repo):
        """Тест удаления больше чем есть"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем актив
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.3)

        # Пытаемся удалить больше
        success, message = repo.remove_asset(user_id, 'btc', 0.5)

        assert success is False
        assert 'недостаточно' in message.lower()

    def test_get_user_assets(self, repo):
        """Тест получения активов пользователя"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем активы
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.5)
        repo.add_asset(user_id, 'eth', 2.0)

        assets = repo.get_user_assets(user_id)

        assert isinstance(assets, dict)
        assert 'btc' in assets
        assert 'eth' in assets
        assert assets['btc']['amount'] == 0.5
        assert assets['eth']['amount'] == 2.0

    def test_get_user_assets_not_found(self, repo):
        """Тест получения активов несуществующего пользователя"""
        assets = repo.get_user_assets(99999)

        assert isinstance(assets, dict)
        assert len(assets) == 0

    def test_get_portfolio(self, repo):
        """Тест получения всего портфеля"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем актив
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.5)

        portfolio = repo.get_portfolio(user_id)

        assert portfolio is not None
        assert portfolio['user_id'] == user_id
        assert portfolio['username'] == username
        assert 'btc' in portfolio['assets']
        assert 'created_at' in portfolio
        assert 'updated_at' in portfolio

    def test_get_portfolio_not_found(self, repo):
        """Тест получения портфеля несуществующего пользователя"""
        portfolio = repo.get_portfolio(99999)

        assert portfolio is None

    def test_get_all_users(self, repo):
        """Тест получения всех пользователей"""
        # Создаем несколько пользователей
        repo.get_or_create_user(12345, "user1")
        repo.add_asset(12345, 'btc', 0.5)

        repo.get_or_create_user(67890, "user2")
        repo.add_asset(67890, 'eth', 2.0)

        users = repo.get_all_users()

        assert isinstance(users, list)
        assert len(users) == 2

        # Проверяем структуру
        for user in users:
            assert 'user_id' in user
            assert 'username' in user
            assert 'asset_count' in user
            assert 'created_at' in user
            assert 'updated_at' in user

    def test_clear_portfolio(self, repo):
        """Тест очистки портфеля"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем активы
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.5)
        repo.add_asset(user_id, 'eth', 2.0)

        # Очищаем портфель
        success, message = repo.clear_portfolio(user_id)

        assert success is True
        assert 'очищен' in message.lower()

        # Проверяем что активов нет
        assets = repo.get_user_assets(user_id)
        assert len(assets) == 0

    def test_clear_empty_portfolio(self, repo):
        """Тест очистки пустого портфеля"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя без активов
        repo.get_or_create_user(user_id, username)

        # Пытаемся очистить
        success, message = repo.clear_portfolio(user_id)

        assert success is False
        assert 'уже пуст' in message.lower()

    def test_health_check(self, repo):
        """Тест проверки здоровья"""
        # Добавляем пользователя для данных
        repo.get_or_create_user(12345, "test_user")

        health = repo.health_check()

        assert isinstance(health, dict)
        assert 'status' in health
        assert 'total_users' in health
        assert 'total_assets' in health
        assert health['status'] == 'healthy'
        assert health['initialized'] is True

    def test_save_method(self, repo):
        """Тест публичного метода сохранения"""
        user_id = 12345
        username = "test_user"

        # Создаем пользователя и добавляем актив
        repo.get_or_create_user(user_id, username)
        repo.add_asset(user_id, 'btc', 0.5)

        # Сохраняем через публичный метод
        success = repo.save()

        assert success is True

    def test_update_username(self, repo):
        """Тест обновления имени пользователя"""
        user_id = 12345

        # Создаем пользователя
        repo.get_or_create_user(user_id, "old_username")

        # Обновляем имя
        portfolio = repo.get_or_create_user(user_id, "new_username")

        assert portfolio['username'] == "new_username"