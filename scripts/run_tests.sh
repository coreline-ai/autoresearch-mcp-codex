#!/usr/bin/env bash
set -euo pipefail

mkdir -p tmp

START_TS="$(python3 -c 'import time; print(time.time())')"
EXIT_CODE=0
STDOUT_FILE="tmp/tests_stdout.txt"
STDERR_FILE="tmp/tests_stderr.txt"

if [ -d "tests" ]; then
  pytest tests -q > "$STDOUT_FILE" 2> "$STDERR_FILE" || EXIT_CODE=$?
else
  echo "No tests directory found; skipping tests" > "$STDOUT_FILE"
  : > "$STDERR_FILE"
fi

END_TS="$(python3 -c 'import time; print(time.time())')"

python3 <<PY
import json
from pathlib import Path

start = float("$START_TS")
end = float("$END_TS")
stdout = Path("$STDOUT_FILE").read_text(encoding="utf-8", errors="ignore") if Path("$STDOUT_FILE").exists() else ""
stderr = Path("$STDERR_FILE").read_text(encoding="utf-8", errors="ignore") if Path("$STDERR_FILE").exists() else ""
passed = $([ "$EXIT_CODE" -eq 0 ] && echo "True" || echo "False")

result = {
    "passed": passed,
    "summary": stdout[-4000:] if stdout else ("tests passed" if passed else "tests failed"),
    "failed_tests": [],
    "duration_sec": round(end - start, 3),
    "stderr": stderr[-4000:]
}

Path("tmp/tests_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

exit "$EXIT_CODE"
