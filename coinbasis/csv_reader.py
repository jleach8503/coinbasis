import csv
from typing import get_args
from coinbasis.models import Transaction, COLUMN_MAP


def parse_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped or stripped == '...':
        return None
    return float(stripped)


def parse_string(value: str) -> str | None:
    stripped = value.strip()
    if not stripped or stripped == '...':
        return None
    return str(stripped)


def get_field_parser(field_name: str):
    field_type = Transaction.__dataclass_fields__[field_name].type
    args = get_args(field_type)

    if field_type is float or float in args:
        return parse_float

    return parse_string

def parse_row(row: dict) -> dict:
    parsed = {}
    for col, value in row.items():
        if col not in COLUMN_MAP:
            continue
        field_name = COLUMN_MAP[col]
        parser = get_field_parser(field_name)
        parsed[field_name] = parser(value)

    return parsed


def parse_csv(path: str) -> list[Transaction]:
    transactions = []
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            transactions.append(Transaction(**parse_row(row)))

    return transactions