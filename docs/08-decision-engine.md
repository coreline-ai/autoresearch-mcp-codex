# 초기 실전형 문서에서는 placeholder 결과 파일 생성으로 구조를 유지한다.
python - <<'PY'
import json
from pathlib import Path

result = {
  "changed_files": ["src/search/normalize.py"],
  "change_summary": "applied focused punctuation normalization logic",
  "why_this_change": "should improve matching consistency for punctuation-heavy queries",
  "verification_commands_run": [],
  "notes": ["placeholder implementer result"]
}
Path("tmp/implementer_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

update_state_phase "run_tests"

echo "[iteration] run tests"
TESTS_EXIT_CODE=0
if bash scripts/run_tests.sh > tmp/tests_stdout.txt 2> tmp/tests_stderr.txt; then
  python - <<'PY'
import json
from pathlib import Path
result = {
  "passed": True,
  "summary": "tests passed",
  "failed_tests": [],
  "duration_sec": 0.0
}
Path("tmp/tests_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
else
  TESTS_EXIT_CODE=$?
  python - <<'PY'
import json
from pathlib import Path
stderr = Path("tmp/tests_stderr.txt").read_text(encoding="utf-8", errors="ignore") if Path("tmp/tests_stderr.txt").exists() else ""
result = {
  "passed": False,
  "summary": "tests failed",
  "failed_tests": [],
  "duration_sec": 0.0,
  "stderr": stderr[-4000:]
}
Path("tmp/tests_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
fi

update_state_phase "run_eval"

echo "[iteration] run eval"
EVAL_EXIT_CODE=0
if bash scripts/run_eval.sh > tmp/eval_stdout.txt 2> tmp/eval_stderr.txt; then
  cp tmp/eval_stdout.txt tmp/eval_result.json
else
  EVAL_EXIT_CODE=$?
  python - <<'PY'
import json
from pathlib import Path
stderr = Path("tmp/eval_stderr.txt").read_text(encoding="utf-8", errors="ignore") if Path("tmp/eval_stderr.txt").exists() else ""
result = {
  "score": 0.0,
  "tests_pass": False,
  "constraints_ok": False,
  "latency_ms": None,
  "latency_delta_pct": None,
  "regressions": ["eval execution failed"],
  "notes": [stderr[-4000:]]
}
Path("tmp/eval_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
fi

update_state_phase "critique"

echo "[iteration] critique step"
python - <<PY
import json
from pathlib import Path

eval_result = json.loads(Path("tmp/eval_result.json").read_text(encoding="utf-8"))
tests_result = json.loads(Path("tmp/tests_result.json").read_text(encoding="utf-8"))

objections = []
severity = "low"
recommendation = "accept"

if not tests_result.get("passed", False):
    severity = "high"
    recommendation = "reject"
    objections.append("tests failed")

score = float(eval_result.get("score", 0.0))
baseline = float("$BASELINE")
if score <= baseline:
    severity = "high"
    recommendation = "reject"
    objections.append(f"score did not improve: {score} <= {baseline}")

if not eval_result.get("constraints_ok", True):
    severity = "high"
    recommendation = "reject"
    objections.append("constraints check failed")

result = {
    "severity": severity,
    "objections": objections,
    "recommendation": recommendation,
    "reasoning": "automatic critic review based on tests/eval/constraints"
}

Path("tmp/critic_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

update_state_phase "decide"

echo "[iteration] controller decision"
python - <<PY
import json
from pathlib import Path

eval_result = json.loads(Path("tmp/eval_result.json").read_text(encoding="utf-8"))
tests_result = json.loads(Path("tmp/tests_result.json").read_text(encoding="utf-8"))
critic_result = json.loads(Path("tmp/critic_result.json").read_text(encoding="utf-8"))

baseline = float("$BASELINE")
score = float(eval_result.get("score", 0.0))

decision = "accept"
reason = "score improved and checks passed"
next_action = "archive_and_continue"

if not tests_result.get("passed", False):
    decision = "reject"
    reason = "tests failed"
    next_action = "rollback_and_continue"
elif not eval_result.get("constraints_ok", True):
    decision = "reject"
    reason = "constraints failed"
    next_action = "rollback_and_continue"
elif score <= baseline:
    decision = "reject"
    reason = f"score did not improve ({score} <= {baseline})"
    next_action = "rollback_and_continue"
elif critic_result.get("severity") == "high" and critic_result.get("recommendation") == "reject":
    decision = "reject"
    reason = "critic found blocking issue"
    next_action = "rollback_and_continue"

result = {
    "decision": decision,
    "reason": reason,
    "next_action": next_action
}

Path("tmp/controller_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

DECISION="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("tmp/controller_result.json").read_text(encoding="utf-8"))
print(data["decision"])
PY
)"

REASON="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("tmp/controller_result.json").read_text(encoding="utf-8"))
print(data["reason"])
PY
)"

SCORE_AFTER="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("tmp/eval_result.json").read_text(encoding="utf-8"))
print(data.get("score", 0.0))
PY
)"

TESTS_PASS="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("tmp/tests_result.json").read_text(encoding="utf-8"))
print(str(data.get("passed", False)).lower())
PY
)"

CONSTRAINTS_OK="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("tmp/eval_result.json").read_text(encoding="utf-8"))
print(str(data.get("constraints_ok", False)).lower())
PY
)"

SCORE_DELTA="$(python - <<PY
baseline=float("$BASELINE")
after=float("$SCORE_AFTER")
print(round(after-baseline, 6))
PY
)"

