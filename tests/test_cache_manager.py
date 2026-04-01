import unittest
import tempfile
import os
from datetime import datetime, timezone

from coinbasis.cache_manager import PriceCache
from coinbasis.utils.time import to_iso_minute


class TestPriceCache(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.tempdir.name, "cache.json")
        self.cache = PriceCache(self.cache_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_initializes_empty_when_file_missing(self):
        self.assertEqual(self.cache.data, {})

    def test_store_and_lookup(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        points = [(ts, 10.5, 12345.0)]

        self.cache.store_points("ATOM", points)

        result = self.cache.lookup("ATOM", ts)
        self.assertEqual(result, 10.5)

    def test_lookup_missing_returns_none(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.assertIsNone(self.cache.lookup("ATOM", ts))

    def test_file_written_after_store(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        points = [(ts, 10.5, 12345.0)]

        self.cache.store_points("ATOM", points)

        self.assertTrue(os.path.exists(self.cache_path))

    def test_multiple_symbols(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        self.cache.store_points("ATOM", [(ts, 10.5, 100)])
        self.cache.store_points("BTC", [(ts, 42000.0, 200)])

        self.assertEqual(self.cache.lookup("ATOM", ts), 10.5)
        self.assertEqual(self.cache.lookup("BTC", ts), 42000.0)

    def test_timestamp_normalization(self):
        # naive timestamp should be normalized to UTC
        naive = datetime(2024, 1, 1, 12, 0)
        aware = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

        self.cache.store_points("ATOM", [(aware, 10.5, 100)])

        result = self.cache.lookup("ATOM", naive)
        self.assertEqual(result, 10.5)
