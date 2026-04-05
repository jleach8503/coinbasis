from enum import Enum
from datetime import datetime, timezone, timedelta


class TimeInterval(Enum):
    MIN = '5m'
    HOUR = 'hourly'
    DAY = 'daily'


class TimeRange(Enum):
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'


def normalize_timestamp(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        timestamp = timestamp.astimezone(timezone.utc)

    return timestamp.replace(second=0, microsecond=0)


def to_iso_minute(timestamp: datetime) -> str:
    return timestamp.strftime('%Y-%m-%dT%H:%M')


def get_time_window(timestamp: datetime, span: TimeRange | TimeInterval) -> tuple[datetime, datetime]:
    '''
    Given a timestamp and a TimeRange or TimeInterval, returns the start and end times for the span,
    beginning with the start of the span specified.  For example, specifying WEEK will return the start
    and end of the week (Monday - Saturday) for the week the timestamp falls into.
    '''

    timestamp = normalize_timestamp(timestamp)
    match span:
        case TimeInterval.MIN:
            minute = (timestamp.minute // 5) * 5
            start = timestamp.replace(minute=minute)
            end = start + timedelta(minutes=5)
        case TimeInterval.HOUR:
            start = timestamp.replace(minute=0)
            end = start + timedelta(hours=1)
        case TimeRange.DAY | TimeInterval.DAY:
            start = timestamp.replace(hour=0, minute=0)
            end = start + timedelta(days=1)
        case TimeRange.WEEK:
            weekday = timestamp.weekday()
            start = (timestamp - timedelta(days=weekday)).replace(hour=0, minute=0)
            end = start + timedelta(days=7)
        case TimeRange.MONTH:
            start = timestamp.replace(day=1, hour=0, minute=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        case TimeRange.YEAR:
            start = timestamp.replace(month=1,day=1,hour=0, minute=0)
            end = start.replace(year=start.year + 1)
        case _:
            raise ValueError(f'Unsupported span: {span}')

    end = end - timedelta(minutes=1)
    return start, end


def apply_min_date(timestamp: datetime, min_days: int) -> datetime:
    if (min_days > 0):
        min_date = datetime.now(timezone.utc) - timedelta(days=min_days)
        return max(timestamp, min_date)
    return timestamp
