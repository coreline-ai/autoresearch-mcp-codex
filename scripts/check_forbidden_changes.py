#!/usr/bin/env python3
"""
Check if any forbidden files were modified
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


FORBIDDEN_PATHS = [
    "eval/frozen_eval.py",
    "eval/fixtures.json",
    "eval/baseline.json",
]


def check_forbidden_changes() -> tuple[bool, list[str]]:
    """Check if forbidden files were modified"""
    changed_files = []

    # Get git status --porcelain to find modified files
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    for line in result.stdout.split("\n"):
        if not line:
            continue
        status = line[:2]
        filepath = line[3:]

        # Check if file matches any forbidden path
        for forbidden in FORBIDDEN_PATHS:
            if filepath == forbidden or filepath.endswith(forbidden):
                changed_files.append(filepath)

    return len(changed_files) == 0, changed_files


def main() -> int:
    """Main entry point"""
    clean, changed = check_forbidden_changes()

    if not clean:
        print("ERROR: Forbidden files were modified:", file=sys.stderr)
        for f in changed:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("OK: No forbidden files modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
