import requests

from coinbasis.cache_manager import PriceCache
from coinbasis.utils.time import (
    datetime,
    timezone,
    get_time_window,
    to_iso_minute,
)
from config import (
    BASE_CURRENCY,
    COINGECKO_API_KEY,
    COINGECKO_URL,
    API_INTERVAL,
    API_TIME_WINDOW,
)


PRICE_CACHE = PriceCache('data/cache/prices.json')


def get_usd_price_in_range(symbol: str, timestamp: datetime) -> list[tuple[datetime, float]]:
    if not COINGECKO_API_KEY:
        raise RuntimeError('COINGECKO_API_KEY not set')

    start, end = get_time_window(timestamp, API_TIME_WINDOW)
    url = COINGECKO_URL.format(id=symbol.lower())

    headers = {'x-cg-pro-api-key': COINGECKO_API_KEY}
    params = {
        'vs_currency': BASE_CURRENCY,
        'from': to_iso_minute(start),
        'to': to_iso_minute(end),
        'interval': API_INTERVAL,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    if not response.json():
        raise ValueError(f'No price data returned for {symbol} at {timestamp}')

    return response.json()


def get_usd_price_at_time(symbol: str, timestamp: datetime) -> float:
    price = PRICE_CACHE.lookup(symbol, timestamp)
    if price is not None:
        return price

    price_points = get_usd_price_in_range(symbol, timestamp)
    merged = merge_price_volume(price_points)
    PRICE_CACHE.store_points(symbol, merged)

    return get_usd_price_at_time(symbol, timestamp)


def merge_price_volume(data: dict) -> list[tuple[datetime, float, float]]:
    prices = data.get('prices', [])
    volumes = data.get('total_volumes', [])

    volume_map = {ts: vol for ts, vol in volumes}
    merged = []
    for ts, price in prices:
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        volume = volume_map.get(ts, 0.0)
        merged.append((dt, float(price), float(volume)))

    return merged