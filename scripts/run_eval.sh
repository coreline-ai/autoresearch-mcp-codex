#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"

mkdir -p tmp

STDOUT_FILE="tmp/eval_stdout.txt"
STDERR_FILE="tmp/eval_stderr.txt"
EXIT_CODE=0

$PYTHON eval/frozen_eval.py > "$STDOUT_FILE" 2> "$STDERR_FILE" || EXIT_CODE=$?

if [[ "$EXIT_CODE" -ne 0 ]]; then
  $PYTHON <<'PY'
import json
from pathlib import Path

stderr = Path("tmp/eval_stderr.txt").read_text(encoding="utf-8", errors="ignore") if Path("tmp/eval_stderr.txt").exists() else ""

result = {
    "score": 0.0,
    "tests_pass": False,
    "constraints_ok": False,
    "latency_ms": None,
    "latency_delta_pct": None,
    "regressions": ["frozen eval failed to execute"],
    "notes": [stderr[-4000:]]
}
Path("tmp/eval_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
  exit "$EXIT_CODE"
fi

cp "$STDOUT_FILE" tmp/eval_result.json
exit 0
