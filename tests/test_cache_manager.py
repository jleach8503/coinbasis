import unittest
import tempfile
import os
import json
from datetime import datetime, timezone

from coinbasis.cache_manager import PriceCache, CoinMapCache


class TestPriceCache(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.tempdir.name, 'cache.json')
        self.cache = PriceCache(self.cache_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_initializes_empty_when_file_missing(self):
        self.assertEqual(self.cache.data, {})

    def test_store_and_lookup(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        points = [(ts, 10.5, 12345.0)]

        self.cache.store_points('ATOM', points)

        result = self.cache.lookup('ATOM', ts)
        self.assertEqual(result, 10.5)

    def test_lookup_missing_returns_none(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.assertIsNone(self.cache.lookup('ATOM', ts))

    def test_file_written_after_store(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        points = [(ts, 10.5, 12345.0)]

        self.cache.store_points('ATOM', points)

        self.assertTrue(os.path.exists(self.cache_path))

    def test_multiple_symbols(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        self.cache.store_points('ATOM', [(ts, 10.5, 100)])
        self.cache.store_points('BTC', [(ts, 42000.0, 200)])

        self.assertEqual(self.cache.lookup('ATOM', ts), 10.5)
        self.assertEqual(self.cache.lookup('BTC', ts), 42000.0)

    def test_timestamp_normalization(self):
        # naive timestamp should be normalized to UTC
        naive = datetime(2024, 1, 1, 12, 0)
        aware = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        self.cache.store_points('ATOM', [(aware, 10.5, 100)])

        result = self.cache.lookup('ATOM', naive)
        self.assertEqual(result, 10.5)


class TestCoinMapCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.temp_dir.name, 'coin_ids.json')

        data = {
            'btc': [
                {'coin_id': 'bitcoin', 'name': 'Bitcoin'}
            ],
            'ada': [
                {'coin_id': 'cardano', 'name': 'Cardano'},
                {'coin_id': 'cardano-2', 'name': 'Cardano (old)'}
            ],
            'eth': [
                {'coin_id': 'ethereum', 'name': 'Ethereum'}
            ]
        }

        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self.cache = CoinMapCache(self.json_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lookup_single(self):
        coin_id = self.cache.lookup('btc')
        self.assertEqual(coin_id, 'bitcoin')

    def test_lookup_missing(self):
        with self.assertRaises(ValueError):
            self.cache.lookup('doge')

    def test_lookup_duplicates(self):
        with self.assertRaises(ValueError):
            self.cache.lookup('ada')

    def test_list_duplicates(self):
        dupes = self.cache.list_duplicates('ada')
        self.assertEqual(len(dupes), 2)
        self.assertEqual(dupes[0]['coin_id'], 'cardano')
        self.assertEqual(dupes[1]['coin_id'], 'cardano-2')

    def test_prune_duplicates(self):
        self.cache.prune('ada', 'cardano')
        nodupes = self.cache.list_duplicates('ada')
        self.assertEqual(len(nodupes),1)

        cache2 = CoinMapCache(self.json_path)
        dupes = cache2.list_duplicates('ada')
        self.assertEqual(len(dupes),2)
        self.assertEqual(dupes[0]['coin_id'], 'cardano')


    def test_prune_nonexistent_symbol(self):
        self.cache.prune('doge', 'whatever')

        cache2 = CoinMapCache(self.json_path)
        self.assertIn('btc', cache2.data)
        self.assertIn('ada', cache2.data)
        self.assertIn('eth', cache2.data)