from __future__ import annotations

import json
import sys

from inaminute_core import demo


def test_demo_uses_only_synthetic_candidates() -> None:
    candidates = demo.synthetic_candidates()
    assert set(candidates) == {"SYN-101", "SYN-202"}
    assert all(
        section.course_code.startswith("SYN ") for group in candidates.values() for section in group
    )


def test_demo_prints_machine_readable_ranked_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["inaminute-demo", "--limit", "1"])
    demo.main()
    output = json.loads(capsys.readouterr().out)
    assert len(output) == 1
    assert output[0]["rank"] == 1
    assert 0 <= output[0]["score"] <= 100
