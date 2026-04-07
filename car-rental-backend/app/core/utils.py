from datetime import UTC, date, datetime, time


def date_to_utc_datetime(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=UTC)
