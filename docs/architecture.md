# Architecture

InAMinute Core is intentionally a pure library. The data flow is one-way:

1. A host application converts authorized source data into `ScheduleSection` objects.
2. `ScheduleGenerator` validates inputs and bounds the candidate space.
3. The generator enumerates combinations in a stable order and removes conflicts.
4. `ScheduleScorer` assigns an explainable score to every valid combination.
5. The host application decides how to display, persist, or discard the results.

The library does not make network requests or mutate external state. It does not
know who the user is, where candidate data came from, or how results are shown.

## Determinism

Candidate mappings are ordered by key, candidate sections are ordered by ID, and
final results are sorted by descending score then stable schedule signature.
Callers should provide stable section IDs. Floating-point distance inputs are
clamped to the documented zero-to-one range before scoring.

## Complexity and limits

With candidate group sizes `n1` through `nk`, exhaustive enumeration considers
`n1 × ... × nk` combinations. The generator rejects spaces larger than
`max_combinations` before work begins and checks `timeout_seconds` while running.

This makes behavior predictable for small and medium candidate sets. Constraint
propagation and heuristic search are planned for larger sets.

## Trust boundary

Input validation catches malformed days, times, empty groups, invalid preference
windows, and unsafe search limits. It does not determine whether the host is
authorized to process its data. That responsibility remains outside the package.
