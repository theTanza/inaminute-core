# Contributing

Thank you for helping make scheduling infrastructure safer and easier to reuse.

## Before opening a pull request

1. Search existing issues and open one for substantial behavior changes.
2. Use only fictional, synthetic fixtures.
3. Install the development tools with `python -m pip install -e ".[dev]"`.
4. Run `ruff check .`, `pytest --cov`, and `python scripts/privacy_guard.py`.
5. Keep commits focused and explain user-visible behavior in the pull request.

Never commit real student data, proprietary catalogs, service configuration,
access tokens, private keys, database files, or production exports.

## Design expectations

- Public APIs need type hints and concise docstrings.
- Results must remain deterministic for identical inputs.
- New search behavior needs resource limits and failure tests.
- Scoring changes need an explainable formula and stable scale.
- Breaking changes require a migration note and major-version discussion.

## Developer certificate of origin

By contributing, you certify that you have the right to submit the work under the
Apache License 2.0. Add a sign-off with `git commit -s` if a maintainer requests it.

## Review

Maintainers may request changes for correctness, privacy, maintainability, or
scope. Small pull requests are easier to review and more likely to merge quickly.
