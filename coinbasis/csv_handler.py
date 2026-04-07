import csv
import logging
from typing import get_args
from coinbasis.models import (
    Transaction,
    datetime,
    COLUMN_MAP,
    USD_FIELDS,
)
from datetime import timezone


REVERSED_COLUMN_MAP = {value: key for key, value in COLUMN_MAP.items()}
logger = logging.getLogger(__name__)

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


def parse_timestamp(value: str) -> datetime:
    stripped = value.strip()
    try:
        dt = datetime.strptime(stripped, '%m/%d/%Y %H:%M:%S')
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass

    try:
        dt = datetime.fromisoformat(stripped.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    logger.error(f'Unrecognized timestamp format: {stripped}')
    raise ValueError(f'Unrecognized timestamp format: {stripped}')


def get_field_parser(field_name: str):
    field_type = Transaction.__dataclass_fields__[field_name].type
    args = get_args(field_type)

    if field_type is float or float in args:
        return parse_float
    if field_type is datetime:
        return parse_timestamp

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
    logger.info(f'Parsing CSV file: {path}')
    transactions = []
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            transactions.append(Transaction(**parse_row(row)))

    logger.info(f'Transaction Count: {len(transactions)}')
    return transactions


def transaction_to_row(tx: Transaction) -> dict[str, str]:
    row = {}
    for field_name, col in REVERSED_COLUMN_MAP.items():
        value = getattr(tx, field_name)

        # Force 2-decimal formatting for USD fields
        if field_name in USD_FIELDS and value is not None:
            row[col] = f'{value:2f}'
            continue

        row[col] = '' if value is None else str(value)
    return row


def write_csv(path: str, transactions: list[Transaction]):
    logger.info(f'Writing {len(transactions)} transactions to CSV file: {path}')
    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(COLUMN_MAP.keys()))
        writer.writeheader()
        for tx in transactions:
            writer.writerow(transaction_to_row(tx))
