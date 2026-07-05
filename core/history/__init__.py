"""Historical Runtime Foundation — compares snapshots across time."""

from .foundation import (
    HistoricalEntry,
    HistoricalSnapshot,
    HistoricalTrend,
    HistoricalTrace,
    HistoricalResult,
    FoundationHistoricalRuntime,
    TREND_IMPROVING,
    TREND_DECLINING,
    TREND_STABLE,
    TREND_UNKNOWN,
)

__all__ = [
    "HistoricalEntry",
    "HistoricalSnapshot",
    "HistoricalTrend",
    "HistoricalTrace",
    "HistoricalResult",
    "FoundationHistoricalRuntime",
    "TREND_IMPROVING",
    "TREND_DECLINING",
    "TREND_STABLE",
    "TREND_UNKNOWN",
]
