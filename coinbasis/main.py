import logging
import os

from coinbasis.csv_handler import parse_csv
from coinbasis.price_provider import (
    get_unique_symbols,
    get_usd_price_at_time,
    datetime,
    timezone,
    COIN_ID_CACHE,
    resolve_all_symbols,
)

CSV_PATH = 'C:/Repositories/Coinbasis/input/2025 Transactions.csv'

def setup_logging():
    log_dir = os.path.join('data','logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    log_path = os.path.join(log_dir, f'CoinBasis_{timestamp}.log')

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.getLogger(__name__).info(f'Logging intialized -> {log_path}')


def main ():
    setup_logging()

    print(f'Input File: {CSV_PATH}')
    transactions = parse_csv(CSV_PATH)
    print(f'Transaction Count: {len(transactions)}')

    unique_symbols = get_unique_symbols(transactions)
    print(f'Found {len(unique_symbols)} unique symbols.')
    resolve_all_symbols(unique_symbols, COIN_ID_CACHE)

    #timestamp = datetime(2026, 4, 2, 21, 44)
    #coin = 'ADA'
    #price = get_usd_price_at_time(coin, timestamp)
    #print(f'Price of {coin} on {timestamp} was {price}')


if __name__ == '__main__':
    main()