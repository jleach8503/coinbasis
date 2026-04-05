import requests
from typing import Iterable, Set
from coinbasis.models import Transaction

from coinbasis.cache_manager import (
    PriceCache,
    CoinMapCache,
    CoinNotFoundError,
    MultipleCoinsError,
)
from coinbasis.utils.time import (
    TimeRange,
    datetime,
    timezone,
    get_time_window,
    to_iso_minute,
    apply_min_date,
)
from config import (
    BASE_CURRENCY,
    COINGECKO_API_KEY,
    COINGECKO_URL,
    COINGECKO_COIN_MAP,
    API_INTERVAL,
    API_TIME_RANGE,
    CACHE_PATH,
    API_MIN_DAYS,
)


PRICE_CACHE = PriceCache(CACHE_PATH)
COIN_ID_CACHE = CoinMapCache(COINGECKO_COIN_MAP)

def get_usd_price_in_range(symbol: str, timestamp: datetime) -> list[tuple[datetime, float]]:
    if not COINGECKO_API_KEY:
        raise RuntimeError('COINGECKO_API_KEY not set')

    coin_id = COIN_ID_CACHE.lookup(symbol)
    start, end = get_time_window(timestamp, TimeRange(API_TIME_RANGE))

    url = COINGECKO_URL.format(id=coin_id)

    headers = {'x-cg-pro-api-key': COINGECKO_API_KEY}
    params = {
        'vs_currency': BASE_CURRENCY,
        'from': to_iso_minute(apply_min_date(start, API_MIN_DAYS)),
        'to': to_iso_minute(end),
        'interval': API_INTERVAL,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    if not response.json():
        raise ValueError(f'No price data returned for {symbol} ({coin_id}) at {timestamp}')

    return response.json()


def get_usd_price_at_time(symbol: str, timestamp: datetime) -> float:
    coin_id = COIN_ID_CACHE.lookup(symbol)
    price = PRICE_CACHE.lookup(coin_id, timestamp)
    if price is None:
        price_points = get_usd_price_in_range(coin_id, timestamp)
        merged = merge_price_volume(price_points)
        PRICE_CACHE.store_points(coin_id, merged)
        price = PRICE_CACHE.lookup(coin_id, timestamp)

    return price


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


def resolve_symbol_interactively(symbol: str, entries: list[dict]) -> str:
    print(f'\nMultiple coin IDs found for symbol: {symbol}')

    for idx, entry in enumerate(entries):
        coin_id = entry['coin_id']
        coin_name = entry['name']
        print(f'[{idx}] {coin_id:20} - {coin_name}')

    while True:
        choice = input('Select the correct coin_id: ').strip()
        if choice.isdigit() and int(choice) in range(len(entries)):
            return entries[int(choice)]['coin_id']
        print('Invalid selection. Try again.')


def resolve_all_symbols(symbols: list[str], coin_map: CoinMapCache):
    for symbol in symbols:
        try:
            resolved = coin_map.lookup(symbol)
        except MultipleCoinsError:
            entries = coin_map.list_duplicates(symbol)
            resolved = resolve_symbol_interactively(symbol, entries)
            coin_map.prune(symbol, resolved)
        except CoinNotFoundError:
            raise


def get_unique_symbols(transactions: Iterable[Transaction]) -> Set[str]:
    symbols: set[str] = set()

    for tx in transactions:
        for field in ('received_currency', 'sent_currency', 'fee_currency'):
            value = getattr(tx, field)
            if value:
                symbol = value.lower()
                if symbol != BASE_CURRENCY.lower():
                    symbols.add(symbol)
    return symbols