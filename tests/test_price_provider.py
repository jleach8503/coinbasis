import unittest
from unittest.mock import patch

import coinbasis.price_provider as price_provider


@patch('coinbasis.price_provider.get_usd_price_at_time')
class TestGetUsdPriceAtTime(unittest.TestCase):
    def test_get_usd_price_at_time(self, mock_price):
        mock_price.return_value = 10.0

        result = price_provider.get_usd_price_at_time('ATOM', '2024-01-01-T00:00:00')
        self.assertEqual(result, 10.0)

    def test_called_with_correct_arguments(self, mock_price):
        mock_price.return_value = 10.0

        price_provider.get_usd_price_at_time('ATOM', '2024-01-01T00:00:00')
        mock_price.assert_called_once_with('ATOM', '2024-01-01T00:00:00')

    def test_exception_propagates(self, mock_price):
        mock_price.side_effect = RuntimeError('API failure')

        with self.assertRaises(RuntimeError):
            price_provider.get_usd_price_at_time('ATOM', '2024-01-01T00:00:00')

    def test_multiple_calls(self, mock_price):
        mock_price.side_effect = [10.0, 12.5]

        p1 = price_provider.get_usd_price_at_time('ATOM', '2024-01-01T00:00:00')
        p2 = price_provider.get_usd_price_at_time('ATOM', '2024-01-02T00:00:00')

        self.assertEqual(p1, 10.0)
        self.assertEqual(p2, 12.5)

    def test_invalid_symbol(self, mock_price):
        mock_price.side_effect = ValueError('Unknown symbol')

        with self.assertRaises(ValueError):
            price_provider.get_usd_price_at_time('FAKECOIN', '2024-01-01T00:00:00')

