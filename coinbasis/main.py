from coinbasis.csv_handler import parse_csv

CSV_PATH = 'C:/Repositories/Coinbasis/input/2025 Transactions.csv'

def main ():
    transactions = parse_csv(CSV_PATH)
    print(f'Transaction Count: {len(transactions)}')


if __name__ == "__main__":
    main()