import requests
import logging
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
logger = logging.getLogger(__name__)

def get_usd_price_in_range(coin_id: str, timestamp: datetime) -> dict[str, list[list[float]]]:
    if not COINGECKO_API_KEY:
        logger.error('COINGECKO_API_KEY not set - cannot fetch price data')
        raise RuntimeError('COINGECKO_API_KEY not set')

    start, end = get_time_window(timestamp, TimeRange(API_TIME_RANGE))

    start = apply_min_date(start, API_MIN_DAYS)
    end = apply_min_date(end, API_MIN_DAYS)

    if not (start <= timestamp <= end):
        logger.info(
            f'Skpping price lookup for {coin_id}: timestamp {timestamp} '
            f'outside allowed window {start} + {end}'
        )
        return []

    try:
        url = COINGECKO_URL.format(id=coin_id)

        headers = {'x-cg-pro-api-key': COINGECKO_API_KEY}
        params = {
            'vs_currency': BASE_CURRENCY,
            'from': to_iso_minute(start),
            'to': to_iso_minute(end),
            'interval': API_INTERVAL,
        }

        logger.debug(
            f'Requesting price range for {coin_id} '
            f'from {params['from']} to {params['to']} with interval {API_INTERVAL}'
        )

        response = requests.get(url, params=params)
        response.raise_for_status()

        if not response.json():
            raise ValueError(f'No price data returned for {coin_id} at {timestamp}')

        return response.json()
    except Exception as e:
        logger.warning(
            f'Price lookup failed for {coin_id} at {timestamp}: {e}'
        )
        return []


def get_usd_price_at_time(symbol: str, timestamp: datetime) -> float:
    coin_id = COIN_ID_CACHE.lookup(symbol)
    price = PRICE_CACHE.lookup(coin_id, timestamp)
    if price is None:
        price_points = get_usd_price_in_range(coin_id, timestamp)
        merged = merge_price_volume(price_points)
        PRICE_CACHE.store_points(coin_id, merged)
        price = PRICE_CACHE.lookup(coin_id, timestamp)

    return price


def merge_price_volume(data: dict) -> list[dict]:
    if not data or not isinstance(data, dict):
        return []

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
            selected = entries[int(choice)]
            logger.info(f'Duplicate Coin ID: Selected {selected['coin_id']} for {selected['name']}')
            return selected['coin_id']
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

    logger.info(f'Found {len(symbols)} unique symbols.')
    return symbols


def add_price_to_transactions(transactions: list[Transaction]):
    logger.info(f'Adding pricing data to {len(transactions)} transactions.')
    for idx, tx in enumerate(transactions):
        logger.debug(f'[{idx}] Processing transaction with timestamp {tx.timestamp}')
        if tx.received_currency:
            logger.debug(f'[{idx}] received_currency {tx.received_currency}')
            tx.received_usd_cost_basis = get_usd_price_at_time(tx.received_currency, tx.timestamp)
        if tx.sent_currency:
            logger.debug(f'[{idx}] sent_currency {tx.sent_currency}')
            tx.sent_usd_cost_basis = get_usd_price_at_time(tx.sent_currency, tx.timestamp)
        if tx.fee_currency:
            logger.debug(f'[{idx}] fee_currency {tx.fee_currency}')
            tx.fee_usd_cost_basis = get_usd_price_at_time(tx.fee_currency, tx.timestamp)

    logger.debug(f'[{idx}] Computing realized return')
    compute_realized_return(tx)


def compute_realized_return(tx: Transaction):
    if tx.sent_usd_cost_basis is not None and tx.received_usd_cost_basis is not None:
        tx.realized_return = tx.received_usd_cost_basis - tx.sent_usd_cost_basis

    if tx.fee_usd_cost_basis is not None:
        tx.fee_realized_return -= tx.fee_usd_cost_basis