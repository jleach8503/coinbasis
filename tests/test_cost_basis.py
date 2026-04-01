import unittest
from unittest.mock import patch

from coinbasis.cost_basis import (
    compute_income_cost_basis,
    Transaction,
)


@patch('coinbasis.cost_basis.get_usd_price_at_time')
class TestComputeIncomeCostBasis(unittest.TestCase):
    def test_income_cost_basis(self, mock_price):
        mock_price.return_value = 10.0

        tx = Transaction(
            timestamp='2024-01-01',
            type='STAKING_REWARD',
            transaction_id='12345',
            received_qty=2.0,
            received_currency='ATOM',
        )

        compute_income_cost_basis(tx)

        self.assertEqual(tx.received_usd_cost_basis, 20.0)
        self.assertEqual(tx.realized_return, 20.0)