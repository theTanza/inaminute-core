# Privacy boundary

The safest scheduling engine is one that does not need identity or network access.
InAMinute Core follows that rule: it accepts in-memory candidate sections and
returns in-memory schedules.

## Data the package needs

- A stable section identifier
- A display course code
- Meeting days and start/end times
- Optional labels such as instructor, activity type, or location
- Optional application-defined metadata

Only the first four fields are used for conflict detection. Optional location
labels affect ranking only when the caller supplies a distance map.

## Data the package does not need

- Names, email addresses, account IDs, or authentication tokens
- Enrollment history or academic standing
- A real institution's catalog or curriculum
- Database credentials, analytics identifiers, or service URLs
- Device information, telemetry, or advertising identifiers

Do not place sensitive personal information in `metadata`. The library will not
transmit it, but a host application may log or persist objects after they return.

## Public repository controls

The repository uses fictional fixtures, a privacy-boundary scan in CI, dependency
auditing, and GitHub security reporting. Contributors must not submit production
dumps, real student records, proprietary catalogs, secrets, private keys, or
institution-specific rule tables.

If you discover sensitive information, stop sharing the affected commit and use
the private reporting process in `SECURITY.md`.
