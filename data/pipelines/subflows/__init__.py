"""Stage subflows for the weekly location report. Each one takes its inputs as arguments."""

from data.pipelines.subflows.extract_weekly_events import extract_weekly_events
from data.pipelines.subflows.load_weekly_location_performance import (
    load_weekly_location_performance,
)
from data.pipelines.subflows.transform_location_week import transform_location_week
from data.pipelines.subflows.write_eval_snapshot import write_eval_snapshot

__all__ = [
    "extract_weekly_events",
    "transform_location_week",
    "write_eval_snapshot",
    "load_weekly_location_performance",
]
