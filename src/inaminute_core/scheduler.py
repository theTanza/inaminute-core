"""Deterministic, institution-neutral schedule generation primitives.

The public core intentionally knows nothing about a university, catalog, student,
or production service. Applications provide candidate sections and, optionally,
their own location-distance model.
"""

from __future__ import annotations

import math
import re
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from itertools import pairwise, product
from typing import Final

DAY_ORDER: Final[tuple[str, ...]] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

_DAY_ALIASES: Final[dict[str, str]] = {
    "m": "Monday",
    "mon": "Monday",
    "monday": "Monday",
    "t": "Tuesday",
    "tu": "Tuesday",
    "tue": "Tuesday",
    "tues": "Tuesday",
    "tuesday": "Tuesday",
    "w": "Wednesday",
    "wed": "Wednesday",
    "wednesday": "Wednesday",
    "r": "Thursday",
    "th": "Thursday",
    "thu": "Thursday",
    "thur": "Thursday",
    "thurs": "Thursday",
    "thursday": "Thursday",
    "f": "Friday",
    "fri": "Friday",
    "friday": "Friday",
    "s": "Saturday",
    "sa": "Saturday",
    "sat": "Saturday",
    "saturday": "Saturday",
    "u": "Sunday",
    "su": "Sunday",
    "sun": "Sunday",
    "sunday": "Sunday",
}

_COMPACT_DAY_CODES: Final[dict[str, str]] = {
    "M": "Monday",
    "T": "Tuesday",
    "W": "Wednesday",
    "R": "Thursday",
    "F": "Friday",
    "S": "Saturday",
    "U": "Sunday",
}


class ScheduleGenerationTimeout(RuntimeError):
    """Raised when schedule generation exceeds its configured time budget."""


class ScheduleInputError(ValueError):
    """Raised when candidate schedule data is invalid or ambiguous."""


