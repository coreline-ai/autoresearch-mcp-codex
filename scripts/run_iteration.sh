#!/usr/bin/env bash
# NOTE: This is the SHELL implementation (non-primary).
# The primary execution path is: python orchestrator/cli.py single ...
# This script uses a PLACEHOLDER implementer and does NOT call Claude CLI.
set -euo pipefail

export PYTHON="${PYTHON:-python3}"

# Default values
ITERATION=1
MODE="single-agent"
BASELINE=0.0

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --iteration)
      ITERATION="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    --baseline)
      BASELINE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

echo "[iteration $ITERATION] Starting..."

# Update state
update_state() {
  $PYTHON <<PY
import json
from pathlib import Path
state = {
    "iteration": $ITERATION,
    "mode": "$MODE",
    "phase": "$1",
    "selected_hypothesis": "H-001",
    "baseline_score": $BASELINE,
    "last_updated": "2026-03-25T00:00:00Z"
}
Path("agent/ITERATION_STATE.json").write_text(
    json.dumps(state, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
}

# Phase: IMPLEMENT (placeholder)
update_state "implement"

$PYTHON <<PY
import json
from pathlib import Path
result = {
  "changed_files": ["src/query_processor.py"],
  "change_summary": "placeholder: applied punctuation normalization",
  "why_this_change": "should improve matching consistency",
  "verification_commands_run": [],
  "notes": ["placeholder implementation"]
}
Path("tmp/implementer_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

# Phase: RUN_TESTS
update_state "run_tests"
bash scripts/run_tests.sh

# Phase: RUN_EVAL
update_state "run_eval"
bash scripts/run_eval.sh

# Phase: DECIDE
update_state "decide"

# Read eval result
SCORE_AFTER="$($PYTHON -c 'import json; from pathlib import Path; print(json.loads(Path("tmp/eval_result.json").read_text(encoding="utf-8"))["score"])')"
TESTS_PASS="$($PYTHON -c 'import json; from pathlib import Path; print(json.loads(Path("tmp/tests_result.json").read_text(encoding="utf-8"))["passed"])')"

DECISION="reject"
DECISION_CODE="NO_IMPROVEMENT"
ROLLBACK_REASON="placeholder: score did not improve"

# Simple decision logic (will be enhanced with real Codex connection)
if $PYTHON -c "import sys; exit(0 if float('$SCORE_AFTER') > float('$BASELINE') else 1)"; then
  DECISION="accept"
  DECISION_CODE="ACCEPT"
  ROLLBACK_REASON=""
fi

echo "[iteration $ITERATION] Decision: $DECISION (score: $BASELINE → $SCORE_AFTER)"

# Phase: ACCEPT or REJECT
if [[ "$DECISION" == "accept" ]]; then
  update_state "accept"
  # Update baseline
  $PYTHON <<PY
import json
from pathlib import Path
baseline = json.loads(Path("eval/baseline.json").read_text(encoding="utf-8"))
baseline["score"] = float("$SCORE_AFTER")
baseline["iteration"] = $ITERATION
baseline["measured_at"] = "2026-03-25T00:00:00Z"
Path("eval/baseline.json").write_text(
    json.dumps(baseline, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
else
  update_state "reject"
  # Rollback
  bash scripts/rollback_change.sh
fi

# Write controller result for loop orchestration (after rollback)
mkdir -p tmp
$PYTHON <<PY
import json
from pathlib import Path
result = {
  "decision": "$DECISION",
  "decision_code": "$DECISION_CODE",
  "score_after": float("$SCORE_AFTER"),
  "score_before": float("$BASELINE"),
  "score_delta": round(float("$SCORE_AFTER") - float("$BASELINE"), 6)
}
Path("tmp/controller_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

# Phase: ARCHIVE
update_state "archive"

# Log result
$PYTHON <<PY
import json
import subprocess
from pathlib import Path

payload = {
  "iteration": $ITERATION,
  "hypothesis_id": "H-001",
  "status": "$DECISION",
  "decision_code": "$DECISION_CODE",
  "score_before": $BASELINE,
  "score_after": $SCORE_AFTER,
  "score_delta": round(float("$SCORE_AFTER") - float("$BASELINE"), 6),
  "tests_pass": "$TESTS_PASS",
  "constraints_ok": "true",
  "critic_severity": "low",
  "critic_recommendation": "$DECISION",
  "changed_files_count": 1,
  "change_summary": "placeholder iteration",
  "rollback_reason": "$ROLLBACK_REASON"
}

# Call log_result.py via stdin
subprocess.run(
  ["$PYTHON", "scripts/log_result.py"],
  input=json.dumps(payload).encode("utf-8"),
  check=False
)
PY

# Update memory via stdin
$PYTHON scripts/update_memory.py <<PY || true
{
  "iteration": $ITERATION,
  "status": "$DECISION",
  "decision_code": "$DECISION_CODE",
  "change_summary": "placeholder iteration",
  "rollback_reason": "$ROLLBACK_REASON"
}
PY

# Update decisions markdown
cat >> agent/DECISIONS.md <<EOF

## Iteration $ITERATION
- decision: $DECISION
- decision_code: $DECISION_CODE
- score_before: $BASELINE
- score_after: $SCORE_AFTER
- tests_pass: $TESTS_PASS
- change_summary: placeholder iteration
- rollback_reason: $ROLLBACK_REASON
EOF

update_state "done"
echo "[iteration $ITERATION] Completed"

exit 0
