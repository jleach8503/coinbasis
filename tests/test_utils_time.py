import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from coinbasis.utils.time import (
    get_time_window,
    TimeRange,
    TimeInterval,
    normalize_timestamp,
    to_iso_minute,
    apply_min_date,
)


class TestGetTimeWindow(unittest.TestCase):
    def test_min_interval(self):
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeInterval.MIN)

        self.assertEqual(start, datetime(2024, 1, 17, 12, 30, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc))

    def test_hour_interval(self):
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeInterval.HOUR)

        self.assertEqual(start, datetime(2024, 1, 17, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 1, 17, 12, 59, tzinfo=timezone.utc))

    def test_day_interval(self):
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeInterval.DAY)

        self.assertEqual(start, datetime(2024, 1, 17, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 1, 17, 23, 59, tzinfo=timezone.utc))

    def test_day_range(self):
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeRange.DAY)

        self.assertEqual(start, datetime(2024, 1, 17, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 1, 17, 23, 59, tzinfo=timezone.utc))

    def test_week_range(self):
        # Wednesday, Jan 17 2024 → week starts Monday Jan 15
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeRange.WEEK)

        self.assertEqual(start, datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 1, 21, 23, 59, tzinfo=timezone.utc))

    def test_month_range(self):
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeRange.MONTH)

        self.assertEqual(start, datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 1, 31, 23, 59, tzinfo=timezone.utc))

    def test_month_rollover(self):
        # December → January rollover
        ts = datetime(2024, 12, 15, 10, 0, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeRange.MONTH)

        self.assertEqual(start, datetime(2024, 12, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 12, 31, 23, 59, tzinfo=timezone.utc))

    def test_year_range(self):
        ts = datetime(2024, 6, 10, 8, 0, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeRange.YEAR)

        self.assertEqual(start, datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(end,   datetime(2024, 12, 31, 23, 59, tzinfo=timezone.utc))

    def test_naive_timestamp_converted_to_utc(self):
        ts = datetime(2024, 1, 17, 12, 34)  # naive
        start, end = get_time_window(ts, TimeRange.DAY)

        self.assertEqual(start.tzinfo, timezone.utc)
        self.assertEqual(end.tzinfo, timezone.utc)

    def test_end_is_one_minute_before_next_period(self):
        ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        start, end = get_time_window(ts, TimeRange.DAY)

        # Next day would be Jan 2 00:00 → minus 1 minute = Jan 1 23:59
        expected_end = datetime(2024, 1, 1, 23, 59, tzinfo=timezone.utc)
        self.assertEqual(end, expected_end)


class TestNormalizeTimestamp(unittest.TestCase):
    def test_naive_timestamp_becomes_utc(self):
        ts = datetime(2024, 1, 17, 12, 34, 56, 789000)
        result = normalize_timestamp(ts)

        self.assertEqual(result.tzinfo, timezone.utc)
        self.assertEqual(result, datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc))

    def test_aware_timestamp_converted_to_utc(self):
        # UTC+2
        ts = datetime(2024, 1, 17, 14, 34, tzinfo=timezone(timedelta(hours=2)))
        result = normalize_timestamp(ts)

        # Should convert to 12:34 UTC
        self.assertEqual(result, datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc))

    def test_seconds_and_microseconds_are_zeroed(self):
        ts = datetime(2024, 1, 17, 12, 34, 59, 999999, tzinfo=timezone.utc)
        result = normalize_timestamp(ts)

        self.assertEqual(result.second, 0)
        self.assertEqual(result.microsecond, 0)

    def test_idempotent(self):
        ts = datetime(2024, 1, 17, 12, 34, tzinfo=timezone.utc)
        result1 = normalize_timestamp(ts)
        result2 = normalize_timestamp(result1)

        self.assertEqual(result1, result2)

    def test_does_not_change_date_or_hour(self):
        ts = datetime(2024, 1, 17, 23, 59, 30, tzinfo=timezone.utc)
        result = normalize_timestamp(ts)

        self.assertEqual(result, datetime(2024, 1, 17, 23, 59, tzinfo=timezone.utc))


class TestToIsoMinute(unittest.TestCase):
    def test_to_iso_minute(self):
        dt = datetime(2024, 1, 1, 12, 34, 56, tzinfo=timezone.utc)
        self.assertEqual(to_iso_minute(dt), '2024-01-01T12:34')


class TestApplyMinDate(unittest.TestCase):
    @patch('coinbasis.utils.time.datetime')
    def test_clamps_to_min_date(self, mock_datetime):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        old_ts = now - timedelta(days=400)
        result = apply_min_date(old_ts, min_days=365)

        expected = now - timedelta(days=365)
        self.assertEqual(result, expected)

    @patch('coinbasis.utils.time.datetime')
    def test_does_not_clamp_if_timestamp_newer(self, mock_datetime):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        recent_ts = now - timedelta(days=100)
        result = apply_min_date(recent_ts, min_days=365)

        self.assertEqual(result, recent_ts)

    @patch('coinbasis.utils.time.datetime')
    def test_min_days_zero_returns_original(self, mock_datetime):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        ts = now - timedelta(days=500)
        result = apply_min_date(ts, min_days=0)

        self.assertEqual(result, ts)

    @patch('coinbasis.utils.time.datetime')
    def test_negative_min_days_returns_original(self, mock_datetime):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        ts = now - timedelta(days=500)
        result = apply_min_date(ts, min_days=-10)

        self.assertEqual(result, ts)

    @patch('coinbasis.utils.time.datetime')
    def test_exact_boundary(self, mock_datetime):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        boundary_ts = now - timedelta(days=365)
        result = apply_min_date(boundary_ts, min_days=365)

        self.assertEqual(result, boundary_ts)