from coinbasis.csv_handler import parse_csv
from coinbasis.price_provider import (
    get_unique_symbols,
    get_usd_price_at_time,
    datetime,
    COIN_ID_CACHE,
    resolve_all_symbols,
)

CSV_PATH = 'C:/Repositories/Coinbasis/input/2025 Transactions.csv'


def main ():
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