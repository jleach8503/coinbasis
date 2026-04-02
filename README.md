# CoinBasis - A CoinTracker Cost Basis Assistant

This project is designed to calculate the cost basis of transaction exports from the CoinTracker website.  The initial scope of the project is to only populate values for taxable events that qualify as income but may later be expanded to support more complex transaction types.

## Features

### Provider-Agnostic Price Caching

The project implements price caching to reduce the quantity and rate of API calls to the price provider.

- All prices are stored in a unified JSON cache keyed by a provider-independent `coin_id` identifier.
- Timestamps are normalized to UTC with supported intervals (`min`, `hour`, `day`).
- Switching providers does not invalidate the existing price cache.

### CoinGecko Provider Support

CoinGecko API (Demo and Pro) is currently supported for API calls to retrieve price history.

- Prices are retrieved using the `/market_chart/range` API endpoint with the configured range of data points.
- The configured time intervals allow configurable granularity on pricing history.
- Automatic merging of price/volume pairs.

### Coin ID Caching

A JSON-based cache of currency symbol to `coin_id` is used to ensure all price retrievals do not require additional API calls to retrieve `coin_id`.  A conversion utility is provided in the root of the repository to convert a CSV (symbol, coin_id, name) file into the required JSON format.

```powershell
python .\csv_to_json.py .\data\providers\coingecko.csv
```

## Usage

### Configuration

Prior to running, a `config.py` file should be created and populated like in the example below:

```python
BASE_CURRENCY = 'usd'
API_INTERVAL = 'daily'
API_TIME_RANGE = 'year'

COINGECKO_API_KEY = ''
COINGECKO_URL = 'https://api.coingecko.com/api/v3/coins/{id}/market_chart/range'
COINGECKO_COIN_MAP = 'data/providers/coingecko.json'

CACHE_PATH = 'data/cache/prices.json'
```

| Variable | Description |
|----------|-------------|
| `BASE_CURRENCY` | Sets the base currency for cost-basis conversions. (`usd`) |
| `API_INTERVAL` | Sets the interval size for price retrieval (`5m`,`hourly`,`daily`) |
| `API_TIME_RANGE` | Sets the price retrieval window for non-cached price lookups (`day`,`week`,`month`,`year`)  |
| `COINGECKO_API_KEY` | Sets the API key to be used with the CoinGecko provider |
| `COINGECKO_URL` | Sets the API endpoint to be used with the CoinGecko provider |
| `COINGECKO_COIN_MAP` | Sets the relative path to the local JSON coin ID cache |
| `CACHE_PATH` | Sets the relative path to the local JSON price cache |

### Execution

The easiest way to run the project on Windows is by running the provided scripts in the root of the repository.

```powershell
# Test the project, including the required config.py file
.\test.ps1

# Run CoinBasis
.\run.ps1
```