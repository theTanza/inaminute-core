from __future__ import annotations

from pathlib import Path

import inaminute_core

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_consistent_across_release_metadata() -> None:
    assert inaminute_core.__version__ == "0.1.0"
    assert 'version = "0.1.0"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "version: 0.1.0" in (ROOT / "CITATION.cff").read_text(encoding="utf-8")


def test_required_community_and_security_files_exist() -> None:
    required = {
        "LICENSE",
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "GOVERNANCE.md",
        "ROADMAP.md",
    }
    assert not {name for name in required if not (ROOT / name).is_file()}
