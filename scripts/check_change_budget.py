#!/usr/bin/env python3
"""
Check if changes are within acceptable budget
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MAX_FILES = 5
MAX_DIFF_LINES = 200


def check_change_budget() -> tuple[bool, dict]:
    """Check if changes are within budget"""
    # Get git diff --stat
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        capture_output=True,
        text=True
    )

    if not result.stdout:
        return True, {"within_budget": True, "changed_files": 0, "diff_lines": 0}

    # Parse git diff --stat output
    changed_files = 0
    total_lines = 0

    for line in result.stdout.split("\n"):
        if not line or line.startswith(" "):
            continue
        parts = line.split("|")
        if len(parts) >= 2:
            changed_files += 1
            # Extract line count (format: " file.txt | 100 10")
            line_info = parts[-1].strip()
            if line_info:
                numbers = line_info.split()
                if numbers:
                    total_lines += int(numbers[0])

    within_budget = (
        changed_files <= MAX_FILES and
        total_lines <= MAX_DIFF_LINES
    )

    return within_budget, {
        "within_budget": within_budget,
        "changed_files": changed_files,
        "diff_lines": total_lines,
        "max_files": MAX_FILES,
        "max_diff_lines": MAX_DIFF_LINES
    }


def main() -> int:
    """Main entry point"""
    try:
        within_budget, info = check_change_budget()

        if not within_budget:
            print("ERROR: Change budget exceeded:", file=sys.stderr)
            print(f"  Changed files: {info['changed_files']}/{info['max_files']}", file=sys.stderr)
            print(f"  Diff lines: {info['diff_lines']}/{info['max_diff_lines']}", file=sys.stderr)
            return 1

        print(f"OK: Changes within budget ({info['changed_files']} files, {info['diff_lines']} lines)")
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
