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


@patch('coinbasis.price_provider.PRICE_CACHE')
@patch('coinbasis.price_provider.get_usd_price_in_range')
class TestGetUsdPriceInRange(unittest.TestCase):
    def test_recursive_fetch(self, mock_range, mock_cache):
        ts = price_provider.datetime(2024, 1, 1, 12, 0)
        mock_cache.lookup.side_effect = [None, 10.5]

        # Provider returns raw data
        mock_range.return_value = {
            'prices': [
                [1700000000000, 10.5]
            ],
            'total_volumes': [
                [1700000000000, 12345.0]
            ],
        }

        price = price_provider.get_usd_price_at_time('atom', ts)

        self.assertEqual(price, 10.5)
        mock_range.assert_called_once()
        mock_cache.store_points.assert_called_once()
        self.assertEqual(mock_cache.lookup.call_count, 2)

    def test_empty_provider_response_raises(self, mock_range, mock_cache):
        ts = price_provider.datetime(2024, 1, 1, 12, 0)

        mock_cache.lookup.return_value = None
        mock_range.side_effect = ValueError('No price data returned')

        with self.assertRaises(ValueError):
            price_provider.get_usd_price_at_time('atom', ts)

    def test_store_points_receives_merged_data(self, mock_range, mock_cache):
        ts = price_provider.datetime(2024, 1, 1, 12, 0)

        mock_cache.lookup.side_effect = [None, 10.5]
        mock_range.return_value = {
            'prices': [
                [1700000000000, 10.5]
            ],
            'total_volumes': [
                [1700000000000, 12345.0]
            ],
        }

        price_provider.get_usd_price_at_time('atom', ts)

        args, _ = mock_cache.store_points.call_args
        symbol, points = args

        self.assertEqual(symbol, 'atom')
        self.assertEqual(len(points), 1)

        dt, price, volume = points[0]
        self.assertEqual(price, 10.5)
        self.assertEqual(volume, 12345.0)

    def test_lookup_normalization(self, mock_range, mock_cache):
        naive = price_provider.datetime(2024, 1, 1, 12, 0)
        aware = naive.replace(tzinfo=price_provider.timezone.utc)

        mock_cache.lookup.side_effect = [None, 10.5]
        mock_range.return_value = {
            'prices': [
                [1700000000000, 10.5]
            ],
            'total_volumes': [
                [1700000000000, 12345.0]
            ],
        }

        price_provider.get_usd_price_at_time('atom', naive)

        called_ts = mock_cache.lookup.call_args_list[0][0][1]
        self.assertEqual(called_ts.tzinfo, None)

    @patch('coinbasis.price_provider.merge_price_volume')
    def test_merge_called(self, mock_merge, mock_range, mock_cache):
        ts = price_provider.datetime(2024, 1, 1, 12, 0)

        mock_cache.lookup.side_effect = [None, 10.5]
        mock_range.return_value = {'prices': [], 'total_volumes': []}
        mock_merge.return_value = [(ts, 10.5, 100)]

        price_provider.get_usd_price_at_time('atom', ts)
        mock_merge.assert_called_once_with(mock_range.return_value)


class TestMergePriceVolume(unittest.TestCase):
    def test_basic_merge(self):
        data = {
            'prices': [
                [1700000000000, 10.5]
            ],
            'total_volumes': [
                [1700000000000, 12345.0]
            ]
        }

        result = price_provider.merge_price_volume(data)

        self.assertEqual(len(result), 1)
        dt, price, volume = result[0]

        self.assertEqual(price, 10.5)
        self.assertEqual(volume, 12345.0)
        self.assertEqual(
            dt,
            price_provider.datetime.fromtimestamp(1700000000000 / 1000, tz=price_provider.timezone.utc)
        )

    def test_missing_volume_defaults_to_zero(self):
        data = {
            'prices': [
                [1700000000000, 10.5]
            ],
            'total_volumes': []
        }

        result = price_provider.merge_price_volume(data)

        self.assertEqual(len(result), 1)
        _, price, volume = result[0]

        self.assertEqual(price, 10.5)
        self.assertEqual(volume, 0.0)

    def test_multiple_points(self):
        data = {
            'prices': [
                [1700000000000, 10.5],
                [1700003600000, 11.0],
            ],
            'total_volumes': [
                [1700000000000, 100.0],
                [1700003600000, 200.0],
            ]
        }

        result = price_provider.merge_price_volume(data)

        self.assertEqual(len(result), 2)

        dt1, price1, vol1 = result[0]
        self.assertEqual(price1, 10.5)
        self.assertEqual(vol1, 100.0)

        dt2, price2, vol2 = result[1]
        self.assertEqual(price2, 11.0)
        self.assertEqual(vol2, 200.0)

    def test_ignores_extra_volume_entries(self):
        data = {
            'prices': [
                [1700000000000, 10.5]
            ],
            'total_volumes': [
                [1700000000000, 12345.0],
                [1700003600000, 99999.0],  # extra volume entry
            ]
        }

        result = price_provider.merge_price_volume(data)

        self.assertEqual(len(result), 1)
        _, _, volume = result[0]
        self.assertEqual(volume, 12345.0)

    def test_empty_input(self):
        data = {
            'prices': [],
            'total_volumes': []
        }

        result = price_provider.merge_price_volume(data)
        self.assertEqual(result, [])