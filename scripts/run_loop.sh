#!/usr/bin/env bash
set -euo pipefail

# Default values
MAX_ITERATIONS=10
TARGET_SCORE=""
MODE="single-agent"
STOP_ON_HOLD="true"
ALLOW_DIRTY="false"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --target-score)
      TARGET_SCORE="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    --stop-on-hold)
      STOP_ON_HOLD="$2"
      shift 2
      ;;
    --allow-dirty)
      ALLOW_DIRTY="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

mkdir -p tmp reports/iteration reports/final

echo "[loop] mode=$MODE max_iterations=$MAX_ITERATIONS"

# Check if working tree is clean
if [[ "$ALLOW_DIRTY" != "true" ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "[loop] Working tree is dirty. Commit or stash changes first."
    exit 1
  fi
fi

# Check baseline exists
if [[ ! -f "eval/baseline.json" ]]; then
  echo "[loop] Missing eval/baseline.json"
  exit 1
fi

# Load baseline
CURRENT_BASELINE="$(python3 -c 'import json; from pathlib import Path; print(json.loads(Path("eval/baseline.json").read_text(encoding="utf-8"))["score"])')"
echo "[loop] baseline=$CURRENT_BASELINE"

# Tracking variables
NO_IMPROVEMENT_STREAK=0
MAX_NO_IMPROVEMENT_STREAK=3

# Main loop
for ((i=1; i<=MAX_ITERATIONS; i++)); do
  echo
  echo "=================================================="
  echo "[loop] Iteration $i / $MAX_ITERATIONS"
  echo "=================================================="

  # Run iteration
  ITERATION_EXIT_CODE=0
  bash scripts/run_iteration.sh \
    --iteration "$i" \
    --mode "$MODE" \
    --baseline "$CURRENT_BASELINE" \
    || ITERATION_EXIT_CODE=$?

  if [[ "$ITERATION_EXIT_CODE" -ne 0 ]]; then
    echo "[loop] Iteration failed with exit code $ITERATION_EXIT_CODE"
    break
  fi

  # Read decision
  DECISION="$(python3 -c 'import json; from pathlib import Path; print(json.loads(Path("tmp/controller_result.json").read_text(encoding="utf-8"))["decision"])')"
  NEW_BASELINE="$(python3 -c 'import json; from pathlib import Path; print(json.loads(Path("eval/baseline.json").read_text(encoding="utf-8"))["score"])')"

  echo "[loop] decision=$DECISION baseline_now=$NEW_BASELINE"

  # Track improvement streak
  if python3 -c "import sys; new=float('$NEW_BASELINE'); old=float('$CURRENT_BASELINE'); sys.exit(0 if new > old else 1)"; then
    NO_IMPROVEMENT_STREAK=0
  else
    NO_IMPROVEMENT_STREAK=$((NO_IMPROVEMENT_STREAK + 1))
    echo "[loop] No improvement detected (streak: $NO_IMPROVEMENT_STREAK/$MAX_NO_IMPROVEMENT_STREAK)"
  fi

  CURRENT_BASELINE="$NEW_BASELINE"

  # Check target score
  if [[ -n "$TARGET_SCORE" ]]; then
    if python3 -c "target=float('$TARGET_SCORE'); current=float('$CURRENT_BASELINE'); import sys; sys.exit(0 if current >= target else 1)"; then
      echo "[loop] Target score reached: $CURRENT_BASELINE >= $TARGET_SCORE"
      break
    fi
  fi

  # Check stagnation
  if [[ "$NO_IMPROVEMENT_STREAK" -ge "$MAX_NO_IMPROVEMENT_STREAK" ]]; then
    echo "[loop] No improvement for $MAX_NO_IMPROVEMENT_STREAK consecutive iterations. Stopping."
    break
  fi
done

# Generate final report
echo "[loop] Generating final report..."
python3 scripts/make_final_report.py

echo "[loop] All iterations completed"
echo "Final baseline: $CURRENT_BASELINE"
