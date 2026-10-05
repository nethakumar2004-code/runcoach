from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (the format stored in the database)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Convert a timezone-aware datetime to naive UTC. Naive values are assumed to already be UTC.

    SQLite drops the UTC offset when storing, so "07:00+05:30" would otherwise be saved as 07:00 UTC.
    """
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
