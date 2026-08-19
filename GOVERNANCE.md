# Governance

InAMinute Core is maintained by the InAMinute maintainers. Decisions are made in
public issues and pull requests whenever security or privacy does not require a
private channel.

## Roles

- Contributors propose issues, documentation, tests, and code changes.
- Maintainers review changes, manage releases, and enforce project boundaries.
- The lead maintainer makes the final call when consensus cannot be reached.

## Decision principles

1. Protect users and private data.
2. Preserve deterministic, explainable behavior.
3. Prefer institution-neutral primitives over proprietary policy.
4. Require tests for behavior changes and migration notes for breaking changes.
5. Keep runtime dependencies minimal and justified.

## Becoming a maintainer

Consistent contributors may be invited after demonstrating sound technical
judgment, respectful collaboration, and care for the privacy boundary. Access is
granted gradually and may be removed for inactivity or policy violations.

## Releases

Maintainers use semantic versioning. Pull requests require passing automated
checks and review. Security releases may follow a private embargo coordinated
through the process in `SECURITY.md`.
