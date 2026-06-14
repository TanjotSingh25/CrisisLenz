"""Shared value enums. Inheriting from str so members compare equal to their
string value (e.g. SourceType.eonet_event == "eonet_event"), which keeps
SQLAlchemy filters and existing string comparisons working unchanged."""
from enum import Enum


class SourceType(str, Enum):
    wikinews_dump = "wikinews_dump"
    eonet_event = "eonet_event"


class ReplayStatus(str, Enum):
    pending = "pending"
    released = "released"
    processed = "processed"
    rejected = "rejected"
    failed = "failed"


class AlertStatus(str, Enum):
    new = "new"
    acknowledged = "acknowledged"
    dismissed = "dismissed"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    unknown = "unknown"
