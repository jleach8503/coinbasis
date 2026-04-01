from coinbasis.csv_handler import parse_csv
from coinbasis.price_provider import get_usd_price_at_time, datetime

CSV_PATH = 'C:/Repositories/Coinbasis/input/2025 Transactions.csv'

def main ():
    #transactions = parse_csv(CSV_PATH)
    #print(f'Transaction Count: {len(transactions)}')

    timestamp = datetime(2025, 12, 30, 21, 44)
    coin = 'ADA'
    price = get_usd_price_at_time(coin, timestamp)
    print(f'Price of {coin} on {timestamp} was {price}')


if __name__ == "__main__":
    main()