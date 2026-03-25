# run_loop.sh / run_iteration.sh 실전형 버전
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 반복개선 에이전트 시스템의 실제 실행 흐름을 담당하는
핵심 스크립트 설계를 상세히 정의한다.

대상:
- `scripts/run_loop.sh`
- `scripts/run_iteration.sh`
- 보조 스크립트 연동 방식
- 상태 파일 갱신 규칙
- accept / reject / rollback 흐름
- 결과 기록 규격
- 종료 조건

이 문서의 목표는 단순 설명이 아니라,
바로 구현 가능한 수준의 **실전형 셸 오케스트레이션 골격**을 제공하는 것이다.

---

## 1. 실행 구조 개요

전체 루프는 아래 순서로 동작한다.

```text
run_loop.sh
  ├─ 환경/상태 준비
  ├─ baseline 확인
  ├─ iteration budget 확인
  ├─ 반복:
  │    └─ run_iteration.sh
  │         ├─ 상태 로드
  │         ├─ hypothesis 선택
  │         ├─ plan 생성/검증
  │         ├─ 구현 실행
  │         ├─ tests 실행
  │         ├─ eval 실행
  │         ├─ critic 검토
  │         ├─ controller 결정
  │         ├─ accept 또는 rollback
  │         └─ memory / reports 갱신
  └─ 종료 시 final report 생성
2. 설계 원칙
2.1 run_loop.sh는 상위 오케스트레이터다

역할:

반복 횟수 관리
종료 조건 판단
iteration 실행
최종 보고서 생성
2.2 run_iteration.sh는 한 번의 실험 단위다

역할:

가설 1개
변경 1개
평가 1개
결정 1개
2.3 모든 판단은 파일과 구조화된 결과를 기반으로 한다

즉:

stdout 문장 파싱에 과도하게 의존하지 않는다
가능한 JSON 파일을 남긴다
TSV는 append-only로 관리한다
2.4 실패는 정상 흐름이다

테스트 실패, score regression, constraint 위반은
예외가 아니라 reject 흐름의 일부다.

2.5 롤백은 선택이 아니라 기본 경로다

accept 되기 전까지 모든 변경은 임시 변경이다.

3. 필수 입출력 파일

실행 스크립트는 아래 파일을 사용한다.

입력 파일
agent/PRODUCT_GOAL.md
agent/TASK.md
agent/RULES.md
agent/MEMORY.md
agent/HYPOTHESES.md
agent/PLAN.md
agent/ITERATION_STATE.json
eval/baseline.json
중간 결과 파일
tmp/explorer_result.json
tmp/planner_result.json
tmp/implementer_result.json
tmp/tests_result.json
tmp/eval_result.json
tmp/critic_result.json
tmp/controller_result.json
출력 파일
agent/RESULTS.tsv
agent/DECISIONS.md
agent/MEMORY.md
reports/iteration/iteration-XXX.md
reports/final/final_report.md
4. 디렉토리/도구 전제조건
필수 디렉토리
tmp/
reports/iteration/
reports/final/
agent/
eval/
scripts/
필수 도구
bash
python
git
jq 권장
pytest 권장
권장 조건
working tree가 깨끗한 상태에서 시작
baseline이 존재
tests 또는 최소 eval이 동작 가능
forbidden path 보호 정책 적용
5. 상태 머신 정의

한 iteration은 아래 상태를 가진다.

INIT
READ_CONTEXT
EXPLORE
PLAN
IMPLEMENT
RUN_TESTS
RUN_EVAL
CRITIQUE
DECIDE
ACCEPT | REJECT
ROLLBACK
ARCHIVE
DONE
ERROR
상태별 의미
INIT
환경과 필수 파일 존재 여부 확인
READ_CONTEXT
현재 목표/규칙/기억/기준 점수 로드
EXPLORE
새 hypothesis 생성 또는 기존 hypothesis 중 선택
PLAN
hypothesis를 작은 작업으로 변환
IMPLEMENT
실제 코드/문서 수정
RUN_TESTS
테스트 실행
RUN_EVAL
frozen eval 및 constraints 실행
CRITIQUE
narrow win / regression / scope 위반 검토
DECIDE
accept / reject / hold 판단
ACCEPT
commit + baseline 업데이트 + 기록
REJECT
reject 기록
ROLLBACK
working tree 복구
ARCHIVE
결과 로그/메모리/iteration report 갱신
DONE
iteration 완료
ERROR
중간 치명 오류 발생
6. run_loop.sh 상세 설계
6.1 책임
전체 루프 실행
iteration budget 관리
stop condition 판단
stagnation 감지
final report 생성
6.2 입력 인자

권장 인자:

--max-iterations
--target-score
--mode
--stop-on-hold
--allow-dirty (기본 false)

예:

bash scripts/run_loop.sh --max-iterations 10 --target-score 0.80 --mode single-agent
6.3 종료 조건

다음 중 하나면 종료:

iteration 수가 max 도달
baseline score가 target-score 이상
최근 N회 연속 개선 없음
controller가 hold + manual review 판단
치명적 오류 발생
6.4 권장 상위 의사코드
prepare directories
validate repo state
load baseline
for i in 1..max_iterations:
    run iteration
    inspect result
    if target reached: break
    if stagnation detected: break
    if fatal error: break
generate final report
7. run_iteration.sh 상세 설계
7.1 책임
한 번의 hypothesis 검증 사이클을 끝까지 수행
7.2 입력
현재 baseline
iteration number
운영 모드
목표/규칙/기억 파일
7.3 출력
controller decision
updated state
result row appended
iteration report 생성
baseline 업데이트 여부
7.4 핵심 원칙
한 iteration = 한 hypothesis = 한 핵심 변경
tests/eval/critic/controller를 모두 거친 후에만 accept 가능
중간 실패는 reject + rollback으로 수렴시킨다
8. 실전형 파일 규격
8.1 tmp/tests_result.json

예:

{
  "passed": true,
  "summary": "24 passed, 0 failed",
  "failed_tests": [],
  "duration_sec": 3.21
}
8.2 tmp/eval_result.json

예:

{
  "score": 0.756,
  "tests_pass": true,
  "constraints_ok": true,
  "latency_ms": 118,
  "latency_delta_pct": 2.1,
  "regressions": [],
  "notes": ["punctuation-heavy queries improved"]
}
8.3 tmp/controller_result.json

예:

{
  "decision": "accept",
  "reason": "score improved and no major regressions were found",
  "next_action": "archive_and_continue"
}
9. run_loop.sh 실전형 초안

파일: scripts/run_loop.sh

#!/usr/bin/env bash
set -euo pipefail

MAX_ITERATIONS=10
TARGET_SCORE=""
MODE="single-agent"
STOP_ON_HOLD="true"
ALLOW_DIRTY="false"

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

if [[ "$ALLOW_DIRTY" != "true" ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "[loop] Working tree is dirty. Commit or stash changes first."
    exit 1
  fi
fi

if [[ ! -f "eval/baseline.json" ]]; then
  echo "[loop] Missing eval/baseline.json"
  exit 1
fi

CURRENT_BASELINE="$(python - <<'PY'
import json
from pathlib import Path
p = Path("eval/baseline.json")
data = json.loads(p.read_text(encoding="utf-8"))
print(data["score"])
PY
)"

echo "[loop] baseline=$CURRENT_BASELINE"

NO_IMPROVEMENT_STREAK=0
MAX_NO_IMPROVEMENT_STREAK=3

for ((i=1; i<=MAX_ITERATIONS; i++)); do
  echo
  echo "=================================================="
  echo "[loop] Iteration $i / $MAX_ITERATIONS"
  echo "=================================================="

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

  DECISION="$(python - <<'PY'
import json
from pathlib import Path
p = Path("tmp/controller_result.json")
data = json.loads(p.read_text(encoding="utf-8"))
print(data["decision"])
PY
)"

  NEW_BASELINE="$(python - <<'PY'
import json
from pathlib import Path
p = Path("eval/baseline.json")
data = json.loads(p.read_text(encoding="utf-8"))
print(data["score"])
PY
)"

  echo "[loop] decision=$DECISION"
  echo "[loop] baseline_now=$NEW_BASELINE"

  if python - <<PY
old=float("$CURRENT_BASELINE")
new=float("$NEW_BASELINE")
import sys
sys.exit(0 if new > old else 1)
PY
  then
    NO_IMPROVEMENT_STREAK=0
  else
    NO_IMPROVEMENT_STREAK=$((NO_IMPROVEMENT_STREAK + 1))
  fi

  CURRENT_BASELINE="$NEW_BASELINE"

  if [[ -n "$TARGET_SCORE" ]]; then
    if python - <<PY
target=float("$TARGET_SCORE")
current=float("$CURRENT_BASELINE")
import sys
sys.exit(0 if current >= target else 1)
PY
    then
      echo "[loop] Target score reached: $CURRENT_BASELINE >= $TARGET_SCORE"
      break
    fi
  fi

  if [[ "$DECISION" == "hold" && "$STOP_ON_HOLD" == "true" ]]; then
    echo "[loop] Stopping because controller returned hold."
    break
  fi

  if [[ "$NO_IMPROVEMENT_STREAK" -ge "$MAX_NO_IMPROVEMENT_STREAK" ]]; then
    echo "[loop] Stopping because no improvement streak reached $MAX_NO_IMPROVEMENT_STREAK."
    break
  fi
done

echo "[loop] Generating final report..."
python scripts/make_final_report.py

echo "[loop] Done."
10. run_iteration.sh 실전형 초안

파일: scripts/run_iteration.sh

#!/usr/bin/env bash
set -euo pipefail

ITERATION=""
MODE="single-agent"
BASELINE=""

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

if [[ -z "$ITERATION" || -z "$BASELINE" ]]; then
  echo "[iteration] Missing required arguments."
  exit 1
fi

mkdir -p tmp reports/iteration

echo "[iteration] start iteration=$ITERATION mode=$MODE baseline=$BASELINE"

update_state_phase() {
  local phase="$1"
  python - <<PY
import json
from pathlib import Path
p = Path("agent/ITERATION_STATE.json")
data = json.loads(p.read_text(encoding="utf-8"))
data["iteration"] = int("$ITERATION")
data["mode"] = "$MODE"
data["phase"] = "$phase"
data["baseline_score"] = float("$BASELINE")
data["last_updated"] = "2026-03-25T00:00:00Z"
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

write_iteration_report() {
  local path="reports/iteration/iteration-$(printf "%03d" "$ITERATION").md"
  cat > "$path" <<EOF
# Iteration $ITERATION

- mode: $MODE
- baseline: $BASELINE

## Files
- tmp/tests_result.json
- tmp/eval_result.json
- tmp/critic_result.json
- tmp/controller_result.json
EOF
}

update_state_phase "read_context"

echo "[iteration] validate required files"
for f in \
  agent/PRODUCT_GOAL.md \
  agent/TASK.md \
  agent/RULES.md \
  agent/MEMORY.md \
  agent/HYPOTHESES.md \
  agent/PLAN.md \
  agent/ITERATION_STATE.json \
  eval/frozen_eval.py \
  eval/baseline.json
do
  if [[ ! -f "$f" ]]; then
    echo "[iteration] missing file: $f"
    exit 1
  fi
done

echo "[iteration] checkpoint: git working tree"
git status --short

update_state_phase "explore"

echo "[iteration] explore step"
python - <<'PY'
import json
from pathlib import Path

result = {
  "hypotheses": [
    {
      "id": "H-001",
      "title": "normalize punctuation in queries",
      "description": "remove or normalize punctuation before tokenization",
      "expected_effect": "improve recall for punctuation-heavy queries",
      "risk": "minor precision drop",
      "priority": "high"
    }
  ]
}
Path("tmp/explorer_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

update_state_phase "plan"

echo "[iteration] planning step"
python - <<'PY'
import json
from pathlib import Path

result = {
  "selected_hypothesis": "H-001",
  "change_scope": ["src/search/normalize.py"],
  "planned_change": "normalize punctuation before tokenization",
  "expected_effect": "small recall improvement",
  "risks": ["precision drop", "over-normalization"],
  "tests_to_run": [
    "bash scripts/run_tests.sh",
    "bash scripts/run_eval.sh"
  ],
  "reject_conditions": [
    "tests fail",
    "score regression",
    "latency increase > 5%"
  ]
}
Path("tmp/planner_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY

update_state_phase "implement"

echo "[iteration] implement step"
# 실제 운영에서는 여기서 Codex CLI 호출 또는 MCP 기반 편집이 들어간다.