CHANGE_SUMMARY="$(python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("tmp/implementer_result.json").read_text(encoding="utf-8"))
print(data.get("change_summary", ""))
PY
)"

if [[ "$DECISION" == "accept" ]]; then
  update_state_phase "accept"

  echo "[iteration] accept change"
  bash scripts/accept_change.sh "accepted iteration $ITERATION"

  python - <<PY
import json
from pathlib import Path
p = Path("eval/baseline.json")
data = json.loads(p.read_text(encoding="utf-8"))
data["score"] = float("$SCORE_AFTER")
data["iteration"] = int("$ITERATION")
data["measured_at"] = "2026-03-25T00:00:00Z"
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
PY

  ROLLBACK_REASON=""
else
  update_state_phase "reject"

  echo "[iteration] reject change"
  ROLLBACK_REASON="$REASON"

  update_state_phase "rollback"
  bash scripts/rollback_change.sh
fi

update_state_phase "archive"

echo "[iteration] append decision log"
cat >> agent/DECISIONS.md <<EOF

## Iteration $ITERATION
- decision: $DECISION
- reason: $REASON
- score_before: $BASELINE
- score_after: $SCORE_AFTER
- score_delta: $SCORE_DELTA
- tests_pass: $TESTS_PASS
- constraints_ok: $CONSTRAINTS_OK
- change_summary: $CHANGE_SUMMARY
EOF

python scripts/log_result.py \
  "$ITERATION" \
  "H-001" \
  "$DECISION" \
  "$BASELINE" \
  "$SCORE_AFTER" \
  "$SCORE_DELTA" \
  "$TESTS_PASS" \
  "$CONSTRAINTS_OK" \
  "$CHANGE_SUMMARY" \
  "$ROLLBACK_REASON"

python scripts/update_memory.py || true

write_iteration_report

update_state_phase "done"

echo "[iteration] completed with decision=$DECISION"
exit 0
11. accept / reject / rollback 상세 흐름
11.1 Accept 경로

조건:

tests_pass = true
constraints_ok = true
score_after > baseline
critic severe objection 없음

수행 작업:

git add .
git commit -m "accepted iteration N"
eval/baseline.json 업데이트
RESULTS.tsv append
DECISIONS.md append
MEMORY.md 갱신
iteration report 저장
11.2 Reject 경로

조건:

tests fail
constraints fail
score regression
controller reject
critic severe warning

수행 작업:

reject reason 결정
rollback 수행
RESULTS.tsv append
DECISIONS.md append
MEMORY.md 갱신
iteration report 저장
11.3 Hold 경로

초기 버전에서는 선택적이다.

도입 시 조건:

score는 개선되었지만 회귀 가능성이 높음
scope를 벗어난 변경이 포함됨
manual review가 필요함

초기 MVP에서는
hold는 사실상 reject 또는 루프 중단으로 처리해도 충분하다.

12. scripts/run_tests.sh 구조화 버전

기존 단순 버전을 구조화 결과 중심으로 보강한 권장안이다.

#!/usr/bin/env bash
set -euo pipefail

mkdir -p tmp

START_TS="$(python - <<'PY'
import time
print(time.time())
PY
)"

EXIT_CODE=0
STDOUT_FILE="tmp/tests_stdout.txt"
STDERR_FILE="tmp/tests_stderr.txt"

if [ -d "tests" ]; then
  pytest tests -q > "$STDOUT_FILE" 2> "$STDERR_FILE" || EXIT_CODE=$?
else
  echo "No tests directory found; skipping tests" > "$STDOUT_FILE"
  : > "$STDERR_FILE"
fi

END_TS="$(python - <<'PY'
import time
print(time.time())
PY
)"

python - <<PY
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
13. scripts/run_eval.sh 구조화 버전
#!/usr/bin/env bash
set -euo pipefail

mkdir -p tmp

STDOUT_FILE="tmp/eval_stdout.txt"
STDERR_FILE="tmp/eval_stderr.txt"
EXIT_CODE=0

python eval/frozen_eval.py > "$STDOUT_FILE" 2> "$STDERR_FILE" || EXIT_CODE=$?

