"""Fail when public-repository boundaries are violated.

This is a narrow defense-in-depth check, not a substitute for secret scanning or
human review.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", ".pytest_cache", ".ruff_cache", "build", "dist"}
EXCLUDED_FILES = {".coverage"}
FORBIDDEN_SUFFIXES = {
    ".cer",
    ".db",
    ".mobileprovision",
    ".p12",
    ".pdf",
    ".pem",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_FILENAMES = {".env", ".env.local", ".env.production"}
FORBIDDEN_PATH_PARTS = {"knowledge", "production_data", "student_records", "study-guides"}
MAX_PUBLIC_FILE_BYTES = 1_000_000

# Split selected strings so the guard does not flag its own definitions.
FORBIDDEN_TEXT = {
    "private university acronym": "kf" + "upm",
    "private bulletin host": "bulletin." + "kfupm.edu.sa",
    "production API host": "api." + "inaminute.app",
    "private key material": "BEGIN " + "PRIVATE KEY",
    "RSA private key material": "BEGIN RSA " + "PRIVATE KEY",
    "OpenSSH private key material": "BEGIN OPENSSH " + "PRIVATE KEY",
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|client[_-]?secret|access[_-]?token|database[_-]?url)\s*[:=]\s*['\"][^'\"]{12,}"
)
TEXT_SUFFIXES = {
    "",
    ".cff",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def public_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name not in EXCLUDED_FILES
        and not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
        and not any(part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
    )


def scan() -> list[str]:
    findings: list[str] = []
    for path in public_files():
        relative = path.relative_to(ROOT)
        lower_parts = {part.lower() for part in relative.parts}
        if lower_parts.intersection(FORBIDDEN_PATH_PARTS):
            findings.append(f"forbidden path: {relative}")
        if path.name.lower() in FORBIDDEN_FILENAMES:
            findings.append(f"environment file: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"forbidden file type: {relative}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            findings.append(f"oversized file: {relative}")
        if path == Path(__file__).resolve() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"unexpected binary content: {relative}")
            continue
        lowered = text.lower()
        for label, forbidden in FORBIDDEN_TEXT.items():
            if forbidden.lower() in lowered:
                findings.append(f"{label}: {relative}")
        if SECRET_ASSIGNMENT.search(text):
            findings.append(f"possible embedded secret assignment: {relative}")
    return findings


def main() -> int:
    findings = scan()
    if findings:
        print("Public-repository boundary check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Public-repository boundary check passed ({len(public_files())} files scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
