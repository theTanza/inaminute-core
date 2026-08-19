from __future__ import annotations

import pytest

import inaminute_core.scheduler as scheduler_module
from inaminute_core import (
    Schedule,
    ScheduleGenerationTimeout,
    ScheduleGenerator,
    ScheduleInputError,
    ScheduleScorer,
    ScheduleSection,
    ScheduleValidator,
    ScoringPreferences,
    minutes_to_time_str,
    parse_days,
    time_str_to_minutes,
)


def section(
    section_id: str,
    course_code: str,
    days: str,
    start: str,
    end: str,
    **kwargs: object,
) -> ScheduleSection:
    return ScheduleSection(section_id, course_code, days, start, end, **kwargs)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("09:30", 570),
        ("9 AM", 540),
        ("12:15 PM", 735),
        ("12 AM", 0),
    ],
)
def test_time_parsing(raw: str, expected: int) -> None:
    assert time_str_to_minutes(raw) == expected
    assert time_str_to_minutes(minutes_to_time_str(expected)) == expected


@pytest.mark.parametrize("raw", ["24:00", "13 PM", "nine", -1, 1440])
def test_invalid_times_are_rejected(raw: str | int) -> None:
    with pytest.raises(ScheduleInputError):
        time_str_to_minutes(raw)


def test_integer_minutes_and_output_bounds() -> None:
    assert time_str_to_minutes(90) == 90
    with pytest.raises(ScheduleInputError):
        minutes_to_time_str(1440)


def test_day_parsing_supports_names_and_compact_codes() -> None:
    assert parse_days("MWF") == ("Monday", "Wednesday", "Friday")
    assert parse_days("Sun, Tuesday, Thu") == (
        "Tuesday",
        "Thursday",
        "Sunday",
    )
    assert parse_days(["Mon", "Friday"]) == ("Monday", "Friday")


@pytest.mark.parametrize("raw", ["", "Noday", []])
def test_invalid_day_patterns_are_rejected(raw: str | list[str]) -> None:
    with pytest.raises(ScheduleInputError):
        parse_days(raw)


@pytest.mark.parametrize(
    "args",
    [
        ("", "SYN 101", "M", "09:00", "10:00"),
        ("a", "", "M", "09:00", "10:00"),
        ("a", "SYN 101", "M", "10:00", "09:00"),
    ],
)
def test_section_identity_and_time_window_are_validated(args: tuple[str, ...]) -> None:
    with pytest.raises(ScheduleInputError):
        ScheduleSection(*args)


def test_section_display_name_handles_optional_suffix() -> None:
    plain = section("a", "SYN 101", "M", "09:00", "10:00")
    suffixed = section("b", "SYN 101", "M", "09:00", "10:00", section_suffix="B")
    assert plain.display_name == "SYN 101"
    assert suffixed.display_name == "SYN 101 B"


def test_overlap_is_a_conflict_but_adjacency_is_not() -> None:
    first = section("a", "SYN 101", "MW", "09:00", "10:00")
    overlapping = section("b", "SYN 202", "M", "09:30", "10:30")
    adjacent = section("c", "SYN 303", "M", "10:00", "11:00")
    assert ScheduleValidator.sections_conflict(first, overlapping)
    assert not ScheduleValidator.sections_conflict(first, adjacent)


def test_exact_linked_overlap_can_be_allowed_or_forbidden() -> None:
    first = section(
        "a",
        "SYN 101",
        "TR",
        "11:00",
        "12:00",
        linked_component_key="shared-event",
    )
    second = section(
        "b",
        "SYN 101L",
        "TR",
        "11:00",
        "12:00",
        linked_component_key="shared-event",
    )
    assert not ScheduleValidator.sections_conflict(first, second)
    assert ScheduleValidator.sections_conflict(first, second, allow_exact_linked_overlap=False)


def test_generator_returns_only_valid_deterministic_schedules() -> None:
    groups = {
        "one": [
            section("one-a", "SYN 101", "M", "09:00", "10:00"),
            section("one-b", "SYN 101", "T", "09:00", "10:00"),
        ],
        "two": [
            section("two-a", "SYN 202", "M", "09:30", "10:30"),
            section("two-b", "SYN 202", "M", "10:15", "11:15"),
        ],
    }
    generated = ScheduleGenerator().generate_schedules(groups)
    assert [schedule.signature for schedule in generated] == [
        ("one-a", "two-b"),
        ("one-b", "two-a"),
        ("one-b", "two-b"),
    ]
    assert all(ScheduleValidator.is_valid(item.sections) for item in generated)


def test_closed_sections_are_excluded_by_default() -> None:
    groups = [[section("closed", "SYN 101", "M", "09:00", "10:00", status="closed")]]
    with pytest.raises(ScheduleInputError, match="no available sections"):
        ScheduleGenerator().generate_schedules(groups)
    assert len(ScheduleGenerator(include_closed=True).generate_schedules(groups)) == 1


