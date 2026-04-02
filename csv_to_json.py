import csv
import json
from pathlib import Path
import argparse


def csv_to_json(csv_path: Path) -> None:
    grouped = {}

    with csv_path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row['symbol'].strip().lower()
            entry = {
                'coin_id': row['coin_id'].strip(),
                'name': row['name'].strip(),
            }
            grouped.setdefault(symbol, []).append(entry)

    json_path = csv_path.with_suffix('.json')
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(grouped, f, indent=2)

    print(f'Converted {csv_path} -> {json_path}')

def main():
    parser = argparse.ArgumentParser(description='Convert CSV to JSON with same basename.')
    parser.add_argument('csv_file', help='Path to the CSV file')
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    csv_to_json(csv_path)

if __name__ == '__main__':
    main()