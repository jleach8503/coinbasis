import unittest
import importlib
from coinbasis.utils.time import TimeInterval, TimeRange


class TestConfigModule(unittest.TestCase):
    def setUp(self):
        self.config = importlib.import_module('config')

    def test_required_variables_exist(self):
        required = [
            'BASE_CURRENCY',
            'API_INTERVAL',
            'API_TIME_RANGE',
            'COINGECKO_API_KEY',
            'COINGECKO_URL',
            'COINGECKO_COIN_MAP',
            'CACHE_PATH',
        ]

        for var in required:
            self.assertTrue(
                hasattr(self.config, var),
                f'Missing required config variable: {var}'
            )

    def test_variable_types(self):
        self.assertIsInstance(self.config.BASE_CURRENCY, str)
        self.assertIsInstance(self.config.API_INTERVAL, str)
        self.assertIsInstance(self.config.API_TIME_RANGE, str)
        self.assertIsInstance(self.config.COINGECKO_API_KEY, str)
        self.assertIsInstance(self.config.COINGECKO_URL, str)
        self.assertIsInstance(self.config.COINGECKO_COIN_MAP, str)
        self.assertIsInstance(self.config.CACHE_PATH, str)

    def test_interval_values(self):
        allowed = {item.value for item in TimeInterval}
        self.assertIn(
            self.config.API_INTERVAL,
            allowed,
            f'API_INTERVAL must be one of {allowed}'
        )

    def test_time_range_values(self):
        allowed = {item.value for item in TimeRange}
        self.assertIn(
            self.config.API_TIME_RANGE,
            allowed,
            f'API_TIME_RANGE must be one of {allowed}'
        )

    def test_url_format(self):
        self.assertTrue(
            '{id}' in self.config.COINGECKO_URL,
            'COINGECKO_URL must contain "{id}" placeholder'
        )

    def test_coin_map_path_is_string(self):
        path = self.config.COINGECKO_COIN_MAP
        self.assertIsInstance(path, str)
        self.assertTrue(len(path) > 0)

    def test_cache_path_is_string(self):
        path = self.config.CACHE_PATH
        self.assertIsInstance(path, str)
        self.assertTrue(len(path) > 0)
