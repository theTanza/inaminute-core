"""Minimal example: choose one conflict-free section from each requirement."""

from inaminute_core import ScheduleGenerator, ScheduleSection

candidates = {
    "SYN-101": [
        ScheduleSection("syn-101-a", "SYN 101", "MW", "09:00", "10:15"),
        ScheduleSection("syn-101-b", "SYN 101", "TR", "09:00", "10:15"),
    ],
    "SYN-202": [
        ScheduleSection("syn-202-a", "SYN 202", "MW", "10:30", "11:45"),
        ScheduleSection("syn-202-b", "SYN 202", "TR", "09:30", "10:45"),
    ],
}

for schedule in ScheduleGenerator().generate_schedules(candidates, limit=3):
    print(schedule.score, [section.section_id for section in schedule.sections])
