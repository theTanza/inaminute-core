# InAMinute Core

Build better schedules without shipping anyone's private data.

InAMinute Core is a small, deterministic Python engine for turning candidate
meeting sections into ranked, conflict-free schedules. It is designed for
products that need transparent results, predictable resource limits, and full
control over their own data.

This repository is an institution-neutral extraction of scheduling logic used
by the InAMinute product. The public package is independently versioned and does
not contain production configuration, student information, real catalogs,
private curriculum data, or service credentials.

## Why it is useful

- Deterministic output: identical inputs and preferences produce identical ranks.
- Explainable ranking: every result includes timing, compactness, distribution,
  and location components on a documented 100-point scale.
- Privacy by architecture: applications provide in-memory candidates; the core
  has no database, analytics, network, authentication, or telemetry layer.
- Safe resource limits: combination caps and time budgets prevent accidental
  unbounded work.
- Portable integration: zero runtime dependencies and support for Python 3.10+.

## Quick start

```bash
python -m pip install -e .
inaminute-demo --limit 3
```

Or use the API directly:

```python
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
    print(schedule.score, schedule.signature)
```

The example identifiers are deliberately fictional. Replace them with data your
application is authorized to process.

## How ranking works

Only conflict-free combinations are scored. The default 100-point model assigns:

| Component | Points | What it rewards |
| --- | ---: | --- |
| Timing | 40 | Meetings inside the preferred daily window |
| Compactness | 30 | Short gaps between meetings on the same day |
| Distribution | 20 | Fewer active days, or balanced days when configured |
| Location | 10 | Nearby consecutive meetings using your distance map |

All preferences are soft. An early section can still appear when it is the only
valid option. See [scoring.md](docs/scoring.md) for formulas and tradeoffs.

## Deliberate boundaries

The core does not fetch catalogs, infer eligibility, resolve prerequisites,
store personal data, or connect to a production service. Those are application
responsibilities and often carry institution-specific privacy obligations. See
[privacy-boundary.md](docs/privacy-boundary.md) before integrating real data.

The first public release focuses on repeated weekly meeting windows. Multi-block
sections, hard preference constraints, and scalable search strategies are on the
[roadmap](ROADMAP.md).

## Contributing

Issues and pull requests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md),
read the [governance model](GOVERNANCE.md), and report vulnerabilities through
the private process in [SECURITY.md](SECURITY.md).

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
