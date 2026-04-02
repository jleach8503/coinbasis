import json
import os
from typing import Optional

from coinbasis.utils.time import (
    TimeInterval,
    datetime,
    to_iso_minute,
    normalize_timestamp,
    get_time_window,
)


class PriceCache:
    def __init__(self, path: str, interval: TimeInterval = TimeInterval('daily')):
        self.path = path
        self.interval = interval
        self.data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, 'r') as f:
            return json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def lookup(self, symbol: str, timestamp: datetime) -> Optional[float]:
        data_points = self.lookup_range(symbol, timestamp)
        if not data_points:
            return None
        if len(data_points) == 1:
            return data_points[0]['price']

        normalized = normalize_timestamp(timestamp)
        def distance(dp):
            return abs(dp['timestamp'] - normalized)

        closest = min(data_points, key=distance)
        return closest['price']

    def lookup_range(self, symbol: str, timestamp: datetime) -> list[dict]:
        start, end = (to_iso_minute(t) for t in get_time_window(timestamp, self.interval))
        symbol_data = self.data.get(symbol, {})

        results = []
        for time, entry in symbol_data.items():
            if start <= time <= end:
                results.append({
                    'timestamp': time,
                    'price': entry['price'],
                    'volume': entry['volume'],
                })
        return results

    def store_points(self, symbol: str, points: list[tuple[datetime, float, float]]):
        if symbol not in self.data:
            self.data[symbol] = {}

        for timestamp, price, volume in points:
            iso = to_iso_minute(timestamp)
            self.data[symbol][iso] = {
                'price': price,
                'volume': volume,
            }

        self.save()


class CoinMapCache:
    def __init__(self, path: str):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def lookup(self, symbol: str) -> str:
        symbol = symbol.lower()
        entries = self.data.get(symbol)

        if not entries:
            raise ValueError(f'No coin_id found for symbol: {symbol}')

        if len(entries) > 1:
            raise ValueError(f'Multiple coin_id entries for symbol: {symbol}')

        return entries[0]['coin_id']

    def list_duplicates(self, symbol: str) -> list[dict]:
        return self.data.get(symbol.lower(), [])

    def prune(self, symbol: str, keep_coin_id: str):
        symbol = symbol.lower()
        entries = self.data.get(symbol, [])

        self.data[symbol] = [
            e for e in entries if e['coin_id'] == keep_coin_id
        ]

        self.save()