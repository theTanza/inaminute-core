"""Runnable synthetic demonstration for InAMinute Core."""

from __future__ import annotations

import argparse
import json

from .scheduler import ScheduleGenerator, ScheduleSection, ScoringPreferences


def synthetic_candidates() -> dict[str, list[ScheduleSection]]:
    """Return a small, fictional data set with no institutional information."""

    return {
        "SYN-101": [
            ScheduleSection(
                "syn-101-a",
                "SYN 101",
                "MW",
                "09:00",
                "10:15",
                course_name="Synthetic Systems",
                section_suffix="A",
                instructor="Example Instructor",
                building="North",
            ),
            ScheduleSection(
                "syn-101-b",
                "SYN 101",
                "TR",
                "13:00",
                "14:15",
                course_name="Synthetic Systems",
                section_suffix="B",
                instructor="Sample Instructor",
                building="South",
            ),
        ],
        "SYN-202": [
            ScheduleSection(
                "syn-202-a",
                "SYN 202",
                "MW",
                "10:30",
                "11:45",
                course_name="Responsible Automation",
                section_suffix="A",
                instructor="Demo Instructor",
                building="North",
            ),
            ScheduleSection(
                "syn-202-b",
                "SYN 202",
                "TR",
                "14:30",
                "15:45",
                course_name="Responsible Automation",
                section_suffix="B",
                instructor="Example Instructor",
                building="East",
            ),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ranked schedules from a fully synthetic data set."
    )
    parser.add_argument("--limit", type=int, default=3, help="number of schedules to show")
    args = parser.parse_args()

    preferences = ScoringPreferences(
        preferred_start="09:00",
        preferred_end="16:00",
        location_distances={
            ("North", "South"): 0.7,
            ("North", "East"): 0.4,
            ("South", "East"): 0.5,
        },
    )
    schedules = ScheduleGenerator(preferences=preferences).generate_schedules(
        synthetic_candidates(), limit=args.limit
    )
    output = [
        {
            "rank": index,
            "score": schedule.score,
            "score_breakdown": schedule.score_breakdown.as_dict(),
            "sections": [section.display_name for section in schedule.sections],
        }
        for index, schedule in enumerate(schedules, start=1)
    ]
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
