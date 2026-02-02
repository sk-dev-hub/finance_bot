import aiohttp
import asyncio


async def test_api():
    async with aiohttp.ClientSession() as session:
        # Проверьте CoinGecko
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "usd"}
        async with session.get(url, params=params) as resp:
            print(f"CoinGecko status: {resp.status}")
            print(await resp.text())

        # Проверьте Binance
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}
        async with session.get(url, params=params) as resp:
            print(f"Binance status: {resp.status}")
            print(await resp.text())


asyncio.run(test_api())