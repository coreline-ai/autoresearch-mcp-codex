"""Logging and memory management for AutoResearch Agent System.

Handles RESULTS.tsv, DECISIONS.md, and MEMORY.md updates.
"""

from __future__ import annotations

from datetime import datetime, timezone

RESULTS_HEADER = [
    "iteration", "timestamp", "hypothesis_id", "status", "decision_code",
    "score_before", "score_after", "score_delta", "tests_pass", "constraints_ok",
    "critic_severity", "critic_recommendation", "changed_files_count",
    "change_summary", "rollback_reason",
]


def log_result(
    config,
    iteration: int,
    hypothesis_id: str,
    status: str,
    code: str,
    score_before: float,
    score_after: float,
    tests_pass: bool,
    summary: str,
    reason: str,
    constraints_ok: bool = True,
    critic_severity: str = "low",
    critic_recommendation: str = "accept",
    changed_files_count: int = 1,
) -> None:
    """Append one row to RESULTS.tsv."""
    p = config.results_path
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("\t".join(RESULTS_HEADER) + "\n", encoding="utf-8")

    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    delta = round(score_after - score_before, 6)
    row = [
        str(iteration),
        ts,
        hypothesis_id,
        status,
        code,
        str(score_before),
        str(score_after),
        str(delta),
        str(tests_pass).lower(),
        str(constraints_ok).lower(),
        critic_severity,
        critic_recommendation,
        str(changed_files_count),
        summary.replace("\t", " "),
        reason.replace("\t", " "),
    ]
    with p.open("a", encoding="utf-8") as f:
        f.write("\t".join(row) + "\n")


def log_decision(
    config,
    iteration: int,
    decision: str,
    code: str,
    score_before: float,
    score_after: float,
    tests_pass: bool,
    summary: str,
    reason: str,
    constraints_ok: bool = True,
    critic_severity: str = "low",
    critic_recommendation: str = "accept",
    changed_files_count: int = 1,
) -> None:
    """Append one decision block to DECISIONS.md."""
    p = config.decisions_path
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# DECISIONS\n\n", encoding="utf-8")

    delta = round(score_after - score_before, 6)
    block = (
        f"\n## Iteration {iteration}\n"
        f"- decision: {decision}\n"
        f"- decision_code: {code}\n"
        f"- score_before: {score_before}\n"
        f"- score_after: {score_after}\n"
        f"- score_delta: {'+' if delta >= 0 else ''}{delta}\n"
        f"- tests_pass: {tests_pass}\n"
        f"- constraints_ok: {constraints_ok}\n"
        f"- critic_severity: {critic_severity}\n"
        f"- critic_recommendation: {critic_recommendation}\n"
        f"- changed_files_count: {changed_files_count}\n"
        f"- change_summary: {summary}\n"
        f"- reason: {reason}\n"
    )
    with p.open("a", encoding="utf-8") as f:
        f.write(block)


MAX_MEMORY_ITEMS = 8


def update_memory(config, code: str, summary: str, reason: str) -> None:
    """Update MEMORY.md with new accepted/rejected patterns.

    Keeps each section under MAX_MEMORY_ITEMS entries,
    removing oldest items when the limit is exceeded.
    """
    p = config.memory_path
    p.parent.mkdir(parents=True, exist_ok=True)
    sections: dict[str, list[str]] = {
        "Accepted Patterns": [],
        "Rejected Patterns": [],
        "Known Risks": [],
        "Strategy Notes": [],
    }

    if p.exists():
        content = p.read_text(encoding="utf-8")
        cur = None
        for line in content.split("\n"):
            if line.startswith("## "):
                s = line[3:].strip()
                if s in sections:
                    cur = s
            elif cur and line.startswith("- "):
                sections[cur].append(line[2:].strip())

    # Add new entry based on decision code
    if code == "ACCEPT":
        sections["Accepted Patterns"].append(summary)
    elif code in ("SCORE_REGRESSION", "TEST_FAIL", "CONSTRAINT_FAIL",
                   "CRITIC_BLOCK", "SCOPE_VIOLATION", "FORBIDDEN_FILE",
                   "NO_CODE_CHANGE", "EVAL_CRASH", "IMPLEMENT_ERROR"):
        entry = f"{summary} ({code})"
        if reason:
            entry += f": {reason}"
        sections["Rejected Patterns"].append(entry)

    # Trim sections to max items (keep most recent)
    for key in sections:
        if len(sections[key]) > MAX_MEMORY_ITEMS:
            sections[key] = sections[key][-MAX_MEMORY_ITEMS:]

    # Write updated memory
    with p.open("w", encoding="utf-8") as f:
        f.write("# MEMORY\n")
        for section_name, items in sections.items():
            f.write(f"\n## {section_name}\n")
            for item in items:
                f.write(f"- {item}\n")
