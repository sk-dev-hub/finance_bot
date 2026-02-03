import aiohttp
import asyncio


async def test_api():
    async with aiohttp.ClientSession() as session:
        print("=" * 50)
        print("Тестирование API ЦБ РФ")
        print("=" * 50)

        # Тест 1: Основной API для ежедневных курсов
        cbr_url = "https://www.cbr.ru/scripts/XML_daily.asp"
        print(f"\n1. Тестирование основного API: {cbr_url}")

        try:
            async with session.get(cbr_url) as resp:
                print(f"Статус: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"Успешно! Получено {len(text)} символов")

                    # Проверяем структуру XML
                    if "ValCurs" in text:
                        print("✓ XML структура корректна (содержит ValCurs)")
                    else:
                        print("✗ XML структура некорректна")

                    # Проверяем наличие валют
                    currencies_to_check = ["USD", "EUR", "CNY"]
                    for currency in currencies_to_check:
                        if currency in text:
                            print(f"✓ Валюта {currency} найдена")
                        else:
                            print(f"✗ Валюта {currency} не найдена")
                else:
                    print(f"Ошибка: статус {resp.status}")
        except Exception as e:
            print(f"Ошибка при запросе: {e}")

        print("\n" + "=" * 50)

        # Тест 2: Динамический API для исторических данных
        print("\n2. Тестирование динамического API")

        # Параметры для USD за последние 7 дней
        import datetime
        today = datetime.datetime.now()
        week_ago = today - datetime.timedelta(days=7)

        cbr_dynamic_url = "https://www.cbr.ru/scripts/XML_dynamic.asp"
        params = {
            'date_req1': week_ago.strftime('%d/%m/%Y'),
            'date_req2': today.strftime('%d/%m/%Y'),
            'VAL_NM_RQ': 'R01235'  # Код USD
        }

        print(f"URL: {cbr_dynamic_url}")
        print(f"Параметры: {params}")

        try:
            async with session.get(cbr_dynamic_url, params=params) as resp:
                print(f"Статус: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"Успешно! Получено {len(text)} символов")

                    if "ValCurs" in text and "Record" in text:
                        print("✓ XML структура корректна")
                        # Считаем количество записей
                        record_count = text.count("<Record ")
                        print(f"✓ Найдено записей курса: {record_count}")
                    else:
                        print("✗ XML структура некорректна")
                else:
                    print(f"Ошибка: статус {resp.status}")
        except Exception as e:
            print(f"Ошибка при запросе: {e}")

        print("\n" + "=" * 50)

        # Тест 3: API с параметром даты
        print("\n3. Тестирование API с конкретной датой")

        test_date = "01/01/2024"
        params_with_date = {'date_req': test_date}

        try:
            async with session.get(cbr_url, params=params_with_date) as resp:
                print(f"Запрос курсов на дату: {test_date}")
                print(f"Статус: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    if test_date.replace("/", ".") in text:
                        print(f"✓ Данные за {test_date} получены успешно")
                    else:
                        print("✗ Данные за указанную дату не найдены")
                else:
                    print(f"Ошибка: статус {resp.status}")
        except Exception as e:
            print(f"Ошибка при запросе: {e}")

        print("\n" + "=" * 50)

        # Тест 4: Получаем курс конкретной валюты (USD)
        print("\n4. Получение текущего курса USD/RUB")

        try:
            async with session.get(cbr_url) as resp:
                if resp.status == 200:
                    text = await resp.text()

                    # Ищем USD в XML
                    import re
                    # Паттерн для поиска USD курса
                    usd_pattern = r'<Valute ID="R01235">.*?<Value>([\d,]+)</Value>'
                    match = re.search(usd_pattern, text, re.DOTALL)

                    if match:
                        usd_rate = match.group(1).replace(',', '.')
                        print(f"✓ Текущий курс USD/RUB: {usd_rate}")

                        # Проверяем, что курс - валидное число
                        try:
                            rate_float = float(usd_rate)
                            print(f"✓ Курс в числовом формате: {rate_float}")
                            if 10 < rate_float < 200:  # Реалистичный диапазон для рубля
                                print("✓ Курс в реалистичном диапазоне")
                            else:
                                print("⚠ Курс вне ожидаемого диапазона")
                        except ValueError:
                            print("✗ Не удалось преобразовать курс в число")
                    else:
                        print("✗ Курс USD не найден в ответе")
                else:
                    print(f"✗ Ошибка при получении данных: {resp.status}")
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n" + "=" * 50)

        # Проверьте CoinGecko
        print("\n5. Тестирование CoinGecko API")
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "usd"}
        try:
            async with session.get(url, params=params) as resp:
                print(f"CoinGecko статус: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ Bitcoin цена: ${data['bitcoin']['usd']}")
                else:
                    print(f"✗ Ошибка: {resp.status}")
                    print(await resp.text())
        except Exception as e:
            print(f"Ошибка CoinGecko: {e}")

        print("\n" + "=" * 50)

        # Проверьте Binance
        print("\n6. Тестирование Binance API")
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}
        try:
            async with session.get(url, params=params) as resp:
                print(f"Binance статус: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ BTC/USDT цена: ${data['price']}")
                else:
                    print(f"✗ Ошибка: {resp.status}")
                    print(await resp.text())
        except Exception as e:
            print(f"Ошибка Binance: {e}")


if __name__ == "__main__":
    print("Запуск тестов API...")
    asyncio.run(test_api())