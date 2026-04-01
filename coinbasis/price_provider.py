import requests

from coinbasis.utils.time import (
    datetime,
    timezone,
    get_time_window,
)
from config import (
    BASE_CURRENCY,
    COINGECKO_API_KEY,
    COINGECKO_URL,
    API_INTERVAL,
    API_TIME_WINDOW,
)


def get_usd_price_in_range(symbol: str, timestamp: datetime) -> list[tuple[datetime, float]]:
    if not COINGECKO_API_KEY:
        raise RuntimeError('COINGECKO_API_KEY not set')

    start, end = get_time_window(timestamp, API_TIME_WINDOW)
    url = COINGECKO_URL.format(id=symbol.lower())

    headers = {'x-cg-pro-api-key': COINGECKO_API_KEY}
    params = {
        'vs_currency': BASE_CURRENCY,
        'from': start.strftime('%Y-%m-%dT%H:%M'),
        'to': end.strftime('%Y-%m-%dT%H:%M'),
        'interval': API_INTERVAL,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    prices = data.get('prices', [])
    if not prices:
        raise ValueError(f'No price data returned for {symbol} at {timestamp}')

    result = []
    for unix_ms, price in prices:
        dt = datetime.fromtimestamp(unix_ms / 1000, tz=timezone.utc)
        result.append((dt, float(price)))

    return result


def get_usd_price_at_time(symbol: str, timestamp: datetime) -> float:
    raise NotImplementedError("Not implemented yet")