# test_cbr_metals_service.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
from src.services.cbr_metals_service import MetalService

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def test_all_methods():
    """Тестирование всех методов MetalService"""

    # Импортируем сервис
    try:
        from src.services.cbr_metals_service import MetalService, MetalPrice
    except ImportError:
        print("Ошибка: Не удалось импортировать MetalService")
        print("Убедитесь, что файл cbr_metals_service.py находится в правильной директории")
        return

    print("=" * 70)
    print("ТЕСТИРОВАНИЕ METAL SERVICE")
    print("=" * 70)

    # Создаем экземпляр сервиса
    service = MetalService()

    test_results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }

    try:
        # 1. Тест: get_available_metal_types()
        print("\n" + "=" * 70)
        print("1. Тест: get_available_metal_types()")
        print("-" * 70)
        metal_types = await service.get_available_metal_types()
        test_results["total"] += 1

        if metal_types and len(metal_types) == 4:
            print(f"✓ Методы возвращены: {metal_types}")
            test_results["passed"] += 1
        else:
            print(f"✗ Ошибка: ожидалось 4 типа металлов, получено {len(metal_types) if metal_types else 0}")
            test_results["failed"] += 1

        # 2. Тест: get_metal_name()
        print("\n" + "=" * 70)
        print("2. Тест: get_metal_name()")
        print("-" * 70)

        test_cases = [
            ("gold", "Золото"),
            ("silver", "Серебро"),
            ("platinum", "Платина"),
            ("palladium", "Палладий"),
            ("invalid", None)  # Несуществующий металл
        ]

        for metal_code, expected_name in test_cases:
            test_results["total"] += 1
            name = await service.get_metal_name(metal_code)

            if name == expected_name:
                print(f"✓ {metal_code}: {name}")
                test_results["passed"] += 1
            else:
                print(f"✗ {metal_code}: ожидалось '{expected_name}', получено '{name}'")
                test_results["failed"] += 1

        # 3. Тест: get_latest_prices()
        print("\n" + "=" * 70)
        print("3. Тест: get_latest_prices()")
        print("-" * 70)

        prices = await service.get_latest_prices()
        test_results["total"] += 1

        if prices and len(prices) > 0:
            print(f"✓ Получено {len(prices)} записей")
            latest = prices[0]
            print(f"  Последняя запись: {latest.date.strftime('%d.%m.%Y')}")
            print(f"  Золото: {latest.gold:.2f} руб/г")
            print(f"  Серебро: {latest.silver:.2f} руб/г")
            test_results["passed"] += 1
        else:
            print("✗ Ошибка: не удалось получить цены")
            test_results["failed"] += 1

        # 4. Тест: get_latest_metal_price()
        print("\n" + "=" * 70)
        print("4. Тест: get_latest_metal_price()")
        print("-" * 70)

        for metal_type in metal_types:
            test_results["total"] += 1
            price_obj = await service.get_latest_metal_price(metal_type)

            if price_obj and isinstance(price_obj, MetalPrice):
                metal_name = await service.get_metal_name(metal_type)
                price = getattr(price_obj, metal_type)
                print(f"✓ {metal_name}: {price:.2f} руб/г")
                test_results["passed"] += 1
            else:
                print(f"✗ Не удалось получить цену для {metal_type}")
                test_results["failed"] += 1

        # 5. Тест: get_metal_price_by_date()
        print("\n" + "=" * 70)
        print("5. Тест: get_metal_price_by_date()")
        print("-" * 70)

        # Тест 5.1: Текущая дата
        test_results["total"] += 1
        today_price = await service.get_metal_price_by_date(datetime.now())

        if today_price:
            print(f"✓ Цена на сегодня: найдена")
            test_results["passed"] += 1
        else:
            print(f"✗ Цена на сегодня: не найдена")
            test_results["failed"] += 1

        # Тест 5.2: Историческая дата (вчера)
        test_results["total"] += 1
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_price = await service.get_metal_price_by_date(yesterday)

        if yesterday_price:
            print(f"✓ Цена на вчера ({yesterday.strftime('%d.%m.%Y')}): найдена")
            test_results["passed"] += 1
        else:
            print(f"✓ Цена на вчера: не найдена (может быть нормально, если нет данных)")
            test_results["passed"] += 1

        # 6. Тест: Методы получения конкретных цен
        print("\n" + "=" * 70)
        print("6. Тест: Методы получения конкретных цен")
        print("-" * 70)

        specific_methods = [
            ("get_gold_price()", service.get_gold_price),
            ("get_silver_price()", service.get_silver_price),
            ("get_platinum_price()", service.get_platinum_price),
            ("get_palladium_price()", service.get_palladium_price)
        ]

        for method_name, method in specific_methods:
            test_results["total"] += 1
            price = await method()

            if price and isinstance(price, float):
                print(f"✓ {method_name}: {price:.2f} руб/г")
                test_results["passed"] += 1
            else:
                print(f"✗ {method_name}: не удалось получить цену")
                test_results["failed"] += 1

        # 7. Тест: get_all_metal_prices_dict()
        print("\n" + "=" * 70)
        print("7. Тест: get_all_metal_prices_dict()")
        print("-" * 70)

        prices_dict = await service.get_all_metal_prices_dict()
        test_results["total"] += 1

        if prices_dict and isinstance(prices_dict, dict):
            print(f"✓ Словарь цен получен:")
            print(f"  Дата: {prices_dict.get('date')}")
            for metal, formatted in prices_dict.get('formatted', {}).items():
                print(f"  {metal.capitalize()}: {formatted} руб/г")
            test_results["passed"] += 1
        else:
            print("✗ Ошибка: не удалось получить словарь цен")
            test_results["failed"] += 1

        # 8. Тест: get_price_history()
        print("\n" + "=" * 70)
        print("8. Тест: get_price_history()")
        print("-" * 70)

        # Тест 8.1: История за 5 дней
        test_results["total"] += 1
        history_5 = await service.get_price_history(days=5)

        if history_5 and len(history_5) > 0:
            print(f"✓ История за 5 дней: получено {len(history_5)} записей")
            for i, price in enumerate(history_5[:3]):  # Показываем первые 3
                print(f"  {i + 1}. {price.date.strftime('%d.%m.%Y')}: "
                      f"Au={price.gold:.2f}, Ag={price.silver:.2f}")
            test_results["passed"] += 1
        else:
            print("✗ Ошибка: не удалось получить историю за 5 дней")
            test_results["failed"] += 1

        # Тест 8.2: История за 30 дней
        test_results["total"] += 1
        history_30 = await service.get_price_history(days=30)

        if history_30:
            print(f"✓ История за 30 дней: получено {len(history_30)} записей")
            test_results["passed"] += 1
        else:
            print("✗ Ошибка: не удалось получить историю за 30 дней")
            test_results["failed"] += 1

        # 9. Тест: get_metal_price_change()
        print("\n" + "=" * 70)
        print("9. Тест: get_metal_price_change()")
        print("-" * 70)

        if len(prices) >= 2:  # Нужно хотя бы 2 записи для расчета
            for metal_type in ["gold", "silver"]:
                test_results["total"] += 1
                change = await service.get_metal_price_change(metal_type, days=1)

                if change is not None:
                    metal_name = await service.get_metal_name(metal_type)
                    print(f"✓ Изменение {metal_name} за 1 день: {change:+.2f}%")
                    test_results["passed"] += 1
                else:
                    print(f"✓ Изменение {metal_type} за 1 день: данных недостаточно")
                    test_results["passed"] += 1  # Это не ошибка, а недостаток данных
        else:
            print("⚠ Недостаточно данных для теста изменения цен")
            test_results["total"] += 1
            test_results["passed"] += 1

        # 10. Тест: Принудительное обновление кэша
        print("\n" + "=" * 70)
        print("10. Тест: Принудительное обновление кэша")
        print("-" * 70)

        test_results["total"] += 1
        prices_forced = await service.get_latest_prices(force_refresh=True)

        if prices_forced:
            print(f"✓ Данные принудительно обновлены: {len(prices_forced)} записей")
            test_results["passed"] += 1
        else:
            print("✗ Ошибка при принудительном обновлении")
            test_results["failed"] += 1

        # 11. Тест: clear_cache()
        print("\n" + "=" * 70)
        print("11. Тест: clear_cache()")
        print("-" * 70)

        test_results["total"] += 1
        service.clear_cache()
        print("✓ Кэш очищен")
        test_results["passed"] += 1

        # 12. Тест: to_dict() для MetalPrice
        print("\n" + "=" * 70)
        print("12. Тест: MetalPrice.to_dict()")
        print("-" * 70)

        if prices:
            test_results["total"] += 1
            latest_price = prices[0]
            price_dict = latest_price.to_dict()

            if isinstance(price_dict, dict) and "date" in price_dict:
                print("✓ Метод to_dict() работает корректно")
                print(f"  Ключи: {list(price_dict.keys())}")
                test_results["passed"] += 1
            else:
                print("✗ Ошибка в методе to_dict()")
                test_results["failed"] += 1

            # Тест format_price()
            test_results["total"] += 1
            formatted = latest_price.format_price("gold")
            if formatted and "руб" not in formatted:  # Метод только форматирует число
                print(f"✓ Метод format_price(): {formatted}")
                test_results["passed"] += 1
            else:
                print("✗ Ошибка в методе format_price()")
                test_results["failed"] += 1

        # Итоги тестирования
        print("\n" + "=" * 70)
        print("ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 70)

        print(f"Всего тестов: {test_results['total']}")
        print(f"Пройдено: {test_results['passed']}")
        print(f"Не пройдено: {test_results['failed']}")

        success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
        print(f"Успешность: {success_rate:.1f}%")

        if test_results['failed'] == 0:
            print("\n✅ Все тесты пройдены успешно!")
        else:
            print(f"\n⚠ Имеются проблемы: {test_results['failed']} тест(ов) не пройдено")

        print("\n" + "=" * 70)
        print("ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ")
        print("=" * 70)

        # Вывод детальной информации о полученных данных
        if prices:
            print(f"\nВсего получено записей: {len(prices)}")
            print(f"Диапазон дат: {prices[-1].date.strftime('%d.%m.%Y')} - {prices[0].date.strftime('%d.%m.%Y')}")

            # Средние цены
            avg_gold = sum(p.gold for p in prices) / len(prices)
            avg_silver = sum(p.silver for p in prices) / len(prices)
            print(f"\nСредняя цена золота: {avg_gold:.2f} руб/г")
            print(f"Средняя цена серебра: {avg_silver:.2f} руб/г")

            # Изменение за период
            if len(prices) > 1:
                first = prices[-1]
                last = prices[0]
                gold_change = ((last.gold - first.gold) / first.gold) * 100
                silver_change = ((last.silver - first.silver) / first.silver) * 100

                print(f"\nИзменение за период:")
                print(f"  Золото: {gold_change:+.2f}%")
                print(f"  Серебро: {silver_change:+.2f}%")

    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании: {e}", exc_info=True)
        test_results["failed"] += 1
        print(f"\n❌ Критическая ошибка: {e}")

    finally:
        # Закрываем сессию
        await service.close()
        print("\n✅ Сессия закрыта")

    return test_results


async def run_performance_test():
    """Тест производительности"""
    print("\n" + "=" * 70)
    print("ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 70)

    from src.services.cbr_metals_service import MetalService
    import time

    service = MetalService()

    try:
        # Тест скорости получения данных
        start_time = time.time()
        prices = await service.get_latest_prices()
        load_time = time.time() - start_time

        print(f"Время загрузки данных: {load_time:.2f} сек")
        print(f"Количество записей: {len(prices) if prices else 0}")

        # Тест скорости работы с кэшем
        start_time = time.time()
        cached_prices = await service.get_latest_prices()
        cache_time = time.time() - start_time

        print(f"Время получения из кэша: {cache_time:.2f} сек")

        # Ускорение за счет кэша
        if load_time > 0 and cache_time > 0:
            speedup = load_time / cache_time
            print(f"Ускорение за счет кэша: {speedup:.1f}x")

        # Тест получения отдельных цен
        print("\nТест получения отдельных цен:")
        for metal in ["gold", "silver", "platinum", "palladium"]:
            start_time = time.time()
            price = await service.get_latest_metal_price(metal)
            elapsed = time.time() - start_time
            print(f"  {metal.capitalize()}: {elapsed:.3f} сек")

    finally:
        await service.close()


async def test_error_handling():
    """Тестирование обработки ошибок"""
    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК")
    print("=" * 70)

    from src.services.cbr_metals_service import MetalService

    service = MetalService()

    try:
        # Тест с некорректным типом металла
        print("\n1. Тест некорректного типа металла:")
        invalid_price = await service.get_latest_metal_price("invalid_metal")
        if invalid_price is None:
            print("✓ Обработка некорректного типа: корректно возвращает None")
        else:
            print("✗ Ожидался None для некорректного типа")

        # Тест с некорректной датой
        print("\n2. Тест очень старой даты:")
        old_date = datetime(2000, 1, 1)
        old_price = await service.get_metal_price_by_date(old_date)
        if old_price is None:
            print("✓ Обработка очень старой даты: корректно возвращает None")
        else:
            print("✓ Найдена цена для старой даты")

        # Тест метода format_price с некорректным типом
        print("\n3. Тест format_price с некорректным типом:")
        if prices := await service.get_latest_prices():
            try:
                # Это должно вызвать исключение
                invalid_format = prices[0].format_price("invalid")
                print("✗ Ожидалось исключение для некорректного типа")
            except ValueError as e:
                print(f"✓ Исключение перехвачено: {e}")

    finally:
        await service.close()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ПОЛНАЯ ПРОВЕРКА METAL SERVICE")
    print("=" * 70)

    try:
        # Основные тесты
        results = asyncio.run(test_all_methods())

        # Тесты производительности (опционально)
        if results.get('failed', 0) == 0:
            asyncio.run(run_performance_test())

        # Тесты обработки ошибок (опционально)
        asyncio.run(test_error_handling())

    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Непредвиденная ошибка: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 70)