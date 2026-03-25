#!/usr/bin/env python3
"""
Update MEMORY.md based on iteration results
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


MEMORY_PATH = Path("agent/MEMORY.md")


def parse_sections(text: str) -> dict[str, list[str]]:
    """Parse existing sections from MEMORY.md"""
    sections = {
        "Accepted Patterns": [],
        "Rejected Patterns": [],
        "Known Risks": [],
        "Strategy Notes": [],
    }

    current_section = None
    for line in text.split("\n"):
        if line.startswith("## "):
            section_name = line[3:].strip()
            if section_name in sections:
                current_section = section_name
        elif current_section and line.startswith("- "):
            sections[current_section].append(line[2:].strip())

    return sections


def update_memory(payload: dict) -> None:
    """Update MEMORY.md with new learnings from iteration."""
    if not MEMORY_PATH.exists():
        # Create new MEMORY.md with default structure
        content = """# MEMORY

## Accepted Patterns
-

## Rejected Patterns
-

## Known Risks
-

## Strategy Notes
-
"""
    else:
        content = MEMORY_PATH.read_text(encoding="utf-8")

    sections = parse_sections(content)

    decision_code = payload.get("decision_code", "")
    change_summary = payload.get("change_summary", "")

    if decision_code == "ACCEPT":
        sections["Accepted Patterns"].append(f"- {change_summary}")
    elif decision_code in ["SCORE_REGRESSION", "TEST_FAIL", "CONSTRAINT_FAIL"]:
        sections["Rejected Patterns"].append(f"- {change_summary}: {payload.get('rollback_reason', '')}")

    # Write updated memory
    with MEMORY_PATH.open("w", encoding="utf-8") as f:
        f.write("# MEMORY\n\n")
        f.write("## Accepted Patterns\n")
        for item in sections["Accepted Patterns"]:
            f.write(f"{item}\n")
        f.write("\n## Rejected Patterns\n")
        for item in sections["Rejected Patterns"]:
            f.write(f"{item}\n")
        f.write("\n## Known Risks\n")
        for item in sections["Known Risks"]:
            f.write(f"{item}\n")
        f.write("\n## Strategy Notes\n")
        for item in sections["Strategy Notes"]:
            f.write(f"{item}\n")


def main() -> int:
    """Main entry point"""
    if len(sys.argv) == 2:
        payload_path = Path(sys.argv[1])
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    elif not sys.stdin.isatty():
        payload = json.loads(sys.stdin.read())
    else:
        # No update needed
        return 0

    update_memory(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
