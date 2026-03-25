#!/usr/bin/env python3
"""
Log iteration result to RESULTS.tsv
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


RESULTS_PATH = Path("agent/RESULTS.tsv")


def ensure_header() -> None:
    """Create RESULTS.tsv with header if it doesn't exist."""
    if not RESULTS_PATH.exists():
        header = "\t".join([
            "iteration", "timestamp", "hypothesis_id", "status", "decision_code",
            "score_before", "score_after", "score_delta", "tests_pass", "constraints_ok",
            "critic_severity", "critic_recommendation", "changed_files_count",
            "change_summary", "rollback_reason"
        ])
        RESULTS_PATH.write_text(header + "\n", encoding="utf-8")


def main() -> int:
    """Main entry point for logging results."""
    # Allow passing JSON as argument or via stdin
    if len(sys.argv) == 2:
        payload_path = Path(sys.argv[1])
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    elif not sys.stdin.isatty():
        payload = json.loads(sys.stdin.read())
    else:
        print("Usage: log_result.py <payload.json>", file=sys.stderr)
        return 1

    ensure_header()

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    row = [
        str(payload.get("iteration", "")),
        timestamp,
        payload.get("hypothesis_id", ""),
        payload.get("status", ""),
        payload.get("decision_code", ""),
        str(payload.get("score_before", "")),
        str(payload.get("score_after", "")),
        str(payload.get("score_delta", "")),
        str(payload.get("tests_pass", "")).lower(),
        str(payload.get("constraints_ok", "")).lower(),
        payload.get("critic_severity", ""),
        payload.get("critic_recommendation", ""),
        str(payload.get("changed_files_count", "")),
        payload.get("change_summary", "").replace("\t", " "),
        payload.get("rollback_reason", "").replace("\t", " "),
    ]

    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write("\t".join(row) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
