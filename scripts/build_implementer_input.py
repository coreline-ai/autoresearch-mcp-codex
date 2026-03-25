#!/usr/bin/env python3
"""
Build implementer input JSON from plan and context
"""

from __future__ import annotations

import json
from pathlib import Path


def build_implementer_input() -> dict:
    """Create implementer input from PLAN.md and context"""
    plan_path = Path("agent/PLAN.md")
    task_path = Path("agent/TASK.md")
    rules_path = Path("agent/RULES.md")

    plan_content = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    task_content = task_path.read_text(encoding="utf-8") if task_path.exists() else ""
    rules_content = rules_path.read_text(encoding="utf-8") if rules_path.exists() else ""

    # Extract selected hypothesis and change scope
    selected_hypothesis = ""
    change_scope = []
    for line in plan_content.split("\n"):
        if line.startswith("## Selected Hypothesis"):
            selected_hypothesis = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line.startswith("- ") and "src/" in line:
            change_scope.append(line[2:].strip())

    return {
        "selected_hypothesis": selected_hypothesis,
        "change_scope": change_scope,
        "task_summary": task_content[:500] if task_content else "",
        "rules_summary": rules_content[:500] if rules_content else "",
        "forbidden_paths": [
            "eval/frozen_eval.py",
            "eval/fixtures.json",
            "eval/baseline.json",
            "agent/RESULTS.tsv"
        ]
    }


def main() -> int:
    """Main entry point"""
    input_data = build_implementer_input()

    output_path = Path("tmp/implementer_input.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(
        json.dumps(input_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Implementer input created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
