import logging
import os

from coinbasis.csv_handler import (
    parse_csv,
    write_csv,
    csv,
)
from coinbasis.price_provider import (
    datetime,
    timezone,
    COIN_ID_CACHE,
    PRICE_CACHE,
    resolve_all_symbols,
    get_unique_symbols,
    add_price_to_transactions,
)

CSV_PATH = 'C:/Repositories/Coinbasis/input/2025 Transactions.csv'
logger = logging.getLogger(__name__)

def setup_logging():
    log_dir = os.path.join('data','logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    log_path = os.path.join(log_dir, f'CoinBasis_{timestamp}.log')

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.getLogger(__name__).info(f'Logging intialized -> {log_path}')


def load_historical_prices_from_csv(coin_id: str, csv_path: str):
    '''
    Load historical price data from a CoinGecko CSV export and store it
    into the PRICE_CACHE under the given coin_id.
    '''
    points = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            ts_str = row['snapped_at'].strip()
            price_str = row['price'].strip()
            vol_str = row['total_volume'].strip()

            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S %Z')
            dt = dt.replace(tzinfo=timezone.utc)

            price = float(price_str)
            volume = float(vol_str)

            points.append((dt, price, volume))

    PRICE_CACHE.store_points(coin_id, points)

    logger.info(
        f'Loaded {len(points)} historical price points for {coin_id} '
        f'from {csv_path}'
    )


def prompt_import_historical_prices(symbols: set[str]):
    '''
    Interactive menu allowing the user to import historical price CSVs
    for any resolved symbol. User can import multiple files, one at a time,
    until selecting 0 to continue.
    '''
    print('\n=== Historical Price Import ===')

    indexed = []
    for i, sym in enumerate(sorted(symbols), start=1):
        coin_id = COIN_ID_CACHE.lookup(sym)
        indexed.append((i, sym, coin_id))

    print('Resolved symbols:')
    for i, sym, coin_id in indexed:
        print(f'  {i}. {sym}  (coin_id: {coin_id})')
    print('  0. Continue without importing')

    while True:
        choice = input('\nSelect a number to import historical prices (0 to continue): ').strip()
        if not choice.isdigit():
            print('Please enter a valid number.')
            continue

        choice = int(choice)

        if choice == 0:
            print('Continuing without further imports.')
            return

        if not (1 <= choice <= len(indexed)):
            print('Invalid selection. Try again.')
            continue

        _, sym, coin_id = indexed[choice - 1]
        csv_path = input(f'Enter CSV path for {sym} (or press Enter to cancel): ').strip()
        if not csv_path:
            print(f'Skipping {sym}.')
            continue

        if not os.path.exists(csv_path):
            print(f'File not found: {csv_path}. Skipping.')
            continue

        load_historical_prices_from_csv(coin_id, csv_path)
        logger.info(f'Imported historical prices for {sym}.')


def main ():
    setup_logging()

    transactions = parse_csv(CSV_PATH)
    unique_symbols = get_unique_symbols(transactions)
    resolve_all_symbols(unique_symbols, COIN_ID_CACHE)
    prompt_import_historical_prices(unique_symbols)
    add_price_to_transactions(transactions)

    output_path = 'input/enriched_transactions.csv'
    write_csv(output_path, transactions)

    logger.info('CoinBasis calculations complete.')


if __name__ == '__main__':
    main()