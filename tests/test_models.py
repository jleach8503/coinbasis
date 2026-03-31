import unittest
from dataclasses import fields

from coinbasis.models import (
    Transaction,
    COLUMN_MAP,
)


class TestTransactionModel(unittest.TestCase):
    def test_column_map_matches_transaction_fields(self):
        dataclass_fields = {f.name for f in fields(Transaction)}
        mapped_fields = set(COLUMN_MAP.values())

        # Ensure every mapped field exists in the dataclass
        self.assertTrue(
            mapped_fields.issubset(dataclass_fields),
            f'COLUMN_MAP contains fields not in Transaction: {mapped_fields - dataclass_fields}',
        )

        unmapped = dataclass_fields - mapped_fields
        self.assertEqual(
            unmapped,
            set(),
            f'Transaction fields missing from COLUMN_MAP: {unmapped}',
        )