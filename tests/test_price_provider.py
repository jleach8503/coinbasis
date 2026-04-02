import unittest
from unittest.mock import patch, MagicMock

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


@patch('coinbasis.price_provider.COIN_ID_CACHE.lookup', return_value='atom')
@patch('coinbasis.price_provider.PRICE_CACHE')
@patch('coinbasis.price_provider.get_usd_price_in_range')
class TestGetUsdPriceInRange(unittest.TestCase):
    def test_recursive_fetch(self, mock_range, mock_cache, mock_coin_id):
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

        price = price_provider.get_usd_price_at_time('atom', ts)

        self.assertEqual(price, 10.5)
        mock_range.assert_called_once()
        mock_cache.store_points.assert_called_once()
        self.assertEqual(mock_cache.lookup.call_count, 2)

    def test_empty_provider_response_raises(self, mock_range, mock_cache, mock_coin_id):
        ts = price_provider.datetime(2024, 1, 1, 12, 0)

        mock_cache.lookup.return_value = None
        mock_range.side_effect = ValueError('No price data returned')

        with self.assertRaises(ValueError):
            price_provider.get_usd_price_at_time('atom', ts)

    def test_store_points_receives_merged_data(self, mock_range, mock_cache, mock_coin_id):
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

    def test_lookup_normalization(self, mock_range, mock_cache, mock_coin_id):
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
    def test_merge_called(self, mock_merge, mock_range, mock_cache, mock_coin_id):
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


class TestGetUniqueSymbols(unittest.TestCase):
    def test_extracts_all_three_currency_fields(self):
        txs = [
            price_provider.Transaction(
                timestamp='2024-01-01',
                type='trade',
                transaction_id='1',
                received_currency='ATOM',
                sent_currency='BTC',
                fee_currency='ETH',
            )
        ]

        symbols = price_provider.get_unique_symbols(txs)
        self.assertEqual(symbols, {'atom', 'btc', 'eth'})

    def test_ignores_none_values(self):
        txs = [
            price_provider.Transaction(
                timestamp='2024-01-01',
                type='trade',
                transaction_id='1',
                received_currency=None,
                sent_currency='BTC',
                fee_currency=None,
            )
        ]

        symbols = price_provider.get_unique_symbols(txs)
        self.assertEqual(symbols, {'btc'})

    def test_excludes_base_currency(self):
        txs = [
            price_provider.Transaction(
                timestamp='2024-01-01',
                type='trade',
                transaction_id='1',
                received_currency='USD',
                sent_currency='BTC',
                fee_currency='usd',
            )
        ]

        symbols = price_provider.get_unique_symbols(txs)
        self.assertEqual(symbols, {'btc'})  # USD excluded

    def test_lowercases_all_symbols(self):
        txs = [
            price_provider.Transaction(
                timestamp='2024-01-01',
                type='trade',
                transaction_id='1',
                received_currency='AtOm',
                sent_currency='bTc',
                fee_currency='Eth',
            )
        ]

        symbols = price_provider.get_unique_symbols(txs)
        self.assertEqual(symbols, {'atom', 'btc', 'eth'})

    def test_deduplicates_symbols(self):
        txs = [
            price_provider.Transaction(
                timestamp='2024-01-01',
                type='trade',
                transaction_id='1',
                received_currency='ATOM',
                sent_currency='atom',
                fee_currency='ATOM',
            )
        ]

        symbols = price_provider.get_unique_symbols(txs)
        self.assertEqual(symbols, {'atom'})

    def test_multiple_transactions(self):
        txs = [
            price_provider.Transaction(
                timestamp='2024-01-01',
                type='trade',
                transaction_id='1',
                received_currency='ATOM',
                sent_currency='BTC',
                fee_currency=None,
            ),
            price_provider.Transaction(
                timestamp='2024-01-02',
                type='trade',
                transaction_id='2',
                received_currency='ETH',
                sent_currency='BTC',
                fee_currency='ATOM',
            ),
        ]

        symbols = price_provider.get_unique_symbols(txs)
        self.assertEqual(symbols, {'atom', 'btc', 'eth'})


class TestResolveSymbolInteractively(unittest.TestCase):
    def setUp(self):
        self.entries = [
            {'coin_id': 'cosmos', 'name': 'Cosmos Hub'},
            {'coin_id': 'cosmos-2', 'name': 'Cosmos Legacy'},
        ]

    @patch('builtins.input', return_value='0')
    def test_select_first_entry(self, mock_input):
        result = price_provider.resolve_symbol_interactively('ATOM', self.entries)
        self.assertEqual(result, 'cosmos')

    @patch('builtins.input', return_value='1')
    def test_select_second_entry(self, mock_input):
        result = price_provider.resolve_symbol_interactively('ATOM', self.entries)
        self.assertEqual(result, 'cosmos-2')

    @patch('builtins.input', side_effect=['x', '5', '-1', '1'])
    def test_invalid_then_valid_selection(self, mock_input):
        result = price_provider.resolve_symbol_interactively('ATOM', self.entries)
        self.assertEqual(result, 'cosmos-2')

    @patch('builtins.input', side_effect=['', 'abc', '0'])
    def test_empty_and_non_digit_then_valid(self, mock_input):
        result = price_provider.resolve_symbol_interactively('ATOM', self.entries)
        self.assertEqual(result, 'cosmos')

    @patch('builtins.input', return_value='0')
    @patch('builtins.print')
    def test_prints_menu(self, mock_print, mock_input):
        price_provider.resolve_symbol_interactively('ATOM', self.entries)

        mock_print.assert_any_call('\nMultiple coin IDs found for symbol: ATOM')

        mock_print.assert_any_call('[0] cosmos               - Cosmos Hub')
        mock_print.assert_any_call('[1] cosmos-2             - Cosmos Legacy')


class TestResolveAllSymbols(unittest.TestCase):
    def setUp(self):
        self.coin_map = MagicMock(spec=price_provider.CoinMapCache)

    def test_lookup_success(self):
        self.coin_map.lookup.return_value = 'bitcoin'

        result = price_provider.resolve_all_symbols(['btc'], self.coin_map)

        self.coin_map.lookup.assert_called_once_with('btc')
        self.assertEqual(result, None)  # function currently returns nothing

    @patch('coinbasis.price_provider.resolve_symbol_interactively', return_value='cosmos')
    def test_multiple_coins_flow(self, mock_interactive):
        self.coin_map.lookup.side_effect = price_provider.MultipleCoinsError()
        self.coin_map.list_duplicates.return_value = [
            {'coin_id': 'cosmos', 'name': 'Cosmos Hub'},
            {'coin_id': 'cosmos-2', 'name': 'Cosmos Legacy'},
        ]
        self.coin_map.prune = MagicMock()

        price_provider.resolve_all_symbols(['atom'], self.coin_map)

        self.coin_map.lookup.assert_called_once_with('atom')
        self.coin_map.list_duplicates.assert_called_once_with('atom')
        mock_interactive.assert_called_once()
        self.coin_map.prune.assert_called_once_with('atom', 'cosmos')

    def test_coin_not_found_raises(self):
        self.coin_map.lookup.side_effect = price_provider.CoinNotFoundError()

        with self.assertRaises(price_provider.CoinNotFoundError):
            price_provider.resolve_all_symbols(['unknown'], self.coin_map)