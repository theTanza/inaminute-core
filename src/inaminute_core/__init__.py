"""InAMinute Core public API."""

from .scheduler import (
    DAY_ORDER,
    Schedule,
    ScheduleGenerationTimeout,
    ScheduleGenerator,
    ScheduleInputError,
    ScheduleScorer,
    ScheduleSection,
    ScheduleValidator,
    ScoreBreakdown,
    ScoringPreferences,
    combinations_from_lists,
    minutes_to_time_str,
    parse_days,
    time_str_to_minutes,
)

__all__ = [
    "DAY_ORDER",
    "Schedule",
    "ScheduleGenerationTimeout",
    "ScheduleGenerator",
    "ScheduleInputError",
    "ScheduleScorer",
    "ScheduleSection",
    "ScheduleValidator",
    "ScoreBreakdown",
    "ScoringPreferences",
    "combinations_from_lists",
    "minutes_to_time_str",
    "parse_days",
    "time_str_to_minutes",
]

__version__ = "0.1.0"
