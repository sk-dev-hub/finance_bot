# src/test_simple_repo.py
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.simple_repo import portfolio_repo


def test_simple_repo():
    print("=== Testing Simple Repository ===")

    # 1. Проверим путь к файлу
    print(f"Data file: {portfolio_repo.data_file}")
    print(f"File exists: {portfolio_repo.data_file.exists()}")

    # 2. Проверим загруженные данные
    print(f"\nUsers loaded: {len(portfolio_repo.data)}")

    # 3. Тестируем добавление актива
    test_user_id = 123456
    print(f"\n--- Testing user {test_user_id} ---")

    # Создаем/получаем пользователя
    portfolio = portfolio_repo.get_or_create_user(test_user_id, "test_user")
    print(f"Portfolio created: {portfolio['user_id']}, assets: {len(portfolio['assets'])}")

    # Добавляем актив
    print(f"\nAdding BTC...")
    success, message = portfolio_repo.add_asset(test_user_id, "btc", 0.5)
    print(f"Add result: {success} - {message}")

    # Проверяем что добавилось
    portfolio = portfolio_repo.get_portfolio(test_user_id)
    assets = portfolio.get("assets", {})
    print(f"Assets after add: {assets}")
    print(f"BTC amount: {assets.get('btc', {}).get('amount', 0)}")

    # 4. Проверяем health check
    print(f"\n--- Health Check ---")
    health = portfolio_repo.health_check()
    for key, value in health.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_simple_repo()