def time_str_to_minutes(value: str | int) -> int:
    """Convert a 24-hour or AM/PM time to minutes after midnight."""

    if isinstance(value, int):
        if 0 <= value < 24 * 60:
            return value
        raise ScheduleInputError("minute values must be between 0 and 1439")

    cleaned = value.strip().upper().replace(".", "")
    twelve_hour = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)", cleaned)
    if twelve_hour:
        hour = int(twelve_hour.group(1))
        minute = int(twelve_hour.group(2) or "0")
        if not 1 <= hour <= 12 or not 0 <= minute <= 59:
            raise ScheduleInputError(f"invalid time: {value!r}")
        hour = hour % 12 + (12 if twelve_hour.group(3) == "PM" else 0)
        return hour * 60 + minute

    twenty_four_hour = re.fullmatch(r"(\d{1,2}):(\d{2})", cleaned)
    if twenty_four_hour:
        hour = int(twenty_four_hour.group(1))
        minute = int(twenty_four_hour.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour * 60 + minute

    raise ScheduleInputError(f"invalid time {value!r}; use HH:MM, H AM, or H:MM PM")


def minutes_to_time_str(value: int) -> str:
    """Convert minutes after midnight to a zero-padded 24-hour time."""

    if not 0 <= value < 24 * 60:
        raise ScheduleInputError("minute values must be between 0 and 1439")
    return f"{value // 60:02d}:{value % 60:02d}"


def _normalize_day(value: str) -> str:
    normalized = _DAY_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise ScheduleInputError(f"unrecognized day: {value!r}")
    return normalized


def parse_days(value: str | Iterable[str]) -> tuple[str, ...]:
    """Normalize day names, aliases, or compact codes such as ``MWF``."""

    parsed: list[str]
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            raise ScheduleInputError("at least one meeting day is required")
        if re.fullmatch(r"[MTWRFSU]+", cleaned):
            parsed = [_COMPACT_DAY_CODES[code] for code in cleaned]
        else:
            tokens = [token for token in re.split(r"[,/|\s]+", cleaned) if token]
            parsed = [_normalize_day(token) for token in tokens]
    else:
        parsed = [_normalize_day(str(token)) for token in value]

    if not parsed:
        raise ScheduleInputError("at least one meeting day is required")
    return tuple(day for day in DAY_ORDER if day in set(parsed))


@dataclass(frozen=True)
class ScheduleSection:
    """A single candidate section with one repeated weekly meeting window."""

    section_id: str
    course_code: str
    day_pattern: str | Iterable[str]
    start_time: str | int
    end_time: str | int
    course_name: str = ""
    section_suffix: str = ""
    instructor: str = ""
    activity_type: str = "class"
    location: str = ""
    building: str = ""
    status: str = "open"
    linked_component_key: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        if not self.section_id.strip():
            raise ScheduleInputError("section_id cannot be empty")
        if not self.course_code.strip():
            raise ScheduleInputError("course_code cannot be empty")
        if self.end_minutes <= self.start_minutes:
            raise ScheduleInputError(f"section {self.section_id!r} must end after it starts")

    @cached_property
    def days(self) -> tuple[str, ...]:
        return parse_days(self.day_pattern)

    @cached_property
    def start_minutes(self) -> int:
        return time_str_to_minutes(self.start_time)

    @cached_property
    def end_minutes(self) -> int:
        return time_str_to_minutes(self.end_time)

    @property
    def display_name(self) -> str:
        suffix = f" {self.section_suffix}" if self.section_suffix else ""
        return f"{self.course_code}{suffix}"


@dataclass(frozen=True)
class ScoreBreakdown:
    """Explainable score components, each bounded to its advertised maximum."""

    timing: float
    compactness: float
    distribution: float
    location: float

    @property
    def total(self) -> float:
        return round(self.timing + self.compactness + self.distribution + self.location, 2)

    def as_dict(self) -> dict[str, float]:
        return {
            "total": self.total,
            "timing": round(self.timing, 2),
            "compactness": round(self.compactness, 2),
            "distribution": round(self.distribution, 2),
            "location": round(self.location, 2),
        }


@dataclass(frozen=True)
class Schedule:
    """A valid schedule and its explainable preference score."""

    sections: tuple[ScheduleSection, ...]
    score_breakdown: ScoreBreakdown | None = None

    @property
    def score(self) -> float:
        return self.score_breakdown.total if self.score_breakdown else 0.0

    @cached_property
    def signature(self) -> tuple[str, ...]:
        return tuple(sorted(section.section_id for section in self.sections))

    @cached_property
    def by_day(self) -> dict[str, tuple[ScheduleSection, ...]]:
        grouped: dict[str, list[ScheduleSection]] = {}
        for section in self.sections:
            for day in section.days:
                grouped.setdefault(day, []).append(section)
        return {
            day: tuple(sorted(items, key=lambda item: (item.start_minutes, item.section_id)))
            for day, items in grouped.items()
        }


@dataclass(frozen=True)
class ScoringPreferences:
    """Soft preferences used to rank valid schedules."""

    preferred_start: str | int = "09:00"
    preferred_end: str | int = "17:00"
    ideal_gap_minutes: int = 15
    prefer_fewer_days: bool = True
    location_distances: Mapping[tuple[str, str], float] = field(default_factory=dict)
    unknown_location_distance: float = 0.5

    def __post_init__(self) -> None:
        if time_str_to_minutes(self.preferred_end) <= time_str_to_minutes(self.preferred_start):
            raise ScheduleInputError("preferred_end must be after preferred_start")
        if self.ideal_gap_minutes < 0:
            raise ScheduleInputError("ideal_gap_minutes cannot be negative")
        if not 0 <= self.unknown_location_distance <= 1:
            raise ScheduleInputError("unknown_location_distance must be between 0 and 1")


class ScheduleValidator:
    """Validate combinations without relying on external services or state."""

    @staticmethod
    def sections_conflict(
        left: ScheduleSection,
        right: ScheduleSection,
        *,
        allow_exact_linked_overlap: bool = True,
    ) -> bool:
        shared_days = set(left.days).intersection(right.days)
        if not shared_days:
            return False

        overlaps = left.start_minutes < right.end_minutes and right.start_minutes < left.end_minutes
        if not overlaps:
            return False

        same_link = (
            allow_exact_linked_overlap
            and left.linked_component_key
            and left.linked_component_key == right.linked_component_key
            and left.start_minutes == right.start_minutes
            and left.end_minutes == right.end_minutes
            and left.days == right.days
        )
        return not bool(same_link)

    @classmethod
    def is_valid(
        cls,
        sections: Sequence[ScheduleSection],
        *,
        allow_exact_linked_overlap: bool = True,
    ) -> bool:
        for index, left in enumerate(sections):
            for right in sections[index + 1 :]:
                if cls.sections_conflict(
                    left,
                    right,
                    allow_exact_linked_overlap=allow_exact_linked_overlap,
                ):
                    return False
        return True


class ScheduleScorer:
    """Rank schedules on a transparent 100-point scale."""

    def __init__(self, preferences: ScoringPreferences | None = None) -> None:
        self.preferences = preferences or ScoringPreferences()

    @staticmethod
    def _bounded(value: float, maximum: float) -> float:
        return min(max(value, 0.0), maximum)

    def _timing_score(self, schedule: Schedule) -> float:
        preferred_start = time_str_to_minutes(self.preferences.preferred_start)
        preferred_end = time_str_to_minutes(self.preferences.preferred_end)
        penalty = 0.0
        for section in schedule.sections:
            early = max(0, preferred_start - section.start_minutes)
            late = max(0, section.end_minutes - preferred_end)
            penalty += (early + late) / 60 * 4
        return self._bounded(40 - penalty, 40)

    def _compactness_score(self, schedule: Schedule) -> float:
        gaps: list[int] = []
        for sections in schedule.by_day.values():
            for left, right in pairwise(sections):
                gaps.append(max(0, right.start_minutes - left.end_minutes))
        if not gaps:
            return 30.0
        excess = sum(max(0, gap - self.preferences.ideal_gap_minutes) for gap in gaps)
        return self._bounded(30 - excess / 60 * 3, 30)

    def _distribution_score(self, schedule: Schedule) -> float:
        active_days = len(schedule.by_day)
        if active_days == 0:
            return 0.0
        if self.preferences.prefer_fewer_days:
            return self._bounded(20 - max(0, active_days - 1) * 2.5, 20)

        counts = [len(items) for items in schedule.by_day.values()]
        mean = sum(counts) / len(counts)
        variance = sum((count - mean) ** 2 for count in counts) / len(counts)
        return self._bounded(20 - math.sqrt(variance) * 4, 20)

    def _distance(self, left: ScheduleSection, right: ScheduleSection) -> float:
        left_location = left.building or left.location
        right_location = right.building or right.location
        if left_location and left_location == right_location:
            return 0.0
        distances = self.preferences.location_distances
        direct = distances.get((left_location, right_location))
        reverse = distances.get((right_location, left_location))
        raw = direct if direct is not None else reverse
        if raw is None:
            return self.preferences.unknown_location_distance
        return min(max(float(raw), 0.0), 1.0)

    def _location_score(self, schedule: Schedule) -> float:
        distances: list[float] = []
        for sections in schedule.by_day.values():
            for left, right in pairwise(sections):
                if not (left.building or left.location) or not (right.building or right.location):
                    continue
                distances.append(self._distance(left, right))
        if not distances:
            return 10.0
        return self._bounded(10 * (1 - sum(distances) / len(distances)), 10)

    def score(self, schedule: Schedule) -> ScoreBreakdown:
        return ScoreBreakdown(
            timing=self._timing_score(schedule),
            compactness=self._compactness_score(schedule),
            distribution=self._distribution_score(schedule),
            location=self._location_score(schedule),
        )


class ScheduleGenerator:
    """Generate and rank conflict-free schedules from candidate groups."""

    CLOSED_STATUSES: Final[frozenset[str]] = frozenset({"closed", "cancelled", "canceled"})

    def __init__(
        self,
        *,
        preferences: ScoringPreferences | None = None,
        include_closed: bool = False,
        allow_exact_linked_overlap: bool = True,
    ) -> None:
        self.scorer = ScheduleScorer(preferences)
        self.include_closed = include_closed
        self.allow_exact_linked_overlap = allow_exact_linked_overlap

    def _normalize_groups(
        self,
        candidate_groups: Mapping[str, Sequence[ScheduleSection]]
        | Sequence[Sequence[ScheduleSection]],
    ) -> tuple[tuple[ScheduleSection, ...], ...]:
        raw_groups = (
            tuple(candidate_groups[key] for key in sorted(candidate_groups))
            if isinstance(candidate_groups, Mapping)
            else tuple(candidate_groups)
        )
        if not raw_groups:
            raise ScheduleInputError("at least one candidate group is required")

        normalized: list[tuple[ScheduleSection, ...]] = []
        for index, group in enumerate(raw_groups):
            filtered = tuple(
                section
                for section in group
                if self.include_closed or section.status.strip().lower() not in self.CLOSED_STATUSES
            )
            if not filtered:
                raise ScheduleInputError(f"candidate group {index} has no available sections")
            normalized.append(tuple(sorted(filtered, key=lambda section: section.section_id)))
        return tuple(normalized)

    def generate_schedules(
        self,
        candidate_groups: Mapping[str, Sequence[ScheduleSection]]
        | Sequence[Sequence[ScheduleSection]],
        *,
        limit: int = 25,
        max_combinations: int = 100_000,
        timeout_seconds: float = 5.0,
    ) -> list[Schedule]:
        """Return the highest-scoring valid schedules in deterministic order."""

        if limit <= 0:
            raise ScheduleInputError("limit must be positive")
        if max_combinations <= 0:
            raise ScheduleInputError("max_combinations must be positive")
        if timeout_seconds <= 0:
            raise ScheduleInputError("timeout_seconds must be positive")

        groups = self._normalize_groups(candidate_groups)
        combination_count = math.prod(len(group) for group in groups)
        if combination_count > max_combinations:
            raise ScheduleInputError(
                f"candidate space has {combination_count:,} combinations; "
                f"configured maximum is {max_combinations:,}"
            )

        started = time.monotonic()
        schedules: list[Schedule] = []
        seen: set[tuple[str, ...]] = set()
        for combination in product(*groups):
            if time.monotonic() - started > timeout_seconds:
                raise ScheduleGenerationTimeout(
                    f"schedule generation exceeded {timeout_seconds:g} seconds"
                )
            if not ScheduleValidator.is_valid(
                combination,
                allow_exact_linked_overlap=self.allow_exact_linked_overlap,
            ):
                continue
            base = Schedule(tuple(combination))
            if base.signature in seen:
                continue
            seen.add(base.signature)
            schedules.append(Schedule(base.sections, self.scorer.score(base)))

        schedules.sort(key=lambda schedule: (-schedule.score, schedule.signature))
        return schedules[:limit]


def combinations_from_lists(
    candidate_groups: Sequence[Sequence[ScheduleSection]],
) -> Iterable[tuple[ScheduleSection, ...]]:
    """Expose the deterministic Cartesian product used by the generator."""

    return product(*candidate_groups)