if [[ "$EXIT_CODE" -ne 0 ]]; then
  python - <<'PY'
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
14. scripts/accept_change.sh 권장 강화판
#!/usr/bin/env bash
set -euo pipefail

MESSAGE="${1:-accepted iteration change}"

if [[ -n "$(git status --porcelain)" ]]; then
  git add .
  git commit -m "$MESSAGE"
  echo "Accepted and committed: $MESSAGE"
else
  echo "No changes to commit."
fi
15. scripts/rollback_change.sh 권장 강화판
#!/usr/bin/env bash
set -euo pipefail

git restore .
git clean -fd
echo "Rollback completed"

운영 환경에 따라 더 안전하게 하려면:

worktree snapshot
temp branch
iteration branch 분기
등을 사용할 수 있다.
16. iteration report 상세 규격

파일:

reports/iteration/iteration-001.md

권장 내용:

baseline
selected hypothesis
changed files
tests 결과
eval 결과
critic 요약
controller 결정
rollback 여부

예시 포맷:

# Iteration 1

## Summary
- decision: accept
- baseline_before: 0.70
- score_after: 0.756
- score_delta: 0.056

## Hypothesis
- H-001: normalize punctuation in queries

## Changed Files
- src/search/normalize.py

## Tests
- passed: true

## Eval
- constraints_ok: true
- latency_delta_pct: 2.1

## Critic
- severity: low
- recommendation: accept

## Controller
- reason: score improved and checks passed
17. stagnation 감지 로직

루프가 무한히 도는 것을 막기 위해
상위 루프에서 stagnation을 감지해야 한다.

권장 기준
최근 3회 연속 baseline 미개선
최근 5회 중 accept 비율이 지나치게 낮음
같은 유형의 hypothesis가 반복 reject
구현 위치
run_loop.sh
기본 정책
NO_IMPROVEMENT_STREAK >= 3 이면 종료
18. 실제 Codex CLI 연결 지점

현재 초안에서는 implement 단계가 placeholder다.
실제 구현 시 이 부분이 교체된다.

연결 위치

run_iteration.sh 의 implement step

연결 개념
1. planner_result.json 준비
2. implementer prompt 준비
3. Codex CLI 호출
4. 변경 파일/요약 결과 수집
5. tests/eval 진행
중요 원칙
Codex CLI 호출 결과를 바로 accept하지 않는다
항상 tests/eval/critic/controller를 통과해야 한다
Codex는 실행 주체이지 심판이 아니다
19. 오류 처리 전략
19.1 필수 파일 누락

동작:

즉시 종료
iteration 실패 처리
19.2 tests 실행 실패

동작:

reject
rollback
stderr 저장
19.3 eval 실행 실패

동작:

reject
rollback
eval_result.json에 failure 구조 저장
19.4 git rollback 실패

동작:

loop 중단 권장
manual intervention 필요 표시
19.5 JSON 파싱 실패

동작:

해당 단계 실패로 간주
reject 또는 loop 중단
20. 확장 포인트

현재 문서는 bash 기반 최소 오케스트레이션이다.
실전 고도화 시 다음으로 확장할 수 있다.

20.1 Python 오케스트레이터 전환

장점:

JSON 처리 쉬움
상태 머신 관리 쉬움
로그 구조화 쉬움
20.2 브랜치 기반 candidate 비교
candidate branch 생성
accept 시 squash merge
reject 시 branch 폐기
20.3 parallel hypothesis sandbox
여러 hypothesis를 분리 브랜치에서 실험
accept는 단일 controller만 수행
20.4 UI / 대시보드
baseline 추이
accept/reject 히스토리
hypothesis 상태
rollback 횟수
21. 최소 동작 보장 체크리스트

실행 전 체크:

 eval/frozen_eval.py 동작
 eval/baseline.json 존재
 agent/RESULTS.tsv 헤더 생성
 agent/ITERATION_STATE.json 초기화
 git repo 초기화됨
 tests 최소 1개 이상 또는 skip 가능
 tmp/ 생성 가능
 scripts/log_result.py 동작
22. 핵심 요약

이 문서의 핵심은 다음이다.

run_loop.sh는 전체 반복을 통제한다
run_iteration.sh는 한 번의 실험을 끝까지 수행한다
tests/eval/critic/controller를 거친 후에만 accept 가능하다
reject는 즉시 rollback한다
모든 결과는 TSV/JSON/Markdown으로 남긴다
baseline은 accept된 결과만 반영한다

즉 이 구조만 제대로 구현되면,
시스템은 최소한 다음 루프를 신뢰성 있게 돌릴 수 있다.

작은 변경
→ 테스트
→ 평가
→ 비판
→ 승인/거절
→ 롤백 또는 유지
→ 기록
→ 반복

```md
# 다음 단계 문서 4
