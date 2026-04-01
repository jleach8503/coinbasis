import json
import os
from typing import Optional

from coinbasis.utils.time import (
    datetime,
    to_iso_minute,
    normalize_timestamp,
)


class PriceCache:
    def __init__(self, path: str):
        self.path = path
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
        iso = to_iso_minute(normalize_timestamp(timestamp))
        return self.data.get(symbol, {}).get(iso, {}).get('price')

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