def test_large_candidate_spaces_fail_before_expensive_work() -> None:
    candidates = [
        [section(f"{group}-{index}", f"SYN {group}", "M", "09:00", "10:00") for index in range(4)]
        for group in range(4)
    ]
    with pytest.raises(ScheduleInputError, match="256 combinations"):
        ScheduleGenerator().generate_schedules(candidates, max_combinations=255)


def test_generator_validates_empty_inputs_and_resource_limits() -> None:
    generator = ScheduleGenerator()
    with pytest.raises(ScheduleInputError, match="candidate group"):
        generator.generate_schedules([])
    candidates = [[section("a", "SYN 101", "M", "09:00", "10:00")]]
    for kwargs in ({"limit": 0}, {"max_combinations": 0}, {"timeout_seconds": 0}):
        with pytest.raises(ScheduleInputError):
            generator.generate_schedules(candidates, **kwargs)


def test_generator_enforces_runtime_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    timestamps = iter([0.0, 1.0])
    monkeypatch.setattr(scheduler_module.time, "monotonic", lambda: next(timestamps))
    candidates = [[section("a", "SYN 101", "M", "09:00", "10:00")]]
    with pytest.raises(ScheduleGenerationTimeout):
        ScheduleGenerator().generate_schedules(candidates, timeout_seconds=0.1)


def test_generator_deduplicates_equivalent_signatures() -> None:
    duplicate = section("a", "SYN 101", "M", "09:00", "10:00")
    generated = ScheduleGenerator().generate_schedules([[duplicate, duplicate]])
    assert [item.signature for item in generated] == [("a",)]


def test_location_model_is_caller_supplied_and_symmetric() -> None:
    first = section("a", "SYN 101", "M", "09:00", "10:00", building="North")
    second = section("b", "SYN 202", "M", "10:00", "11:00", building="South")
    preferences = ScoringPreferences(location_distances={("South", "North"): 0.2})
    score = ScheduleScorer(preferences).score(Schedule((first, second)))
    assert score.location == pytest.approx(8.0)


def test_missing_locations_are_not_penalized() -> None:
    first = section("a", "SYN 101", "M", "09:00", "10:00")
    second = section("b", "SYN 202", "M", "10:00", "11:00")
    score = ScheduleScorer().score(Schedule((first, second)))
    assert score.location == 10.0


def test_same_and_unknown_locations_follow_documented_defaults() -> None:
    north = section("a", "SYN 101", "M", "09:00", "10:00", building="North")
    same = section("b", "SYN 202", "M", "10:00", "11:00", building="North")
    unknown = section("c", "SYN 303", "M", "11:00", "12:00", building="Unknown")
    scorer = ScheduleScorer()
    assert scorer.score(Schedule((north, same))).location == 10.0
    assert scorer.score(Schedule((same, unknown))).location == 5.0


def test_soft_time_preferences_rank_instead_of_discarding() -> None:
    early = section("early", "SYN 101", "M", "07:00", "08:00")
    preferred = section("preferred", "SYN 101", "M", "10:00", "11:00")
    schedules = ScheduleGenerator().generate_schedules([[early, preferred]])
    assert [item.signature for item in schedules] == [("preferred",), ("early",)]


def test_scores_stay_on_the_documented_scale() -> None:
    sample = Schedule(
        (
            section("a", "SYN 101", "M", "06:00", "07:00", building="North"),
            section("b", "SYN 202", "M", "20:00", "21:00", building="South"),
        )
    )
    breakdown = ScheduleScorer().score(sample)
    assert 0 <= breakdown.total <= 100
    assert set(breakdown.as_dict()) == {
        "total",
        "timing",
        "compactness",
        "distribution",
        "location",
    }


def test_balanced_distribution_mode_and_empty_schedule() -> None:
    monday = section("a", "SYN 101", "M", "09:00", "10:00")
    monday_two = section("b", "SYN 202", "M", "10:00", "11:00")
    tuesday = section("c", "SYN 303", "T", "09:00", "10:00")
    scorer = ScheduleScorer(ScoringPreferences(prefer_fewer_days=False))
    assert scorer.score(Schedule((monday, tuesday))).distribution == 20.0
    assert scorer.score(Schedule((monday, monday_two, tuesday))).distribution < 20.0
    assert scorer.score(Schedule(())).distribution == 0.0
    assert Schedule(()).score == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"preferred_start": "17:00", "preferred_end": "09:00"},
        {"ideal_gap_minutes": -1},
        {"unknown_location_distance": 1.1},
    ],
)
def test_scoring_preferences_validate_bounds(kwargs: dict[str, object]) -> None:
    with pytest.raises(ScheduleInputError):
        ScoringPreferences(**kwargs)


def test_combinations_helper_uses_cartesian_product() -> None:
    one = section("a", "SYN 101", "M", "09:00", "10:00")
    two = section("b", "SYN 202", "T", "09:00", "10:00")
    assert list(scheduler_module.combinations_from_lists([[one], [two]])) == [(one, two)]
