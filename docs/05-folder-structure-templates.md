# 다음 단계 문서 1
# 폴더별 실제 파일 초안
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 바로 구현에 들어갈 수 있도록
실제 프로젝트에 생성할 파일들의 초안을 제공한다.

이번 문서 범위:
1. 폴더 구조
2. 핵심 파일 초안
3. 각 파일의 실제 텍스트 샘플
4. 최소 실행 가능한 형태의 시작점

주의:
- 이 문서는 "설명용"이 아니라 "바로 복붙 가능한 초안"에 가깝게 작성한다.
- 초기 버전은 과도한 멀티 에이전트보다, **단일 실행 루프 + 역할 프롬프트 분리**를 우선한다.
- `frozen eval` 관련 파일은 절대 수정 금지 규칙을 전제로 한다.

---

## 1. 권장 폴더 구조

```text
autoresearch-agent/
├─ src/
├─ tests/
├─ eval/
│  ├─ frozen_eval.py
│  ├─ fixtures.json
│  ├─ rubric.md
│  ├─ baseline.json
│  └─ constraints.py
├─ agent/
│  ├─ PRODUCT_GOAL.md
│  ├─ TASK.md
│  ├─ RULES.md
│  ├─ MEMORY.md
│  ├─ HYPOTHESES.md
│  ├─ PLAN.md
│  ├─ ITERATION_STATE.json
│  ├─ RESULTS.tsv
│  └─ DECISIONS.md
├─ prompts/
│  ├─ controller.md
│  ├─ explorer.md
│  ├─ planner.md
│  ├─ implementer.md
│  ├─ critic.md
│  └─ archivist.md
├─ scripts/
│  ├─ run_loop.sh
│  ├─ run_iteration.sh
│  ├─ run_tests.sh
│  ├─ run_eval.sh
│  ├─ accept_change.sh
│  ├─ rollback_change.sh
│  ├─ log_result.py
│  ├─ update_memory.py
│  └─ make_final_report.py
├─ mcp/
│  ├─ servers.json
│  ├─ capabilities.json
│  └─ tool-policies.md
├─ reports/
│  ├─ iteration/
│  └─ final/
├─ tmp/
└─ README.md
2. 루트 README.md 초안

파일: README.md

# AutoResearch Agent System

반복 개선형 에이전트 시스템

핵심 개념:
- 목표를 정의한다
- 작은 변경을 수행한다
- frozen eval로 측정한다
- 좋아지면 유지한다
- 나빠지면 롤백한다
- 결과를 기억으로 축적한다

## 주요 디렉토리

- `agent/` : 목표, 규칙, 메모리, 계획, 결과 로그
- `eval/` : frozen eval 및 평가 기준
- `prompts/` : 역할별 프롬프트
- `scripts/` : 실행 스크립트
- `mcp/` : MCP 연결 및 정책
- `reports/` : iteration / final 결과 리포트

## 기본 실행 흐름

1. 목표 설정
2. baseline 측정
3. hypothesis 생성
4. 작은 수정 적용
5. 테스트 + eval 실행
6. accept / reject
7. 결과 기록
8. 반복

## 매우 중요한 원칙

- `eval/frozen_eval.py` 수정 금지
- `eval/fixtures.json` 수정 금지
- 한 iteration 당 하나의 핵심 변경만 허용
- tests 실패 시 reject
- score 미개선 시 reject
3. agent 폴더 파일 초안
3.1 agent/PRODUCT_GOAL.md
# PRODUCT GOAL

## 목표
검색 relevance를 baseline 대비 유의미하게 개선한다.

## 성공 조건
- frozen eval score를 현재 baseline보다 높인다.
- tests는 모두 통과해야 한다.
- latency 증가는 5% 이내여야 한다.
- public API는 변경하지 않는다.

## 우선순위
1. relevance 개선
2. regression 방지
3. latency budget 준수
4. 코드 변경 범위 최소화

## 금지사항
- frozen eval 수정 금지
- fixtures 수정 금지
- 근거 없는 대규모 리팩터링 금지
- 전체 구조를 한 번에 갈아엎는 변경 금지
3.2 agent/TASK.md
# CURRENT TASK

## 현재 집중 문제
사용자 검색 query 전처리를 개선하여 recall을 높인다.

## 이번 cycle 목표
- punctuation normalization이 relevance에 도움이 되는지 검증한다.

## 변경 범위
- query normalization 관련 코드만 수정한다.
- 검색 파이프라인 전체 구조는 변경하지 않는다.

## 이번 cycle 성공 기준
- frozen eval score가 baseline보다 상승
- tests 통과
- latency 증가 5% 이하

## 제외 범위
- synonym expansion
- reranker 구조 변경
- DB schema 변경
3.3 agent/RULES.md
# OPERATING RULES

## 절대 규칙
1. `eval/frozen_eval.py` 수정 금지
2. `eval/fixtures.json` 수정 금지
3. `eval/baseline.json` 임의 수정 금지
4. 한 iteration당 하나의 핵심 변경만 허용
5. tests 실패 시 무조건 reject
6. score 미개선 시 무조건 reject
7. 변경 이유를 반드시 요약 기록
8. 실패 이유도 반드시 기록

## 변경 범위 규칙
- 가능하면 하나 또는 소수의 관련 파일만 수정
- 대규모 rename 금지
- 불필요한 formatting-only diff 금지
- speculative cleanup 금지

## 안전 규칙
- destructive shell command 금지
- production 자원 접근 금지
- dependency upgrade는 별도 승인 전까지 금지

## 품질 규칙
- diff는 작고 설명 가능해야 한다
- rollback 가능성이 항상 확보되어야 한다
- accepted change만 baseline으로 승격할 수 있다
3.4 agent/MEMORY.md
# MEMORY

## Accepted Patterns
- query normalization은 일반적으로 recall 개선 가능성이 있다.
- 작은 전처리 변경은 낮은 비용으로 실험하기 좋다.

## Rejected Patterns
- 공격적인 synonym expansion은 false positive를 크게 늘릴 수 있다.
- 너무 많은 전처리를 한 번에 추가하면 원인 추적이 어려워진다.

## Known Risks
- punctuation normalization은 일부 precision 저하를 유발할 수 있다.
- latency budget은 무제한이 아니다.

## Strategy Notes
- 먼저 작은 전처리 개선부터 시도한다.
- 구조 변경보다 저위험 변경을 우선한다.
- 한 iteration 당 하나의 가설만 검증한다.
3.5 agent/HYPOTHESES.md
# HYPOTHESES

- H-001
  - title: normalize punctuation in queries
  - expected_effect: recall improvement
  - risk: minor precision drop
  - priority: high
  - status: selected

- H-002
  - title: lowercase normalization before tokenization
  - expected_effect: improve match consistency
  - risk: low
  - priority: high
  - status: proposed

- H-003
  - title: aggressive synonym expansion
  - expected_effect: recall improvement
  - risk: false positives
  - priority: medium
  - status: parked
3.6 agent/PLAN.md
# PLAN

## Selected Hypothesis
H-001: normalize punctuation in queries

## Change Scope
- `src/search/normalize.py`
- 필요 시 관련 테스트 파일 최소 범위 수정

## Planned Change
- query 입력에서 punctuation을 제거 또는 normalize한다.
- tokenization 이전 단계에서만 수행한다.
- API surface는 변경하지 않는다.

## Expected Effect
- punctuation variation이 있는 query에서 match consistency 개선
- recall 소폭 상승 기대

## Risks
- precision이 약간 떨어질 수 있음
- 일부 fixture에서 의미 있는 punctuation까지 제거될 위험

## Tests To Run
1. unit tests
2. search 관련 integration tests
3. frozen eval
4. constraints check

## Reject Conditions
- tests fail
- score regression
- latency increase > 5%
- diff 범위 과도
3.7 agent/ITERATION_STATE.json
{
  "iteration": 1,
  "mode": "single-agent-with-role-prompts",
  "phase": "init",
  "selected_hypothesis": "H-001",
  "baseline_score": 0.0,
  "candidate_score": null,
  "tests_pass": null,
  "constraints_ok": null,
  "decision": null,
  "last_updated": "2026-03-25T00:00:00Z"
}
3.8 agent/RESULTS.tsv
iteration	hypothesis_id	status	score_before	score_after	score_delta	tests_pass	constraints_ok	change_summary	rollback_reason
3.9 agent/DECISIONS.md
# DECISIONS

## Iteration 1
- hypothesis: H-001
- status: pending
- decision_reason: not evaluated yet
4. eval 폴더 파일 초안
4.1 eval/rubric.md
# EVAL RUBRIC

## 목적
검색 relevance 품질을 고정된 기준으로 측정한다.

## 핵심 원칙
- 동일 입력 세트 사용
- 동일 채점 기준 사용
- iteration 중 수정 금지

## 평가 항목
1. 정답 문서/결과를 상위에 노출하는가
2. 관련 없는 결과를 과도하게 끌어오지 않는가
3. query variation에 robust한가

## 점수 범위
- 0.0 ~ 1.0

## 해석
- baseline보다 score가 높아야 accept 후보가 된다.
- tests와 constraints를 함께 만족해야 최종 accept 가능하다.
4.2 eval/fixtures.json
[
  {
    "id": "Q-001",
    "query": "wireless-mouse!!",
    "expected_keywords": ["wireless", "mouse"],
    "description": "punctuation-heavy product query"
  },
  {
    "id": "Q-002",
    "query": "USB-C cable???",
    "expected_keywords": ["usb", "c", "cable"],
    "description": "mixed punctuation query"
  },
  {
    "id": "Q-003",
    "query": "bluetooth speaker",
    "expected_keywords": ["bluetooth", "speaker"],
    "description": "normal baseline query"
  }
]
4.3 eval/baseline.json
{
  "score": 0.70,
  "measured_at": "2026-03-25T00:00:00Z",
  "iteration": 0
}
4.4 eval/constraints.py
from __future__ import annotations

import json
import sys


def main() -> int:
    """
    실제 프로젝트에서는 latency, memory, resource usage 등을 확인한다.
    초기 버전은 always-pass 형태로 시작할 수 있다.
    """
    result = {
        "constraints_ok": True,
        "latency_ms": 100,
        "latency_delta_pct": 0.0,
        "notes": ["initial placeholder constraints check"]
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
4.5 eval/frozen_eval.py
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXTURES_PATH = ROOT / "fixtures.json"


def normalize_query(query: str) -> list[str]:
    """
    실제 프로젝트에서는 src 코드 결과를 호출해야 한다.
    초기 샘플에서는 매우 단순한 토큰 분리만 수행한다.
    """
    cleaned = []
    for ch in query.lower():
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    tokens = [t for t in "".join(cleaned).split() if t]
    return tokens


def score_fixture(item: dict) -> float:
    tokens = set(normalize_query(item["query"]))
    expected = set(item["expected_keywords"])
    if not expected:
        return 0.0
    matched = len(tokens & expected)
    return matched / len(expected)


def main() -> int:
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    scores = [score_fixture(item) for item in fixtures]
    final_score = sum(scores) / len(scores) if scores else 0.0

    result = {
        "score": round(final_score, 4),
        "tests_pass": True,
        "constraints_ok": True,
        "latency_ms": 100,
        "latency_delta_pct": 0.0,
        "regressions": [],
        "notes": ["sample frozen eval completed"]
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
5. prompts 폴더 초안

이번 문서에서는 간단 버전만 포함한다.
다음 단계 문서에서 역할 프롬프트를 더 상세히 확장한다.

5.1 prompts/controller.md
You are the Controller.

Your job:
- read PRODUCT_GOAL.md, TASK.md, RULES.md, MEMORY.md, PLAN.md
- decide whether the latest change should be accepted or rejected
- prefer safety and evidence over speculation
- only accept if tests pass, constraints pass, and score improves

Do not:
- ignore regressions
- accept large unexplained changes
- modify frozen eval rules
5.2 prompts/explorer.md
You are the Explorer.

Your job:
- propose a few promising hypotheses
- use MEMORY.md and RESULTS.tsv to avoid repeating failed ideas
- prefer concrete, testable ideas
- include expected effect and risk

Do not:
- propose giant rewrites
- propose untestable changes
5.3 prompts/planner.md
You are the Planner.

Your job:
- take one selected hypothesis
- convert it into one small, testable iteration plan
- define change scope, expected effect, risks, tests, and reject conditions

Do not:
- combine multiple major changes in one iteration
- create vague plans
5.4 prompts/implementer.md
You are the Implementer.

Your job:
- make one focused change based on PLAN.md
- keep the diff small
- do not modify frozen eval files
- run required tests and evaluation commands after editing
- summarize exactly what changed

Do not:
- make speculative broad refactors
- touch forbidden files
- hide failures
5.5 prompts/critic.md
You are the Critic.

Your job:
- challenge the apparent success of a change
- look for regressions, overfitting, narrow wins, and hidden costs
- provide evidence-based objections

Do not:
- reject everything by default
- use vague opinions without evidence
5.6 prompts/archivist.md
You are the Archivist.

Your job:
- summarize what was tried
- update memory with short, reusable lessons
- keep logs concise and actionable

Do not:
- write long narratives
- copy raw transcripts into memory
6. mcp 폴더 파일 초안
6.1 mcp/tool-policies.md
# TOOL POLICIES

## Allowed by default
- filesystem read/write inside workspace
- shell test commands
- git status
- git diff
- git restore
- git commit

## Restricted
- deleting large numbers of files
- dependency upgrades
- schema changes
- external network access
- production resource access

## Never allowed
- modifying frozen eval files as part of optimization
- destructive commands outside workspace
- force pushing to remote
6.2 mcp/capabilities.json
{
  "required": [
    "filesystem",
    "shell",
    "git"
  ],
  "optional": [
    "browser",
    "logs",
    "database"
  ]
}
6.3 mcp/servers.json
{
  "servers": [
    {
      "name": "filesystem",
      "enabled": true
    },
    {
      "name": "shell",
      "enabled": true
    },
    {
      "name": "git",
      "enabled": true
    }
  ]
}
7. scripts 폴더 초안
7.1 scripts/run_tests.sh
#!/usr/bin/env bash
set -euo pipefail

if [ -d "tests" ]; then
  pytest tests -q
else
  echo "No tests directory found; skipping tests"
fi
7.2 scripts/run_eval.sh
#!/usr/bin/env bash
set -euo pipefail

python eval/frozen_eval.py
7.3 scripts/rollback_change.sh
#!/usr/bin/env bash
set -euo pipefail

git restore .
git clean -fd
echo "Rollback completed"
7.4 scripts/accept_change.sh
#!/usr/bin/env bash
set -euo pipefail

MESSAGE="${1:-accepted iteration change}"
git add .
git commit -m "$MESSAGE"
echo "Accepted and committed: $MESSAGE"
7.5 scripts/log_result.py
from __future__ import annotations

from pathlib import Path
import sys


RESULTS_PATH = Path("agent/RESULTS.tsv")


def main() -> int:
    if len(sys.argv) != 11:
        print(
            "usage: log_result.py iteration hypothesis_id status score_before "
            "score_after score_delta tests_pass constraints_ok change_summary rollback_reason"
        )
        return 1

    row = "\t".join(sys.argv[1:])
    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write(row + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
7.6 scripts/update_memory.py
from __future__ import annotations

from pathlib import Path


MEMORY_PATH = Path("agent/MEMORY.md")
DECISIONS_PATH = Path("agent/DECISIONS.md")


def main() -> int:
    if not MEMORY_PATH.exists() or not DECISIONS_PATH.exists():
        return 0

    decisions = DECISIONS_PATH.read_text(encoding="utf-8").strip()
    memory = MEMORY_PATH.read_text(encoding="utf-8").rstrip()

    updated = (
        memory
        + "\n\n## Latest Decision Snapshot\n"
        + decisions.splitlines()[-3:].__str__()
    )

    MEMORY_PATH.write_text(updated + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
7.7 scripts/make_final_report.py
from __future__ import annotations

from pathlib import Path


RESULTS_PATH = Path("agent/RESULTS.tsv")
REPORT_PATH = Path("reports/final/final_report.md")


def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not RESULTS_PATH.exists():
        REPORT_PATH.write_text("# Final Report\n\nNo results found.\n", encoding="utf-8")
        return 0

    lines = RESULTS_PATH.read_text(encoding="utf-8").strip().splitlines()
    body = "\n".join(f"- {line}" for line in lines[1:]) if len(lines) > 1 else "- no iterations logged"

    text = f"""# Final Report

## Results
{body}
"""
    REPORT_PATH.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
7.8 scripts/run_iteration.sh

초기 버전은 오케스트레이션 껍데기만 둔다.

#!/usr/bin/env bash
set -euo pipefail

echo "[1] run tests"
bash scripts/run_tests.sh

echo "[2] run eval"
python eval/frozen_eval.py > tmp/eval_result.json

echo "[3] done"
cat tmp/eval_result.json
7.9 scripts/run_loop.sh
#!/usr/bin/env bash
set -euo pipefail

mkdir -p tmp reports/iteration reports/final

echo "Starting loop..."
bash scripts/run_iteration.sh

echo "Generating final report..."
python scripts/make_final_report.py

echo "Done."
8. src / tests 샘플 초안
8.1 src/search/normalize.py
from __future__ import annotations


def normalize_query(query: str) -> list[str]:
    cleaned = []
    for ch in query.lower():
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return [t for t in "".join(cleaned).split() if t]
8.2 tests/test_normalize.py
from src.search.normalize import normalize_query


def test_normalize_query_removes_punctuation() -> None:
    assert normalize_query("wireless-mouse!!") == ["wireless", "mouse"]


def test_normalize_query_lowercases() -> None:
    assert normalize_query("USB-C cable???") == ["usb", "c", "cable"]
9. 최소 시작 절차
1. 폴더 구조 생성
2. baseline 측정
3. tests 준비
4. RULES.md 작성
5. PLAN.md에 첫 가설 작성
6. Codex CLI에게 implementer prompt로 작은 수정 수행
7. scripts/run_iteration.sh 실행
8. 결과 기록
9. accept/reject 결정
10. MEMORY.md 갱신
10. 이 문서 다음 단계

다음 문서에서 이어서 작성해야 할 것은 아래다.

prompts/*.md 상세판
run_loop.sh / run_iteration.sh 실전형 버전
accept/reject/rollback 자동 결정 구조
RESULTS.tsv 자동 기록 규격
Codex CLI 호출 규칙
MCP tool usage policy 상세판
11. 핵심 요약

이 문서는 실제 구현을 위한 가장 첫 번째 파일 세트를 제공한다.

핵심은:

목표 파일이 있고
규칙 파일이 있고
평가 파일이 있고
기록 파일이 있고
실행 스크립트가 있으며
역할 프롬프트가 분리되어 있다는 점이다.

즉 지금 상태만으로도
"작은 수정 → 테스트 → eval → 기록" 의 최소 루프는 시작할 수 있다.


```md
# 다음 단계 문서 2
