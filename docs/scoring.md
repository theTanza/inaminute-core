# Explainable scoring

Scoring ranks valid schedules; it never makes a conflicting schedule valid. Every
component is bounded, and the total is bounded from zero to 100.

## Timing: 40 points

Meetings inside the preferred start/end window receive full credit. For meetings
outside it, the score loses four points per hour before the preferred start or
after the preferred end.

## Compactness: 30 points

Consecutive meetings are compared within each day. Gaps at or below
`ideal_gap_minutes` receive full credit. Larger gaps lose three points per excess
hour across the week.

## Distribution: 20 points

By default, the score rewards fewer active days and loses 2.5 points for each day
after the first. Set `prefer_fewer_days=False` to reward an even distribution of
meetings across active days instead.

## Location: 10 points

Applications can provide normalized distances between zero (same or very close)
and one (furthest). The map is symmetric at lookup time. Unknown pairs use the
configurable neutral distance of 0.5 by default; no campus assumptions are built in.

## Why preferences are soft

A strict preferred window can hide the only feasible schedule. InAMinute Core
ranks less-preferred options lower while keeping valid fallbacks visible. Host
applications that need hard exclusions should filter candidates before generation.
