# MCP servers.json 실제 예시 + 최소 동작 템플릿 파일 세트 + 초기 부트스트랩 절차
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 앞선 설계를 실제 프로젝트에서 **처음부터 바로 띄울 수 있게 만드는 부트스트랩 문서**다.

핵심 범위:
1. `mcp/servers.json` 실제 예시
2. 최소 동작 템플릿 파일 세트
3. 초기 프로젝트 생성 절차
4. 첫 baseline 측정 절차
5. 첫 iteration 실행 절차
6. 실패 시 점검 포인트

이 문서의 목표는
"구조는 이해했는데 실제로 무엇부터 만들어야 하는지 모르겠다"를 없애는 것이다.

즉 이 문서는 **실행 시작 문서**다.

---

## 1. 전체 부트스트랩 개요

처음 시작할 때 필요한 순서는 아래다.

```text
1. 프로젝트 디렉토리 생성
2. 기본 폴더 구조 생성
3. 핵심 템플릿 파일 생성
4. git 초기화
5. baseline 측정
6. tests / eval 동작 확인
7. Codex implement 경로 연결
8. 첫 iteration 실행
9. 결과 로그 확인
10. 반복개선 루프 시작
2. 최소 동작 목표

초기 부트스트랩의 목표는 거창하지 않다.

최소 성공 기준

아래 6개만 되면 성공이다.

run_loop.sh 가 실행된다
run_iteration.sh 가 1회 끝까지 돈다
tests 가 실행된다
eval/frozen_eval.py 가 점수를 반환한다
RESULTS.tsv 에 1줄이 기록된다
accept 또는 reject 후 상태가 정리된다

즉 초반에는
"멀티 에이전트 느낌"보다
루프 1회가 신뢰성 있게 도는 것이 더 중요하다.

3. 폴더 구조 재확인

최소 권장 구조:

autoresearch-agent/
├─ src/
│  └─ search/
│     └─ normalize.py
├─ tests/
│  └─ test_normalize.py
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
│  ├─ build_implementer_input.py
│  ├─ check_forbidden_changes.py
│  ├─ check_change_budget.py
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
4. mcp/servers.json 실제 예시

주의:

MCP 서버 이름과 실행 명령은 실제 환경마다 다를 수 있다.
아래 예시는 구조 예시다.
핵심은 "어떤 서버를 어떤 정책으로 연결할지"다.
4.1 최소 버전 예시

파일: mcp/servers.json

{
  "servers": [
    {
      "name": "filesystem",
      "enabled": true,
      "description": "Read/write files inside the workspace",
      "policy": {
        "workspace_only": true,
        "allow_delete": false
      }
    },
    {
      "name": "shell",
      "enabled": true,
      "description": "Run tests and eval commands",
      "policy": {
        "workspace_only": true,
        "allow_network": false,
        "allow_destructive_commands": false
      }
    },
    {
      "name": "git",
      "enabled": true,
      "description": "Inspect diffs, restore changes, commit accepted iterations",
      "policy": {
        "allow_commit": true,
        "allow_force_push": false,
        "allow_history_rewrite": false
      }
    }
  ]
}

이 버전만으로도 대부분의 초기 루프는 충분히 돌릴 수 있다.

4.2 확장 버전 예시
{
  "servers": [
    {
      "name": "filesystem",
      "enabled": true,
      "description": "Workspace file access",
      "policy": {
        "workspace_only": true,
        "allow_delete": false
      }
    },
    {
      "name": "shell",
      "enabled": true,
      "description": "Local shell execution for tests/eval/lint/build",
      "policy": {
        "workspace_only": true,
        "allow_network": false,
        "allow_destructive_commands": false,
        "timeout_sec": 180
      }
    },
    {
      "name": "git",
      "enabled": true,
      "description": "Git status, diff, restore, add, commit",
      "policy": {
        "allow_commit": true,
        "allow_restore": true,
        "allow_force_push": false,
        "allow_history_rewrite": false
      }
    },
    {
      "name": "logs",
      "enabled": false,
      "description": "Read recent local logs only",
      "policy": {
        "read_only": true,
        "max_lines": 500
      }
    },
    {
      "name": "browser",
      "enabled": false,
      "description": "UI verification for browser-based projects",
      "policy": {
        "read_only_workflows": true
      }
    },
    {
      "name": "database",
      "enabled": false,
      "description": "Read-only local database inspection",
      "policy": {
        "read_only": true,
        "allow_mutation": false
      }
    }
  ]
}

초기에는 enabled: false 로 두고
실제로 필요할 때만 켜는 게 좋다.

5. mcp/capabilities.json 예시

파일: mcp/capabilities.json

{
  "required": [
    "filesystem",
    "shell",
    "git"
  ],
  "optional": [
    "logs",
    "browser",
    "database"
  ],
  "bootstrap_mode": {
    "enabled_servers": [
      "filesystem",
      "shell",
      "git"
    ]
  }
}
6. mcp/tool-policies.md 실제 예시

파일: mcp/tool-policies.md

# MCP Tool Policies

## Default Allowed
- filesystem read/write inside workspace
- shell commands for tests, eval, lint, build
- git status, diff, restore, add, commit

## Restricted
- file deletion
- multi-file rename
- dependency install/update
- schema change
- browser automation
- database access

## Forbidden
- editing eval/frozen_eval.py during optimization
- editing eval/fixtures.json during optimization
- editing eval/baseline.json from implementer
- directly editing agent/RESULTS.tsv
- directly editing agent/DECISIONS.md
- destructive shell commands
- force push
- history rewrite
- production mutations
7. 최소 동작 템플릿 파일 세트

이번 섹션은 정말 최소다.
즉 이 파일들만 있으면 첫 루프를 시작할 수 있다.

7.1 src/search/normalize.py
from __future__ import annotations


def normalize_query(query: str) -> list[str]:
    cleaned = []
    for ch in query.lower():
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return [t for t in "".join(cleaned).split() if t]
7.2 tests/test_normalize.py
from src.search.normalize import normalize_query


def test_normalize_query_removes_punctuation() -> None:
    assert normalize_query("wireless-mouse!!") == ["wireless", "mouse"]


def test_normalize_query_lowercases() -> None:
    assert normalize_query("USB-C cable???") == ["usb", "c", "cable"]
7.3 eval/fixtures.json
[
  {
    "id": "Q-001",
    "query": "wireless-mouse!!",
    "expected_keywords": ["wireless", "mouse"]
  },
  {
    "id": "Q-002",
    "query": "USB-C cable???",
    "expected_keywords": ["usb", "c", "cable"]
  },
  {
    "id": "Q-003",
    "query": "bluetooth speaker",
    "expected_keywords": ["bluetooth", "speaker"]
  }
]
7.4 eval/frozen_eval.py
from __future__ import annotations

import json
from pathlib import Path

from src.search.normalize import normalize_query


ROOT = Path(__file__).resolve().parent
FIXTURES_PATH = ROOT / "fixtures.json"


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
        "notes": ["baseline frozen eval completed"]
    }

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
7.5 eval/baseline.json

처음에는 bootstrap score를 직접 넣어도 되고,
처음 eval 실행 후 생성해도 된다.

{
  "score": 0.0,
  "measured_at": "2026-03-25T00:00:00Z",
  "iteration": 0
}
7.6 agent/RESULTS.tsv
iteration	timestamp	hypothesis_id	status	decision_code	score_before	score_after	score_delta	tests_pass	constraints_ok	critic_severity	critic_recommendation	changed_files_count	change_summary	rollback_reason
7.7 agent/ITERATION_STATE.json
{
  "iteration": 0,
  "mode": "single-agent",
  "phase": "init",
  "selected_hypothesis": null,
  "baseline_score": 0.0,
  "candidate_score": null,
  "tests_pass": null,
  "constraints_ok": null,
  "decision": null,
  "last_updated": "2026-03-25T00:00:00Z"
}
7.8 agent/DECISIONS.md
# DECISIONS
7.9 agent/MEMORY.md
# MEMORY

## Accepted Patterns
-

## Rejected Patterns
-

## Known Risks
-

## Strategy Notes
-
7.10 agent/PRODUCT_GOAL.md
# PRODUCT GOAL

## 목표
검색 relevance를 baseline보다 개선한다.

## 성공 조건
- frozen eval score 상승
- tests 통과
- constraints 유지

## 금지사항
- frozen eval 수정 금지
- fixtures 수정 금지
7.11 agent/TASK.md
# CURRENT TASK

## 현재 집중 문제
query punctuation normalization 개선 가능성을 검증한다.
7.12 agent/RULES.md
# RULES

1. eval/frozen_eval.py 수정 금지
2. eval/fixtures.json 수정 금지
3. 한 iteration당 하나의 핵심 변경만 허용
4. tests 실패 시 reject
5. score 미개선 시 reject
7.13 agent/HYPOTHESES.md
# HYPOTHESES

- H-001
  - title: normalize punctuation in queries
  - expected_effect: recall improvement
  - risk: minor precision drop
  - priority: high
  - status: selected
7.14 agent/PLAN.md
# PLAN

## Selected Hypothesis
H-001

## Change Scope
- src/search/normalize.py

## Planned Change
- punctuation normalization before tokenization

## Tests To Run
- bash scripts/run_tests.sh
- bash scripts/run_eval.sh

## Reject Conditions
- tests fail
- score regression
8. 최소 실행 스크립트 세트
8.1 scripts/run_tests.sh
#!/usr/bin/env bash
set -euo pipefail
pytest tests -q
8.2 scripts/run_eval.sh
#!/usr/bin/env bash
set -euo pipefail
python eval/frozen_eval.py
8.3 scripts/accept_change.sh
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
8.4 scripts/rollback_change.sh
#!/usr/bin/env bash
set -euo pipefail
git restore .
git clean -fd
echo "Rollback completed"
9. 초기 부트스트랩 절차

이제 실제로 시작하는 순서다.

9.1 디렉토리 생성
mkdir -p autoresearch-agent
cd autoresearch-agent

mkdir -p \
  src/search \
  tests \
  eval \
  agent \
  prompts \
  scripts \
  mcp \
  reports/iteration \
  reports/final \
  tmp
9.2 핵심 파일 생성

위 템플릿 파일들을 각 경로에 생성한다.

9.3 git 초기화
git init
git add .
git commit -m "bootstrap autoresearch agent project"

이 시점부터 rollback이 안정적으로 가능해진다.

9.4 Python / pytest 준비

예:

python -m venv .venv
source .venv/bin/activate
pip install pytest

환경에 따라 uv, poetry, pipenv 등을 써도 된다.
핵심은 tests가 실행 가능해야 한다는 점이다.

9.5 baseline 측정

먼저 현재 구현 상태의 frozen eval 점수를 확인한다.

python eval/frozen_eval.py

예상 출력:

{"score": 1.0, "tests_pass": true, "constraints_ok": true, "latency_ms": 100, "latency_delta_pct": 0.0, "regressions": [], "notes": ["baseline frozen eval completed"]}

그 다음 baseline을 파일에 반영한다.

예:

{
  "score": 1.0,
  "measured_at": "2026-03-25T00:00:00Z",
  "iteration": 0
}

주의:

이 샘플은 너무 단순해서 baseline이 1.0일 수도 있다.
실제 프로젝트에서는 frozen eval을 더 의미 있게 설계해야 한다.
10. 첫 실행 전 체크리스트

실행 전에 아래를 반드시 확인한다.

 pytest tests -q 가 통과하는가
 python eval/frozen_eval.py 가 JSON을 출력하는가
 git status 가 깨끗한가
 agent/RESULTS.tsv 헤더가 있는가
 agent/ITERATION_STATE.json 이 존재하는가
 eval/baseline.json 이 존재하는가
 tmp/ 폴더가 존재하는가
 forbidden path 정책이 정의되어 있는가
11. 첫 baseline 측정과 초기 commit 전략

권장 전략은 이렇다.

11.1 bootstrap commit

프로젝트 템플릿 생성 후 바로 커밋

git add .
git commit -m "bootstrap project structure"
11.2 baseline commit

baseline 값 확인 후 필요 시 baseline 파일 갱신 후 커밋

git add eval/baseline.json
git commit -m "record initial baseline"

이렇게 하면 첫 iteration부터
rollback 기준점이 훨씬 명확해진다.

12. 첫 iteration 실행 절차

초기에는 run_iteration.sh 또는 run_loop.sh 를 사용한다.

예:

bash scripts/run_iteration.sh --iteration 1 --mode single-agent --baseline 1.0

또는:

bash scripts/run_loop.sh --max-iterations 3 --mode single-agent
13. 첫 iteration에서 기대하는 결과

초기 샘플 프로젝트는 이미 간단한 normalize 로직이 들어 있으므로
개선 여지가 거의 없을 수 있다.
그래서 첫 iteration 결과는 보통 아래 둘 중 하나다.

경우 A: reject
score 개선 없음
rollback 수행
RESULTS.tsv 1행 추가
경우 B: accept
아주 작은 개선이 들어감
baseline 갱신
commit 생성

초기 부트스트랩 단계에서는
accept 자체보다도 아래가 더 중요하다.

loop가 끝까지 도는가
reject 시 롤백이 되는가
logs/memory/report가 남는가
14. 실패 시 점검 포인트
14.1 tests 실패

확인:

import path 문제
pytest 설치 여부
테스트 파일 경로
14.2 eval 실패

확인:

frozen_eval.py 가 JSON만 출력하는지
stdout에 불필요한 로그가 섞이지 않는지
fixtures.json 경로가 맞는지
14.3 rollback 실패

확인:

git repo 초기화 여부
untracked 파일 과다 생성 여부
.gitignore 설정 필요 여부
14.4 RESULTS.tsv 기록 실패

확인:

헤더 존재 여부
append 스크립트 인자 수
탭 문자 깨짐 여부
14.5 baseline 갱신 이상

확인:

accept 시에만 baseline 갱신하는지
reject인데 baseline이 바뀌지 않았는지
score_after 파싱이 정확한지
15. .gitignore 권장 예시

파일: .gitignore

.venv/
__pycache__/
.pytest_cache/
tmp/*.txt
tmp/*.log

주의:

tmp/*.json 은 디버깅에 유용하므로 초기에는 남겨도 된다.
안정화 후 일부만 ignore 해도 된다.
16. 실제 운영 시작 전 추천 보강

부트스트랩이 끝난 뒤 바로 보강하면 좋은 것들:

16.1 frozen eval 현실화

현재 샘플 eval은 너무 단순하다.
실제 프로젝트용으로 바꿔야 한다.

16.2 reject code 분류 강화

NO_IMPROVEMENT, TEST_FAIL, CRITIC_BLOCK 등을 정확히 남기면 좋다.

16.3 implement 단계 실제 Codex 연결

placeholder를 실제 Codex CLI 호출로 치환해야 한다.

16.4 change budget 적용

diff line 수, changed files 수 제한

16.5 forbidden path 검사 자동화

실수로 eval 파일을 건드리지 않게 해야 한다.

17. 초기 부트스트랩 완료 기준

아래가 되면 초기 세팅은 완료다.

 프로젝트 구조 생성 완료
 git commit 2회 이상 완료
 baseline 측정 완료
 tests / eval 개별 실행 성공
 iteration 1회 실행 성공
 RESULTS.tsv 기록 확인
 DECISIONS.md 업데이트 확인
 MEMORY.md 갱신 또는 유지 확인
 final report 생성 확인
18. 가장 중요한 현실적 조언

초기 부트스트랩에서 가장 많이 하는 실수는
시스템을 너무 크게 시작하는 것이다.

나쁜 시작
explorer/planner/critic/controller를 동시에 고도화
browser/db/logs/tool 전부 연결
복잡한 UI까지 같이 만듦
좋은 시작
filesystem + shell + git만 연결
단일 프로젝트
단일 frozen eval
iteration 1회 끝까지 돌리기부터 확인

즉:

멀티 에이전트 느낌보다, reject가 안전하게 되는 루프를 먼저 만들어야 한다.

19. 핵심 요약

이 문서의 핵심은 아래다.

mcp/servers.json 은 처음엔 최소 3개(filesystem/shell/git)만 켜라
템플릿 파일 세트만 있으면 첫 루프를 시작할 수 있다
bootstrap 직후 바로 git commit을 잡아라
baseline 측정이 끝나야 반복개선이 의미가 생긴다
첫 iteration의 목표는 "개선"보다 "루프가 끝까지 도는지 확인"이다
실패는 괜찮지만 rollback/log/report는 반드시 살아 있어야 한다

즉 이 문서까지 완료되면,
이제 시스템은 개념 문서가 아니라
실제로 켜볼 수 있는 형태가 된다.


다음 문서는 `Python 오케스트레이터 버전 설계 + bash에서 Python으로 이전하는 구조 + 상태머신 클래스 초안`으로 이어가면 가장 좋다.
다음 문서 작성
# 다음 단계 문서 8
# Python 오케스트레이터 버전 설계 + bash에서 Python으로 이전하는 구조 + 상태머신 클래스 초안
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 현재의 bash 기반 반복개선 루프를
**Python 오케스트레이터 기반 구조**로 이전하기 위한 설계 문서다.

핵심 범위:
1. 왜 bash에서 Python으로 옮기는가
2. 어떤 부분을 Python이 맡아야 하는가
3. 상태머신을 어떻게 코드로 표현할 것인가
4. 실행 컨텍스트 / 상태 / 결과 / 결정 로직을 어떤 클래스로 나눌 것인가
5. 최소 동작 가능한 Python 오케스트레이터 초안을 어떻게 구성할 것인가

이 문서의 목표는
기존 bash 스크립트를 버리는 것이 아니라,
**검증된 루프를 더 안정적이고 확장 가능하게 재구성하는 것**이다.

---

## 1. 왜 Python 오케스트레이터가 필요한가

bash는 빠르게 시작하기에는 좋다.
하지만 반복개선 시스템이 커질수록 아래 문제가 생긴다.

### 1.1 JSON 처리 복잡도
반복개선 루프는 거의 모든 단계가 JSON 입출력에 의존한다.

예:
- `planner_result.json`
- `implementer_result.json`
- `tests_result.json`
- `eval_result.json`
- `critic_result.json`
- `controller_result.json`

bash에서도 처리할 수 있지만:
- 파싱이 취약해지고
- 에러 처리가 어려워지고
- 조건 분기가 복잡해진다

### 1.2 상태머신 표현이 약함
bash는 선형 흐름에는 강하지만
상태 기반 시스템에는 약하다.

반복개선 루프는 실제로 아래 같은 상태를 가진다.

```text
INIT
READ_CONTEXT
EXPLORE
PLAN
IMPLEMENT
RUN_TESTS
RUN_EVAL
CRITIQUE
DECIDE
ACCEPT
REJECT
ROLLBACK
ARCHIVE
FINALIZE
ERROR

이 구조는 bash보다 Python 클래스/enum 쪽이 훨씬 자연스럽다.

1.3 예외 처리 한계

반복개선 루프에서는
"실패를 정상 흐름처럼 처리"해야 한다.

예:

테스트 실패 → reject
eval 실패 → reject
JSON 파싱 실패 → reject or error
forbidden file 수정 → reject

이런 흐름은 Python이 훨씬 명확하다.

1.4 확장성 문제

향후 확장:

multi-agent orchestration
candidate branch
richer MCP policies
dashboard / API
parallel hypothesis sandbox

이런 건 bash보다 Python 기반이 훨씬 낫다.

2. 이전 전략 원칙

중요한 건 "한 번에 다 갈아엎지 않는 것"이다.

권장 전략은 아래다.

2.1 1단계

bash 기반 실행을 그대로 유지

tests
eval
git rollback
log append
2.2 2단계

Python 오케스트레이터가 bash 스크립트를 감싼다

Python이 상태/결정 담당
bash는 실행 유틸리티로만 남음
2.3 3단계

일부 bash 로직을 Python으로 흡수

tests 실행
eval 실행
result parsing
report generation
2.4 4단계

상태머신/결정 엔진/보고서/입력 번들 생성까지 Python 일원화

즉:

초기에는 bash를 "실행 도구"로 남기고
Python을 "오케스트레이터"로 올리는 게 가장 안전하다.

3. 목표 아키텍처

Python 오케스트레이터 버전의 상위 구조는 아래와 같다.

orchestrator.py
  ├─ config.py
  ├─ state_machine.py
  ├─ models.py
  ├─ file_store.py
  ├─ runner.py
  ├─ decision_engine.py
  ├─ reporting.py
  ├─ codex_adapter.py
  ├─ mcp_policy.py
  └─ utils.py

실제 프로젝트 구조 예시는 아래처럼 갈 수 있다.

orchestrator/
├─ __init__.py
├─ main.py
├─ config.py
├─ enums.py
├─ models.py
├─ state_machine.py
├─ file_store.py
├─ decision_engine.py
├─ codex_adapter.py
├─ command_runner.py
├─ iteration_service.py
├─ reporting.py
└─ utils.py
4. Python 오케스트레이터가 맡을 책임

Python 오케스트레이터는 아래를 맡는다.

4.1 상태 로드
baseline 읽기
goal/task/rules/memory 읽기
iteration state 읽기
4.2 단계 실행
explore
plan
implement
tests
eval
critique
decision
archive
4.3 JSON 검증
required field 확인
malformed JSON 처리
default 값 보정
4.4 결정 수행
accept / reject / hold
baseline 갱신
rollback 호출
4.5 기록 관리
RESULTS.tsv append
DECISIONS.md append
MEMORY.md 갱신
final report 생성
5. bash와 Python의 역할 분리

초기 이전 단계에서 가장 좋은 분리는 아래다.

bash에 남길 것
scripts/run_tests.sh
scripts/run_eval.sh
scripts/accept_change.sh
scripts/rollback_change.sh
Python으로 옮길 것
iteration orchestration
state machine
decision logic
JSON result aggregation
input bundle generation
reporting
memory update
forbidden/budget checks

즉:

Python = 뇌 + 상태관리 + 판단
bash = 단순 실행기
6. 핵심 데이터 모델

Python 오케스트레이터에서 가장 먼저 정의해야 하는 건
데이터 모델이다.

6.1 OrchestratorConfig

역할:

실행 설정값 보관

필드 예:

max_iterations
target_score
mode
stop_on_hold
allow_dirty
max_no_improvement_streak
6.2 IterationState

역할:

현재 iteration 상태 표현

필드 예:

iteration
mode
phase
selected_hypothesis
baseline_score
candidate_score
tests_pass
constraints_ok
decision
last_updated
6.3 EvalResult

역할:

frozen eval 결과 표현

필드 예:

score
tests_pass
constraints_ok
latency_ms
latency_delta_pct
regressions
notes
6.4 TestsResult

역할:

테스트 실행 결과 표현

필드 예:

passed
summary
failed_tests
duration_sec
stderr
6.5 ImplementerResult

역할:

Codex implement 결과 표현

필드 예:

changed_files
change_summary
why_this_change
verification_commands_run
notes
scope_respected
forbidden_paths_touched
estimated_risk
6.6 CriticResult

역할:

critic 단계 결과 표현

필드 예:

severity
objections
recommendation
reasoning
6.7 DecisionResult

역할:

controller 최종 결정 표현

필드 예:

decision
reason
next_action
decision_code
7. enum 설계

상태와 의사결정은 문자열보다 enum으로 다루는 게 낫다.

파일: orchestrator/enums.py

from __future__ import annotations

from enum import Enum


class Phase(str, Enum):
    INIT = "init"
    READ_CONTEXT = "read_context"
    EXPLORE = "explore"
    PLAN = "plan"
    IMPLEMENT = "implement"
    RUN_TESTS = "run_tests"
    RUN_EVAL = "run_eval"
    CRITIQUE = "critique"
    DECIDE = "decide"
    ACCEPT = "accept"
    REJECT = "reject"
    ROLLBACK = "rollback"
    ARCHIVE = "archive"
    FINALIZE = "finalize"
    ERROR = "error"
    DONE = "done"


class Decision(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    HOLD = "hold"


class DecisionCode(str, Enum):
    ACCEPT = "ACCEPT"
    TEST_FAIL = "TEST_FAIL"
    CONSTRAINT_FAIL = "CONSTRAINT_FAIL"
    NO_IMPROVEMENT = "NO_IMPROVEMENT"
    SCORE_REGRESSION = "SCORE_REGRESSION"
    CRITIC_BLOCK = "CRITIC_BLOCK"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    FORBIDDEN_FILE = "FORBIDDEN_FILE"
    EVAL_CRASH = "EVAL_CRASH"
    IMPLEMENT_ERROR = "IMPLEMENT_ERROR"
    UNKNOWN = "UNKNOWN"
8. dataclass 모델 초안

파일: orchestrator/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestratorConfig:
    max_iterations: int = 10
    target_score: float | None = None
    mode: str = "single-agent"
    stop_on_hold: bool = True
    allow_dirty: bool = False
    max_no_improvement_streak: int = 3


@dataclass
class IterationState:
    iteration: int
    mode: str
    phase: str
    selected_hypothesis: str | None
    baseline_score: float
    candidate_score: float | None = None
    tests_pass: bool | None = None
    constraints_ok: bool | None = None
    decision: str | None = None
    last_updated: str | None = None


@dataclass
class TestsResult:
    passed: bool
    summary: str
    failed_tests: list[str] = field(default_factory=list)
    duration_sec: float = 0.0
    stderr: str = ""


@dataclass
class EvalResult:
    score: float
    tests_pass: bool
    constraints_ok: bool
    latency_ms: int | None = None
    latency_delta_pct: float | None = None
    regressions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ImplementerResult:
    changed_files: list[str]
    change_summary: str
    why_this_change: str
    verification_commands_run: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    scope_respected: bool = True
    forbidden_paths_touched: list[str] = field(default_factory=list)
    estimated_risk: str = "unknown"


@dataclass
class CriticResult:
    severity: str
    objections: list[str]
    recommendation: str
    reasoning: str


@dataclass
class DecisionResult:
    decision: str
    reason: str
    next_action: str
    decision_code: str


@dataclass
class ResultRow:
    iteration: int
    hypothesis_id: str
    status: str
    decision_code: str
    score_before: float
    score_after: float
    score_delta: float
    tests_pass: bool
    constraints_ok: bool
    critic_severity: str
    critic_recommendation: str
    changed_files_count: int
    change_summary: str
    rollback_reason: str = ""
9. 파일 저장소 계층 설계

상태와 각종 md/json/tsv 파일을 다루는 코드는
한 곳으로 모아야 한다.

파일: orchestrator/file_store.py

역할:

파일 읽기/쓰기
baseline 로드/저장
iteration state 로드/저장
memory/decision/results append
tmp json 로드/저장

이렇게 해야
오케스트레이터 본체는 "비즈니스 로직"에 집중할 수 있다.

9.1 FileStore 책임 목록
read_text(path)
write_text(path, text)
read_json(path)
write_json(path, obj)
load_baseline()
save_baseline(score, iteration)
load_iteration_state()
save_iteration_state(state)
append_result_row(row)
append_decision_block(...)
load_memory()
save_memory(text)
9.2 FileStore 초안
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.models import IterationState, ResultRow


class FileStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, relative: str) -> Path:
        return self.root / relative

    def read_text(self, relative: str) -> str:
        return self.path(relative).read_text(encoding="utf-8")

    def write_text(self, relative: str, text: str) -> None:
        p = self.path(relative)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def read_json(self, relative: str) -> dict:
        return json.loads(self.read_text(relative))

    def write_json(self, relative: str, data: dict) -> None:
        self.write_text(relative, json.dumps(data, ensure_ascii=False, indent=2))

    def load_baseline(self) -> float:
        data = self.read_json("eval/baseline.json")
        return float(data["score"])

    def save_baseline(self, score: float, iteration: int) -> None:
        self.write_json(
            "eval/baseline.json",
            {
                "score": score,
                "iteration": iteration,
                "measured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            },
        )

    def load_iteration_state(self) -> IterationState:
        data = self.read_json("agent/ITERATION_STATE.json")
        return IterationState(**data)

    def save_iteration_state(self, state: IterationState) -> None:
        self.write_json("agent/ITERATION_STATE.json", asdict(state))

    def append_result_row(self, row: ResultRow) -> None:
        path = self.path("agent/RESULTS.tsv")
        path.parent.mkdir(parents=True, exist_ok=True)

        header = [
            "iteration",
            "timestamp",
            "hypothesis_id",
            "status",
            "decision_code",
            "score_before",
            "score_after",
            "score_delta",
            "tests_pass",
            "constraints_ok",
            "critic_severity",
            "critic_recommendation",
            "changed_files_count",
            "change_summary",
            "rollback_reason",
        ]

        need_header = not path.exists()
        with path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            if need_header:
                writer.writerow(header)
            writer.writerow([
                row.iteration,
                datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                row.hypothesis_id,
                row.status,
                row.decision_code,
                row.score_before,
                row.score_after,
                row.score_delta,
                str(row.tests_pass).lower(),
                str(row.constraints_ok).lower(),
                row.critic_severity,
                row.critic_recommendation,
                row.changed_files_count,
                row.change_summary,
                row.rollback_reason,
            ])
10. CommandRunner 설계

Python 오케스트레이터는 외부 명령 실행도 깔끔하게 래핑해야 한다.

파일: orchestrator/command_runner.py

역할:

shell command 실행
stdout/stderr 캡처
timeout
return code 처리
JSON 결과 파일 존재 여부 체크
10.1 CommandResult 모델
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
10.2 CommandRunner 초안
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run(self, command: list[str], timeout: int = 300) -> CommandResult:
        completed = subprocess.run(
            command,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
11. CodexAdapter 설계

Codex CLI 호출은 오케스트레이터 본체에서 직접 하지 말고
adapter로 분리하는 게 좋다.

파일: orchestrator/codex_adapter.py

역할:

implement 입력 번들 생성
Codex CLI 호출
implementer_result.json 검증
실패 시 명확한 예외 반환
11.1 CodexAdapter가 필요한 이유

이유:

나중에 Codex CLI 문법이 바뀌어도 adapter만 수정하면 됨
다른 LLM CLI로 교체하기 쉬움
implement 단계만 독립 테스트 가능
11.2 CodexAdapter 인터페이스
class CodexAdapter:
    def build_input_bundle(...) -> Path: ...
    def run_implement(...) -> ImplementerResult: ...
11.3 CodexAdapter 초안
from __future__ import annotations

import json
from pathlib import Path

from orchestrator.command_runner import CommandRunner
from orchestrator.models import ImplementerResult


class CodexAdapter:
    def __init__(self, root: Path, runner: CommandRunner) -> None:
        self.root = root
        self.runner = runner

    def build_input_bundle(self) -> None:
        # 실제 구현에서는 planner result, rules, memory 등을 읽어 bundle 생성
        tmp = self.root / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "implementer_input.md").write_text(
            "# Implementer Input\n\nPlaceholder bundle.\n",
            encoding="utf-8",
        )

    def run_implement(self) -> ImplementerResult:
        self.build_input_bundle()

        # 실제 Codex CLI 호출 구문으로 대체
        result = self.runner.run(["bash", "scripts/run_codex_implement.sh"])

        if result.returncode != 0:
            raise RuntimeError(f"Codex implement failed: {result.stderr}")

        payload_path = self.root / "tmp" / "implementer_result.json"
        if not payload_path.exists():
            raise RuntimeError("Missing tmp/implementer_result.json")

        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        return ImplementerResult(**payload)
12. 상태머신 클래스 설계

이 문서의 핵심이다.
상태머신은 루프 전체를 통제한다.

파일: orchestrator/state_machine.py

역할:

현재 phase 관리
phase 전이
예외 발생 시 ERROR 상태 전환
iteration 완료 시 DONE 상태 전환
12.1 StateMachine 책임
set_phase(phase)
run_iteration(iteration_no, baseline)
handle_error(exc)
finalize_iteration()
12.2 상태머신이 필요한 이유

bash에서는 phase를 문자열로 흘려보내기 쉽다.
하지만 Python 상태머신은:

현재 phase를 명확히 저장하고
phase 전이를 제한하고
실패 지점을 추적하기 쉽다
12.3 상태머신 초안
from __future__ import annotations

from datetime import datetime, timezone

from orchestrator.enums import Phase
from orchestrator.models import IterationState


class IterationStateMachine:
    def __init__(self, state: IterationState) -> None:
        self.state = state

    def set_phase(self, phase: Phase) -> None:
        self.state.phase = phase.value
        self.state.last_updated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def mark_decision(self, decision: str) -> None:
        self.state.decision = decision
        self.state.last_updated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
13. IterationService 설계

실제 한 iteration의 비즈니스 로직은
하나의 서비스 클래스로 묶는 게 좋다.

파일: orchestrator/iteration_service.py

역할:

한 iteration end-to-end 실행
상태머신 갱신
각 단계 호출
결과 row 생성
decision 수행
baseline 갱신 여부 판단
13.1 책임 분해
입력
iteration 번호
baseline
config
출력
decision result
updated baseline
result row
iteration report
13.2 단계 순서
read_context
→ explore
→ plan
→ implement
→ run_tests
→ run_eval
→ critique
→ decide
→ accept/reject/rollback
→ archive
14. DecisionEngine Python화

이미 문서에서 의사코드는 정리했으니
Python 오케스트레이터에서는 독립 클래스로 둔다.

파일: orchestrator/decision_engine.py

from __future__ import annotations

from orchestrator.enums import Decision, DecisionCode
from orchestrator.models import CriticResult, DecisionResult, EvalResult, ImplementerResult, TestsResult


class DecisionEngine:
    def decide(
        self,
        *,
        score_before: float,
        eval_result: EvalResult,
        tests_result: TestsResult,
        critic_result: CriticResult,
        implementer_result: ImplementerResult,
    ) -> DecisionResult:
        if not tests_result.passed:
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="tests failed",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.TEST_FAIL.value,
            )

        if not eval_result.constraints_ok:
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="constraints failed",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.CONSTRAINT_FAIL.value,
            )

        if implementer_result.forbidden_paths_touched:
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="forbidden file was modified",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.FORBIDDEN_FILE.value,
            )

        if not implementer_result.scope_respected:
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="change exceeded approved scope",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.SCOPE_VIOLATION.value,
            )

        if eval_result.score < score_before:
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="score regressed",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.SCORE_REGRESSION.value,
            )

        if eval_result.score == score_before:
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="score did not improve",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.NO_IMPROVEMENT.value,
            )

        if critic_result.severity == "high" and critic_result.recommendation == "reject":
            return DecisionResult(
                decision=Decision.REJECT.value,
                reason="critic found blocking issue",
                next_action="rollback_and_continue",
                decision_code=DecisionCode.CRITIC_BLOCK.value,
            )

        return DecisionResult(
            decision=Decision.ACCEPT.value,
            reason="score improved and all checks passed",
            next_action="archive_and_continue",
            decision_code=DecisionCode.ACCEPT.value,
        )
15. Reporting 계층 Python화

기존의:

log_result.py
update_memory.py
make_final_report.py

는 Python 오케스트레이터 구조에서는
reporting.py로 통합하거나 래핑할 수 있다.

역할:

result row append
decision markdown append
memory update
iteration report write
final report write
16. Orchestrator 본체 구조

파일: orchestrator/main.py

상위 루프는 아래처럼 될 수 있다.

from __future__ import annotations

from pathlib import Path

from orchestrator.command_runner import CommandRunner
from orchestrator.config import load_config
from orchestrator.file_store import FileStore
from orchestrator.iteration_service import IterationService


def main() -> int:
    root = Path.cwd()
    config = load_config()
    store = FileStore(root)
    runner = CommandRunner(root)

    service = IterationService(
        root=root,
        config=config,
        store=store,
        runner=runner,
    )

    baseline = store.load_baseline()
    no_improvement_streak = 0

    for iteration in range(1, config.max_iterations + 1):
        result = service.run(iteration=iteration, baseline=baseline)

        if result.new_baseline > baseline:
            no_improvement_streak = 0
        else:
            no_improvement_streak += 1

        baseline = result.new_baseline

        if config.target_score is not None and baseline >= config.target_score:
            break

        if result.decision == "hold" and config.stop_on_hold:
            break

        if no_improvement_streak >= config.max_no_improvement_streak:
            break

    service.write_final_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
17. IterationResult 모델

Iteration 하나의 결과를 Python에서 다루기 쉽게
전용 모델이 있으면 좋다.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IterationRunResult:
    decision: str
    decision_code: str
    score_before: float
    score_after: float
    new_baseline: float
18. config.py 초안

bash 인자 파싱 대신
Python에서는 argparse + config loader가 적합하다.

from __future__ import annotations

import argparse

from orchestrator.models import OrchestratorConfig


def load_config() -> OrchestratorConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--target-score", type=float, default=None)
    parser.add_argument("--mode", type=str, default="single-agent")
    parser.add_argument("--stop-on-hold", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--max-no-improvement-streak", type=int, default=3)

    args = parser.parse_args()

    return OrchestratorConfig(
        max_iterations=args.max_iterations,
        target_score=args.target_score,
        mode=args.mode,
        stop_on_hold=args.stop_on_hold,
        allow_dirty=args.allow_dirty,
        max_no_improvement_streak=args.max_no_improvement_streak,
    )
19. Python 이전 시 권장 폴더 구조
autoresearch-agent/
├─ orchestrator/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ enums.py
│  ├─ models.py
│  ├─ file_store.py
│  ├─ state_machine.py
│  ├─ command_runner.py
│  ├─ codex_adapter.py
│  ├─ decision_engine.py
│  ├─ iteration_service.py
│  ├─ reporting.py
│  └─ utils.py
├─ src/
├─ tests/
├─ eval/
├─ agent/
├─ prompts/
├─ scripts/
├─ mcp/
├─ reports/
└─ tmp/
20. bash에서 Python으로 옮길 때의 실제 전환 순서

권장 순서는 아래다.

20.1 1차 전환

Python이 run_iteration.sh 를 감싼다

기존 bash는 그대로 사용
Python은 상태/기록/결정만 관리
20.2 2차 전환

Python이 run_tests.sh, run_eval.sh 결과를 직접 읽는다

bash는 command wrapper만 유지
20.3 3차 전환

Implement 단계와 Codex adapter를 Python으로 이동

20.4 4차 전환

최종적으로 run_loop.sh 는 thin wrapper만 남거나 삭제

즉:

bash를 즉시 폐기하지 말고
Python이 바깥에서 점진적으로 감싸는 식으로 가야 한다
21. 최소 동작 Python 오케스트레이터 템플릿

정말 최소한의 시작점은 아래처럼 둘 수 있다.

파일: orchestrator/main.py

from __future__ import annotations

from pathlib import Path

from orchestrator.command_runner import CommandRunner
from orchestrator.file_store import FileStore


def main() -> int:
    root = Path.cwd()
    store = FileStore(root)
    runner = CommandRunner(root)

    baseline = store.load_baseline()
    print(f"[python-orchestrator] baseline={baseline}")

    tests = runner.run(["bash", "scripts/run_tests.sh"])
    print(f"[python-orchestrator] tests rc={tests.returncode}")

    eval_run = runner.run(["bash", "scripts/run_eval.sh"])
    print(f"[python-orchestrator] eval rc={eval_run.returncode}")
    print(eval_run.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

이렇게 아주 작게 시작해서
점점 iteration service/state machine/decision engine을 얹는 방식이 가장 안전하다.

22. 흔한 실패 패턴
22.1 Python으로 한 번에 전부 옮김

문제:

어디서 깨졌는지 알기 어려움
22.2 bash와 Python 책임이 중복됨

문제:

동일 로직 두 군데 존재
유지보수 어려움
22.3 모델 클래스 없이 dict만 난무

문제:

필드 누락, 오타, 타입 오류 증가
22.4 state machine 없이 if/else만 늘어남

문제:

phase 추적 어려움
오류 처리 불명확
22.5 Codex adapter를 분리하지 않음

문제:

CLI 교체/수정이 어려움
23. 추천 구현 우선순위

Python 오케스트레이터를 만들 때 가장 좋은 순서는 아래다.

models.py
enums.py
file_store.py
command_runner.py
decision_engine.py
state_machine.py
codex_adapter.py
iteration_service.py
main.py
reporting.py

이 순서가 좋은 이유:

데이터 구조
외부 실행
결정 로직
상태 관리
구현 실행
상위 orchestration

순으로 쌓이기 때문이다.

24. 핵심 요약

이 문서의 핵심은 아래다.

bash는 시작이 빠르지만, 장기적으로 Python 오케스트레이터가 유리하다
Python은 상태머신, JSON 처리, 예외 처리, 확장성에서 강하다
bash를 즉시 없애지 말고, Python이 바깥에서 감싸는 방식으로 점진 이전해야 한다
핵심 클래스는 FileStore, CommandRunner, CodexAdapter, DecisionEngine, IterationStateMachine, IterationService 다
dict 남발보다 dataclass + enum 구조가 훨씬 안정적이다
Python 오케스트레이터의 본질은 "실행"이 아니라 상태와 판단을 통제하는 것이다

즉 최종 구조는 아래처럼 정리된다.

Python Orchestrator
  ├─ 상태 관리
  ├─ 파일/JSON 관리
  ├─ Codex 호출
  ├─ tests/eval 실행
  ├─ decision engine
  ├─ rollback/accept 통제
  └─ reporting

이렇게 가야
반복개선 루프가 단순 스크립트 모음이 아니라
실전 운영 가능한 시스템으로 발전할 수 있다.


원하면 다음 문서는 `IterationService 실제 구현 초안 + end-to-end Python 오케스트레이터 코드 뼈대`로 바로 이어서 작성하겠다.
다음 문서 작성 
# 다음 단계 문서 9
# IterationService 실제 구현 초안 + End-to-End Python 오케스트레이터 코드 뼈대
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 앞서 설계한 Python 오케스트레이터를
실제로 동작 가능한 수준으로 끌어내리기 위한
**IterationService 중심 구현 초안**이다.

핵심 범위:
1. `IterationService` 실제 책임 분해
2. 단계별 메서드 설계
3. `End-to-End` 실행 흐름 코드 뼈대
4. 상태 저장 / 결과 기록 / baseline 갱신 연결
5. bash 유틸과 공존하는 Python 오케스트레이터 최소 구현

이 문서의 목표는
추상 설계를 넘어서
**"돌아갈 수 있는 Python 구조"** 를 만드는 것이다.

---

## 1. IterationService의 역할 다시 정의

`IterationService` 는 Python 오케스트레이터의 핵심이다.

한 줄로 정의하면:

> 한 iteration을 처음부터 끝까지 실행하고, 결과를 구조화해 반환하는 서비스

즉 `IterationService` 는 다음을 책임진다.

1. 컨텍스트 로드
2. 상태 phase 갱신
3. explore 결과 준비
4. plan 결과 준비
5. implement 실행
6. tests 실행
7. eval 실행
8. critic 생성
9. decision 생성
10. accept/reject/rollback 수행
11. 결과 로그/메모리/리포트 저장
12. 최종 `IterationRunResult` 반환

---

## 2. IterationService가 받아야 할 의존성

권장 생성자 의존성은 아래와 같다.

- `root: Path`
- `config: OrchestratorConfig`
- `store: FileStore`
- `runner: CommandRunner`
- `decision_engine: DecisionEngine`
- `codex_adapter: CodexAdapter`

선택 의존성:
- `reporting_service`
- `memory_service`
- `critic_service`
- `explorer_service`
- `planner_service`

초기 버전에서는 일부를 내부 메서드로 두고,
나중에 서비스 분리해도 된다.

---

## 3. IterationService 상위 구조

권장 구조:

```text
IterationService
├─ run(iteration, baseline)
├─ _load_context()
├─ _explore()
├─ _plan()
├─ _implement()
├─ _run_tests()
├─ _run_eval()
├─ _critique()
├─ _decide()
├─ _accept()
├─ _reject_and_rollback()
├─ _archive()
└─ write_final_report()

초기에는 _explore, _plan, _critique 를
간단한 placeholder 또는 파일 기반 처리로 둘 수 있다.

4. Context 모델 도입

IterationService 내부에서 여러 파일을 따로따로 넘기기보다
하나의 컨텍스트 구조로 묶는 게 좋다.

파일: orchestrator/models.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IterationContext:
    product_goal: str
    task: str
    rules: str
    memory: str
    hypotheses: str
    plan: str

이 모델은 run() 시작 시 한 번 로드해서
각 단계에 전달할 수 있다.

5. IterationRunResult 모델 보강

이미 간단 버전을 만들었지만,
실전에서는 조금 더 많은 정보를 담는 게 좋다.

파일: orchestrator/models.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IterationRunResult:
    iteration: int
    decision: str
    decision_code: str
    score_before: float
    score_after: float
    score_delta: float
    new_baseline: float
    tests_pass: bool
    constraints_ok: bool
    hypothesis_id: str
    change_summary: str
6. FileStore 보강 포인트

IterationService가 편하게 쓰기 위해
FileStore에 아래 메서드를 추가하면 좋다.

def load_iteration_context(self) -> IterationContext: ...
def append_decision_block(self, *, iteration: int, content: str) -> None: ...
def write_tmp_json(self, filename: str, data: dict) -> None: ...
def read_tmp_json(self, filename: str) -> dict: ...

예시:

from __future__ import annotations

import json
from pathlib import Path

from orchestrator.models import IterationContext


class FileStore:
    # 기존 코드 생략

    def load_iteration_context(self) -> IterationContext:
        return IterationContext(
            product_goal=self.read_text("agent/PRODUCT_GOAL.md"),
            task=self.read_text("agent/TASK.md"),
            rules=self.read_text("agent/RULES.md"),
            memory=self.read_text("agent/MEMORY.md"),
            hypotheses=self.read_text("agent/HYPOTHESES.md"),
            plan=self.read_text("agent/PLAN.md"),
        )

    def write_tmp_json(self, filename: str, data: dict) -> None:
        self.write_json(f"tmp/{filename}", data)

    def read_tmp_json(self, filename: str) -> dict:
        return self.read_json(f"tmp/{filename}")

    def append_decision_block(self, *, iteration: int, content: str) -> None:
        path = self.path("agent/DECISIONS.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if not path.exists() else "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{prefix}\n## Iteration {iteration}\n{content.strip()}\n")
7. Critic / Explorer / Planner 최소 구현 전략

초기 Python 오케스트레이터는
모든 역할을 별도 LLM 호출로 만들 필요가 없다.

권장 초기 전략:

Explorer
agent/HYPOTHESES.md 를 읽고 첫 번째 selected hypothesis 선택
또는 placeholder JSON 생성
Planner
agent/PLAN.md 와 tmp/planner_result.json 를 동기화
초기에는 PLAN을 사실상 source of truth로 사용
Critic
tests/eval 결과 기반 자동 critic 생성
별도 LLM 없이도 충분히 시작 가능

즉 초기에는:

explore / plan / critic 도 완전한 에이전트가 아니라,
파일 기반 규칙 + 간단한 Python 로직으로 먼저 시작한다.

8. 자동 Critic 생성 함수 예시

별도 CriticService 없이
IterationService 내부 helper로 둘 수 있다.

from __future__ import annotations

from orchestrator.models import CriticResult, EvalResult, TestsResult


def auto_critic(
    *,
    score_before: float,
    tests_result: TestsResult,
    eval_result: EvalResult,
) -> CriticResult:
    objections: list[str] = []
    severity = "low"
    recommendation = "accept"
    reasoning = "automatic critic review completed"

    if not tests_result.passed:
        severity = "high"
        recommendation = "reject"
        objections.append("tests failed")

    if not eval_result.constraints_ok:
        severity = "high"
        recommendation = "reject"
        objections.append("constraints failed")

    if eval_result.score < score_before:
        severity = "high"
        recommendation = "reject"
        objections.append("score regressed")

    if eval_result.score == score_before:
        severity = "medium"
        recommendation = "reject"
        objections.append("score did not improve")

    return CriticResult(
        severity=severity,
        objections=objections,
        recommendation=recommendation,
        reasoning=reasoning,
    )
9. IterationService 실제 구현 초안

파일: orchestrator/iteration_service.py

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.codex_adapter import CodexAdapter
from orchestrator.command_runner import CommandRunner
from orchestrator.decision_engine import DecisionEngine
from orchestrator.enums import Decision, Phase
from orchestrator.file_store import FileStore
from orchestrator.models import (
    CriticResult,
    EvalResult,
    ImplementerResult,
    IterationContext,
    IterationRunResult,
    IterationState,
    OrchestratorConfig,
    ResultRow,
    TestsResult,
)
from orchestrator.state_machine import IterationStateMachine


class IterationService:
    def __init__(
        self,
        *,
        root: Path,
        config: OrchestratorConfig,
        store: FileStore,
        runner: CommandRunner,
        decision_engine: DecisionEngine,
        codex_adapter: CodexAdapter,
    ) -> None:
        self.root = root
        self.config = config
        self.store = store
        self.runner = runner
        self.decision_engine = decision_engine
        self.codex_adapter = codex_adapter

    def run(self, *, iteration: int, baseline: float) -> IterationRunResult:
        state = self._load_or_create_state(
            iteration=iteration,
            baseline=baseline,
            mode=self.config.mode,
        )
        machine = IterationStateMachine(state)
        self.store.save_iteration_state(machine.state)

        try:
            machine.set_phase(Phase.READ_CONTEXT)
            self.store.save_iteration_state(machine.state)
            context = self._load_context()

            machine.set_phase(Phase.EXPLORE)
            self.store.save_iteration_state(machine.state)
            hypothesis_id = self._explore(context=context)

            machine.state.selected_hypothesis = hypothesis_id
            self.store.save_iteration_state(machine.state)

            machine.set_phase(Phase.PLAN)
            self.store.save_iteration_state(machine.state)
            self._plan(context=context, hypothesis_id=hypothesis_id)

            machine.set_phase(Phase.IMPLEMENT)
            self.store.save_iteration_state(machine.state)
            implementer_result = self._implement()

            machine.set_phase(Phase.RUN_TESTS)
            self.store.save_iteration_state(machine.state)
            tests_result = self._run_tests()

            machine.state.tests_pass = tests_result.passed
            self.store.save_iteration_state(machine.state)

            machine.set_phase(Phase.RUN_EVAL)
            self.store.save_iteration_state(machine.state)
            eval_result = self._run_eval()

            machine.state.candidate_score = eval_result.score
            machine.state.constraints_ok = eval_result.constraints_ok
            self.store.save_iteration_state(machine.state)

            machine.set_phase(Phase.CRITIQUE)
            self.store.save_iteration_state(machine.state)
            critic_result = self._critique(
                score_before=baseline,
                tests_result=tests_result,
                eval_result=eval_result,
            )

            machine.set_phase(Phase.DECIDE)
            self.store.save_iteration_state(machine.state)
            decision_result = self.decision_engine.decide(
                score_before=baseline,
                eval_result=eval_result,
                tests_result=tests_result,
                critic_result=critic_result,
                implementer_result=implementer_result,
            )

            machine.mark_decision(decision_result.decision)
            self.store.save_iteration_state(machine.state)

            if decision_result.decision == Decision.ACCEPT.value:
                machine.set_phase(Phase.ACCEPT)
                self.store.save_iteration_state(machine.state)
                new_baseline = self._accept(
                    iteration=iteration,
                    score=eval_result.score,
                )
                rollback_reason = ""
                status = "accepted"
            else:
                machine.set_phase(Phase.REJECT)
                self.store.save_iteration_state(machine.state)
                self._reject_and_rollback()
                new_baseline = baseline
                rollback_reason = decision_result.reason
                status = "rejected"

            machine.set_phase(Phase.ARCHIVE)
            self.store.save_iteration_state(machine.state)

            result_row = ResultRow(
                iteration=iteration,
                hypothesis_id=hypothesis_id,
                status=status,
                decision_code=decision_result.decision_code,
                score_before=baseline,
                score_after=eval_result.score,
                score_delta=round(eval_result.score - baseline, 6),
                tests_pass=tests_result.passed,
                constraints_ok=eval_result.constraints_ok,
                critic_severity=critic_result.severity,
                critic_recommendation=critic_result.recommendation,
                changed_files_count=len(implementer_result.changed_files),
                change_summary=implementer_result.change_summary,
                rollback_reason=rollback_reason,
            )

            self._archive(
                iteration=iteration,
                result_row=result_row,
                decision_reason=decision_result.reason,
                tests_result=tests_result,
                eval_result=eval_result,
                critic_result=critic_result,
            )

            machine.set_phase(Phase.DONE)
            self.store.save_iteration_state(machine.state)

            return IterationRunResult(
                iteration=iteration,
                decision=decision_result.decision,
                decision_code=decision_result.decision_code,
                score_before=baseline,
                score_after=eval_result.score,
                score_delta=round(eval_result.score - baseline, 6),
                new_baseline=new_baseline,
                tests_pass=tests_result.passed,
                constraints_ok=eval_result.constraints_ok,
                hypothesis_id=hypothesis_id,
                change_summary=implementer_result.change_summary,
            )
        except Exception:
            machine.set_phase(Phase.ERROR)
            self.store.save_iteration_state(machine.state)
            raise
10. IterationService 내부 헬퍼 메서드 초안

위 클래스에 이어서 아래 메서드들을 붙인다.

    def _load_or_create_state(self, *, iteration: int, baseline: float, mode: str) -> IterationState:
        try:
            state = self.store.load_iteration_state()
            state.iteration = iteration
            state.mode = mode
            state.phase = Phase.INIT.value
            state.baseline_score = baseline
            state.candidate_score = None
            state.tests_pass = None
            state.constraints_ok = None
            state.decision = None
            state.last_updated = self._now()
            return state
        except Exception:
            return IterationState(
                iteration=iteration,
                mode=mode,
                phase=Phase.INIT.value,
                selected_hypothesis=None,
                baseline_score=baseline,
                candidate_score=None,
                tests_pass=None,
                constraints_ok=None,
                decision=None,
                last_updated=self._now(),
            )

    def _load_context(self) -> IterationContext:
        return self.store.load_iteration_context()

    def _explore(self, *, context: IterationContext) -> str:
        """
        초기 버전:
        - HYPOTHESES.md에서 selected로 표시된 첫 hypothesis를 사용
        - 없으면 H-001 fallback
        """
        for line in context.hypotheses.splitlines():
            if "status: selected" in line:
                # 바로 위쪽에서 id를 찾는 단순 전략 대신,
                # 초기 구현은 H-001 fallback을 둔다.
                return "H-001"
        return "H-001"

    def _plan(self, *, context: IterationContext, hypothesis_id: str) -> None:
        """
        초기 버전:
        - PLAN.md를 이미 수동 준비했다고 가정
        - planner_result.json을 최소 구조로 동기화
        """
        payload = {
            "selected_hypothesis": hypothesis_id,
            "change_scope": ["src/search/normalize.py"],
            "planned_change": "focused change from PLAN.md",
            "tests_to_run": [
                "bash scripts/run_tests.sh",
                "bash scripts/run_eval.sh",
            ],
            "reject_conditions": [
                "tests fail",
                "score regression",
                "constraints fail",
            ],
        }
        self.store.write_tmp_json("planner_result.json", payload)

    def _implement(self) -> ImplementerResult:
        return self.codex_adapter.run_implement()

    def _run_tests(self) -> TestsResult:
        result = self.runner.run(["bash", "scripts/run_tests.sh"])
        try:
            payload = self.store.read_tmp_json("tests_result.json")
            return TestsResult(**payload)
        except Exception:
            return TestsResult(
                passed=(result.returncode == 0),
                summary=result.stdout[-4000:] if result.stdout else "tests completed",
                failed_tests=[],
                duration_sec=0.0,
                stderr=result.stderr[-4000:],
            )

    def _run_eval(self) -> EvalResult:
        result = self.runner.run(["bash", "scripts/run_eval.sh"])
        try:
            payload = self.store.read_tmp_json("eval_result.json")
            return EvalResult(**payload)
        except Exception:
            if result.returncode != 0:
                return EvalResult(
                    score=0.0,
                    tests_pass=False,
                    constraints_ok=False,
                    latency_ms=None,
                    latency_delta_pct=None,
                    regressions=["eval execution failed"],
                    notes=[result.stderr[-4000:]],
                )
            raise

    def _critique(
        self,
        *,
        score_before: float,
        tests_result: TestsResult,
        eval_result: EvalResult,
    ) -> CriticResult:
        objections: list[str] = []
        severity = "low"
        recommendation = "accept"
        reasoning = "automatic critic review"

        if not tests_result.passed:
            severity = "high"
            recommendation = "reject"
            objections.append("tests failed")

        if not eval_result.constraints_ok:
            severity = "high"
            recommendation = "reject"
            objections.append("constraints failed")

        if eval_result.score < score_before:
            severity = "high"
            recommendation = "reject"
            objections.append("score regressed")

        if eval_result.score == score_before:
            severity = "medium"
            recommendation = "reject"
            objections.append("score did not improve")

        critic = CriticResult(
            severity=severity,
            objections=objections,
            recommendation=recommendation,
            reasoning=reasoning,
        )
        self.store.write_tmp_json("critic_result.json", asdict(critic))
        return critic

    def _accept(self, *, iteration: int, score: float) -> float:
        result = self.runner.run(
            ["bash", "scripts/accept_change.sh", f"accepted iteration {iteration}"]
        )
        if result.returncode != 0:
            raise RuntimeError(f"accept_change failed: {result.stderr}")
        self.store.save_baseline(score=score, iteration=iteration)
        return score

    def _reject_and_rollback(self) -> None:
        result = self.runner.run(["bash", "scripts/rollback_change.sh"])
        if result.returncode != 0:
            raise RuntimeError(f"rollback failed: {result.stderr}")

    def _archive(
        self,
        *,
        iteration: int,
        result_row: ResultRow,
        decision_reason: str,
        tests_result: TestsResult,
        eval_result: EvalResult,
        critic_result: CriticResult,
    ) -> None:
        self.store.append_result_row(result_row)

        decision_md = f"""
- decision: {result_row.status}
- decision_code: {result_row.decision_code}
- score_before: {result_row.score_before}
- score_after: {result_row.score_after}
- score_delta: {result_row.score_delta}
- tests_pass: {str(result_row.tests_pass).lower()}
- constraints_ok: {str(result_row.constraints_ok).lower()}
- critic_severity: {critic_result.severity}
- critic_recommendation: {critic_result.recommendation}
- changed_files_count: {result_row.changed_files_count}
- change_summary: {result_row.change_summary}
- reason: {decision_reason}
        """.strip()

        self.store.append_decision_block(iteration=iteration, content=decision_md)

        self._write_iteration_report(
            iteration=iteration,
            result_row=result_row,
            decision_reason=decision_reason,
            tests_result=tests_result,
            eval_result=eval_result,
            critic_result=critic_result,
        )

    def _write_iteration_report(
        self,
        *,
        iteration: int,
        result_row: ResultRow,
        decision_reason: str,
        tests_result: TestsResult,
        eval_result: EvalResult,
        critic_result: CriticResult,
    ) -> None:
        report = f"""# Iteration {iteration}

## Summary
- hypothesis: {result_row.hypothesis_id}
- decision: {result_row.status}
- decision_code: {result_row.decision_code}
- baseline_before: {result_row.score_before}
- score_after: {result_row.score_after}
- score_delta: {result_row.score_delta}

## Change
- changed_files_count: {result_row.changed_files_count}
- change_summary: {result_row.change_summary}

## Verification
- tests_pass: {str(tests_result.passed).lower()}
- constraints_ok: {str(eval_result.constraints_ok).lower()}
- critic_severity: {critic_result.severity}
- critic_recommendation: {critic_result.recommendation}

## Notes
- reason: {decision_reason}
- rollback_reason: {result_row.rollback_reason}
"""
        self.store.write_text(
            f"reports/iteration/iteration-{iteration:03d}.md",
            report,
        )

    def write_final_report(self) -> None:
        self.runner.run(["python", "scripts/make_final_report.py"])

    def _now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
11. CodexAdapter 최소 실동 버전

이전 문서의 초안을 약간 보강한다.

파일: orchestrator/codex_adapter.py

from __future__ import annotations

import json
from pathlib import Path

from orchestrator.command_runner import CommandRunner
from orchestrator.models import ImplementerResult


class CodexAdapter:
    def __init__(self, root: Path, runner: CommandRunner) -> None:
        self.root = root
        self.runner = runner

    def build_input_bundle(self) -> None:
        self.runner.run(["python", "scripts/build_implementer_input.py"])

    def run_implement(self) -> ImplementerResult:
        self.build_input_bundle()

        result = self.runner.run(["bash", "scripts/run_codex_implement.sh"])
        if result.returncode != 0:
            raise RuntimeError(f"Codex implement failed: {result.stderr}")

        payload_path = self.root / "tmp" / "implementer_result.json"
        if not payload_path.exists():
            raise RuntimeError("Missing tmp/implementer_result.json")

        payload = json.loads(payload_path.read_text(encoding="utf-8"))

        required = [
            "changed_files",
            "change_summary",
            "why_this_change",
            "verification_commands_run",
            "notes",
        ]
        for key in required:
            if key not in payload:
                raise RuntimeError(f"Missing key in implementer_result.json: {key}")

        payload.setdefault("scope_respected", True)
        payload.setdefault("forbidden_paths_touched", [])
        payload.setdefault("estimated_risk", "unknown")

        return ImplementerResult(**payload)
12. main.py End-to-End 코드 뼈대

파일: orchestrator/main.py

from __future__ import annotations

from pathlib import Path

from orchestrator.codex_adapter import CodexAdapter
from orchestrator.command_runner import CommandRunner
from orchestrator.config import load_config
from orchestrator.decision_engine import DecisionEngine
from orchestrator.file_store import FileStore
from orchestrator.iteration_service import IterationService


def main() -> int:
    root = Path.cwd()
    config = load_config()
    store = FileStore(root)
    runner = CommandRunner(root)
    decision_engine = DecisionEngine()
    codex_adapter = CodexAdapter(root=root, runner=runner)

    service = IterationService(
        root=root,
        config=config,
        store=store,
        runner=runner,
        decision_engine=decision_engine,
        codex_adapter=codex_adapter,
    )

    baseline = store.load_baseline()
    no_improvement_streak = 0

    for iteration in range(1, config.max_iterations + 1):
        result = service.run(iteration=iteration, baseline=baseline)

        print(
            f"[iteration={iteration}] decision={result.decision} "
            f"code={result.decision_code} "
            f"score_before={result.score_before} "
            f"score_after={result.score_after}"
        )

        if result.new_baseline > baseline:
            no_improvement_streak = 0
        else:
            no_improvement_streak += 1

        baseline = result.new_baseline

        if config.target_score is not None and baseline >= config.target_score:
            print(f"[orchestrator] target score reached: {baseline}")
            break

        if result.decision == "hold" and config.stop_on_hold:
            print("[orchestrator] stopping on hold")
            break

        if no_improvement_streak >= config.max_no_improvement_streak:
            print("[orchestrator] stopping due to no improvement streak")
            break

    service.write_final_report()
    print("[orchestrator] final report written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
13. StateMachine 클래스 보강

파일: orchestrator/state_machine.py

from __future__ import annotations

from datetime import datetime, timezone

from orchestrator.enums import Phase
from orchestrator.models import IterationState


class IterationStateMachine:
    def __init__(self, state: IterationState) -> None:
        self.state = state

    def set_phase(self, phase: Phase) -> None:
        self.state.phase = phase.value
        self.state.last_updated = self._now()

    def mark_decision(self, decision: str) -> None:
        self.state.decision = decision
        self.state.last_updated = self._now()

    def _now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

초기에는 단순하지만,
추후 phase 전이 유효성 검사도 넣을 수 있다.

예:

PLAN 없이 IMPLEMENT 금지
RUN_EVAL 없이 DECIDE 금지
14. reporting.py로 분리하는 다음 단계

현재 _archive() 안에 보고서/기록이 들어있지만,
확장 시 아래처럼 분리하는 게 좋다.

ReportingService
├─ append_result_row()
├─ append_decision()
├─ write_iteration_report()
├─ update_memory()
└─ write_final_report()

초기에는 IterationService 안에 있어도 괜찮지만,
커질수록 분리하는 게 낫다.

15. 초기 구현에서 일부 bash에 남기는 이유

질문이 생길 수 있다.

왜 Python 오케스트레이터인데 tests/eval/rollback/accept 를 bash로 남기냐?

이유는 간단하다.

이미 검증된 shell 유틸을 재사용 가능
전환 리스크 감소
오케스트레이터 책임을 명확하게 유지 가능

즉:

Python은 흐름 제어
bash는 실행 도구

이 구조가 점진 이전에 가장 적합하다.

16. End-to-End 실행 흐름 정리

최종적으로 python -m orchestrator.main 을 실행하면
아래 순서로 돈다.

main.py
  ↓
IterationService.run()
  ↓
load context
  ↓
explore
  ↓
plan
  ↓
codex_adapter.run_implement()
  ↓
bash scripts/run_tests.sh
  ↓
bash scripts/run_eval.sh
  ↓
auto critic
  ↓
decision_engine.decide()
  ↓
accept_change.sh or rollback_change.sh
  ↓
append results / decisions / reports
  ↓
return IterationRunResult
17. 최소 동작 체크포인트

이 구조를 구현한 뒤 아래를 확인하면 된다.

 python -m orchestrator.main --max-iterations 1 실행 가능
 agent/ITERATION_STATE.json phase가 갱신됨
 tmp/implementer_result.json 생성됨
 tmp/tests_result.json 또는 fallback 생성됨
 tmp/eval_result.json 생성됨
 agent/RESULTS.tsv 에 row 추가됨
 agent/DECISIONS.md 에 블록 추가됨
 reports/iteration/iteration-001.md 생성됨
 accept 시 baseline 갱신됨
 reject 시 rollback 수행됨
18. 흔한 문제와 대응
18.1 Implementer JSON 누락

대응:

CodexAdapter에서 필수 필드 검증
없으면 즉시 예외
18.2 eval_result.json 미생성

대응:

_run_eval() fallback 처리
실패 시 reject 가능한 구조 유지
18.3 tests_result.json 미생성

대응:

_run_tests() 에서 command result 기반 fallback 생성
18.4 baseline 오염

대응:

_accept() 에서만 baseline 저장
reject 경로에서는 baseline 그대로 유지
18.5 결과 기록 중간 실패

대응:

archive 단계 예외를 별도로 잡아 보강 가능
장기적으로 ReportingService 분리 권장
19. 현재 버전의 한계

이 문서의 코드는 "실동 뼈대"다.
아직 완전 제품은 아니다.

한계:

explore / plan 이 아직 단순함
critic이 자동 규칙 기반임
Codex CLI 실제 호출 부분은 환경별 치환 필요
memory update가 아직 얕음
change budget / forbidden 검사 통합이 약함

하지만 중요한 건:

이제 구조가 "설명"이 아니라 "구현 가능한 코드 단위"까지 내려왔다는 점이다.

20. 다음 리팩터링 우선순위

이후 보강 순서는 아래가 좋다.

ReportingService 분리
MemoryService 분리
PlannerService / ExplorerService 분리
ChangeGuardService 추가
CriticService 고도화
CodexAdapter 실제 CLI 환경 대응
MCPPolicyService 추가
21. 핵심 요약

이 문서의 핵심은 아래다.

IterationService 는 iteration 하나를 end-to-end로 실행하는 핵심 서비스다
Python 오케스트레이터는 이제 실제 코드 뼈대를 가질 수 있다
초기에는 explore/plan/critic도 단순 로직으로 충분히 시작 가능하다
accept / reject / rollback / archive가 하나의 서비스 안에서 연결된다
main.py 는 반복 횟수와 종료 조건만 관리하면 된다
이 구조가 있으면 bash 기반 실험 단계를 Python 중심 구조로 점진 이전할 수 있다

즉 현재 상태는 다음처럼 요약된다.

설계 문서 단계
→ Python 구조 정의
→ IterationService 뼈대 구현
→ End-to-End 오케스트레이터 실행 가능

이제부터는 "문서 설계"보다
실제 템플릿 코드 파일 묶음으로 넘어가도 되는 단계다.


다음 문서는 `ReportingService / MemoryService / ChangeGuardService 분리 설계 + 코드 초안`으로 이어가는 흐름이 가장 좋다.
다음 문서 작성
# 다음 단계 문서 10
# ReportingService / MemoryService / ChangeGuardService 분리 설계 + 코드 초안
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 현재 `IterationService` 안에 뭉쳐 있는 보조 책임들을
명확히 분리하기 위한 설계 문서다.

이번 문서에서 다룰 대상:

1. `ReportingService`
2. `MemoryService`
3. `ChangeGuardService`

핵심 목표는 다음과 같다.

- `IterationService` 를 더 얇고 읽기 쉽게 만든다
- 기록/메모리/변경 검증을 독립 책임으로 분리한다
- 테스트 가능한 서비스 단위로 나눈다
- 이후 UI, 대시보드, 다중 정책, 더 정교한 메모리 전략으로 확장하기 쉽게 만든다

즉 이번 문서는
"오케스트레이터가 너무 많은 일을 하지 않게 만드는 리팩터링 문서"다.

---

## 1. 왜 서비스 분리가 필요한가

현재 `IterationService` 는 많은 일을 한다.

예:
- 결과 row append
- decision markdown append
- iteration report 작성
- final report 생성
- memory 갱신
- forbidden path 검사
- diff budget 검사

이 상태를 계속 유지하면 아래 문제가 생긴다.

### 1.1 책임이 과도하게 많아짐
`IterationService` 가 iteration 흐름 제어 외에도
기록/검증/메모리까지 모두 담당한다.

### 1.2 테스트가 어려워짐
예를 들어 "memory 갱신 로직만 따로 테스트" 하기가 어려워진다.

### 1.3 정책 변경이 불편함
예:
- 메모리 압축 전략 바꾸기
- final report 형식 바꾸기
- change budget 정책 바꾸기

이런 변경이 iteration 흐름 코드와 섞이게 된다.

### 1.4 이후 다중 프로젝트 / 멀티 에이전트 확장이 어려움
서비스가 분리되어 있어야
프로젝트별 정책, 리포트 포맷, 메모리 전략을 쉽게 바꿀 수 있다.

---

## 2. 분리 후 목표 구조

권장 구조는 아래와 같다.

```text
IterationService
├─ context load
├─ explore
├─ plan
├─ implement
├─ tests
├─ eval
├─ critique
├─ decide
├─ accept/reject
└─ delegate:
   ├─ ReportingService
   ├─ MemoryService
   └─ ChangeGuardService

즉:

IterationService = 흐름 제어
ReportingService = 기록/리포트
MemoryService = 요약 기억
ChangeGuardService = 변경 검증/안전장치
3. 서비스별 역할 정의
3.1 ReportingService
책임
RESULTS.tsv append
DECISIONS.md append
reports/iteration/*.md 생성
reports/final/final_report.md 생성
하지 말아야 할 일
accept/reject 판단
rollback 실행
Codex 호출
정책 결정

즉:

ReportingService는 "기록"만 한다.

3.2 MemoryService
책임
MEMORY.md 갱신
accepted/rejected 패턴 요약
risk / strategy note 정리
오래된 메모리 압축
하지 말아야 할 일
raw log 저장
baseline 갱신
tests/eval 실행
Git 조작

즉:

MemoryService는 "다음 iteration을 위한 요약 기억"만 담당한다.

3.3 ChangeGuardService
책임
forbidden path 수정 여부 검사
change scope 준수 여부 검사
changed files count 검사
diff line budget 검사
필요 시 reject 사유 제공
하지 말아야 할 일
실제 rollback 실행
accept 결정
보고서 작성

즉:

ChangeGuardService는 "변경이 안전 규칙 안에 있는지 검사"한다.

4. 권장 파일 구조
orchestrator/
├─ reporting.py
├─ memory_service.py
├─ change_guard.py
├─ iteration_service.py
├─ models.py
├─ file_store.py
├─ decision_engine.py
├─ command_runner.py
└─ ...
5. 모델 확장

서비스 분리를 위해 몇 개 모델을 추가하는 게 좋다.

파일: orchestrator/models.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChangeGuardResult:
    ok: bool
    forbidden_paths_touched: list[str] = field(default_factory=list)
    out_of_scope_files: list[str] = field(default_factory=list)
    changed_files_count: int = 0
    diff_lines: int = 0
    reason_code: str = ""
    reason: str = ""


@dataclass
class MemoryUpdate:
    accepted_patterns: list[str] = field(default_factory=list)
    rejected_patterns: list[str] = field(default_factory=list)
    known_risks: list[str] = field(default_factory=list)
    strategy_notes: list[str] = field(default_factory=list)


@dataclass
class DecisionSummary:
    iteration: int
    status: str
    decision_code: str
    decision_reason: str
    hypothesis_id: str
    score_before: float
    score_after: float
    score_delta: float
    tests_pass: bool
    constraints_ok: bool
    critic_severity: str
    critic_recommendation: str
    changed_files_count: int
    change_summary: str
    rollback_reason: str = ""
6. ReportingService 설계
6.1 책임 상세

ReportingService는 아래 메서드를 가지면 좋다.

append_result_row(row)
append_decision(summary)
write_iteration_report(...)
write_final_report()
6.2 입력 원칙

가능한 한 iteration 결과를 다 계산한 다음,
ReportingService에는 "정리된 결과"만 넘긴다.

즉:

service 내부에서 복잡한 판단을 하지 않음
formatting과 저장만 담당
6.3 ReportingService 초안

파일: orchestrator/reporting.py

from __future__ import annotations

from pathlib import Path

from orchestrator.file_store import FileStore
from orchestrator.models import (
    CriticResult,
    DecisionSummary,
    EvalResult,
    ResultRow,
    TestsResult,
)


class ReportingService:
    def __init__(self, store: FileStore) -> None:
        self.store = store

    def append_result_row(self, row: ResultRow) -> None:
        self.store.append_result_row(row)

    def append_decision(self, summary: DecisionSummary) -> None:
        content = f"""
- decision: {summary.status}
- decision_code: {summary.decision_code}
- score_before: {summary.score_before}
- score_after: {summary.score_after}
- score_delta: {summary.score_delta}
- tests_pass: {str(summary.tests_pass).lower()}
- constraints_ok: {str(summary.constraints_ok).lower()}
- critic_severity: {summary.critic_severity}
- critic_recommendation: {summary.critic_recommendation}
- changed_files_count: {summary.changed_files_count}
- change_summary: {summary.change_summary}
- reason: {summary.decision_reason}
- rollback_reason: {summary.rollback_reason}
        """.strip()

        self.store.append_decision_block(
            iteration=summary.iteration,
            content=content,
        )

    def write_iteration_report(
        self,
        *,
        iteration: int,
        summary: DecisionSummary,
        tests_result: TestsResult,
        eval_result: EvalResult,
        critic_result: CriticResult,
    ) -> None:
        text = f"""# Iteration {iteration}

## Summary
- hypothesis: {summary.hypothesis_id}
- decision: {summary.status}
- decision_code: {summary.decision_code}
- baseline_before: {summary.score_before}
- score_after: {summary.score_after}
- score_delta: {summary.score_delta}

## Change
- changed_files_count: {summary.changed_files_count}
- change_summary: {summary.change_summary}

## Verification
- tests_pass: {str(tests_result.passed).lower()}
- constraints_ok: {str(eval_result.constraints_ok).lower()}
- critic_severity: {critic_result.severity}
- critic_recommendation: {critic_result.recommendation}

## Notes
- reason: {summary.decision_reason}
- rollback_reason: {summary.rollback_reason}
"""
        self.store.write_text(
            f"reports/iteration/iteration-{iteration:03d}.md",
            text,
        )

    def write_final_report(self) -> None:
        """
        초기 버전은 기존 스크립트를 호출한다.
        이후에는 여기서 완전 Python 구현으로 대체 가능하다.
        """
        # 단순 위임 방식
        from subprocess import run

        run(["python", "scripts/make_final_report.py"], check=False)
7. MemoryService 설계
7.1 MemoryService 핵심 철학

메모리는 raw log가 아니다.
메모리는 "다음 iteration 품질을 높이기 위한 압축 지식"이다.

즉 좋은 MemoryService는:

짧고
재사용 가능하고
중복이 적고
다음 행동에 도움 되는 내용을 남긴다
7.2 책임 상세
accepted 패턴 추가
rejected 패턴 추가
known risks 갱신
strategy note 갱신
중복 제거
길이 제한 유지
7.3 권장 정책
길이 제한

각 섹션은 최대 8개 정도 유지

중복 제거

동일 문장은 1번만 남김

우선순위

최근 항목이 먼저 오도록 배치

placeholder 처리

비어 있으면 - 유지 가능

7.4 MemoryService 초안

파일: orchestrator/memory_service.py

from __future__ import annotations

from orchestrator.file_store import FileStore
from orchestrator.models import DecisionSummary, MemoryUpdate


class MemoryService:
    def __init__(self, store: FileStore, max_items_per_section: int = 8) -> None:
        self.store = store
        self.max_items_per_section = max_items_per_section

    def load_sections(self) -> dict[str, list[str]]:
        try:
            text = self.store.read_text("agent/MEMORY.md")
        except Exception:
            text = (
                "# MEMORY\n\n"
                "## Accepted Patterns\n-\n\n"
                "## Rejected Patterns\n-\n\n"
                "## Known Risks\n-\n\n"
                "## Strategy Notes\n-\n"
            )

        sections = {
            "Accepted Patterns": [],
            "Rejected Patterns": [],
            "Known Risks": [],
            "Strategy Notes": [],
        }

        current = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## "):
                key = stripped[3:].strip()
                current = key if key in sections else None
                continue
            if current and stripped.startswith("- "):
                item = stripped[2:].strip()
                if item and item != "-":
                    sections[current].append(item)

        return sections

    def render_sections(self, sections: dict[str, list[str]]) -> str:
        def dedupe_keep_order(items: list[str]) -> list[str]:
            seen = set()
            out = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    out.append(item)
            return out[: self.max_items_per_section]

        lines = ["# MEMORY", ""]
        ordered_keys = [
            "Accepted Patterns",
            "Rejected Patterns",
            "Known Risks",
            "Strategy Notes",
        ]

        for key in ordered_keys:
            lines.append(f"## {key}")
            values = dedupe_keep_order(sections.get(key, []))
            if values:
                lines.extend(f"- {v}" for v in values)
            else:
                lines.append("-")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def update(self, update: MemoryUpdate) -> None:
        sections = self.load_sections()

        sections["Accepted Patterns"] = update.accepted_patterns + sections["Accepted Patterns"]
        sections["Rejected Patterns"] = update.rejected_patterns + sections["Rejected Patterns"]
        sections["Known Risks"] = update.known_risks + sections["Known Risks"]
        sections["Strategy Notes"] = update.strategy_notes + sections["Strategy Notes"]

        self.store.write_text("agent/MEMORY.md", self.render_sections(sections))

    def build_update(
        self,
        *,
        summary: DecisionSummary,
        risk_note: str = "",
        strategy_note: str = "",
    ) -> MemoryUpdate:
        accepted_patterns: list[str] = []
        rejected_patterns: list[str] = []
        known_risks: list[str] = []
        strategy_notes: list[str] = []

        if summary.status == "accepted":
            accepted_patterns.append(summary.change_summary)

        if summary.status == "rejected":
            rejected_patterns.append(
                f"{summary.change_summary} ({summary.decision_code})"
            )

        if summary.decision_reason:
            known_risks.append(summary.decision_reason)

        if risk_note:
            known_risks.append(risk_note)

        if strategy_note:
            strategy_notes.append(strategy_note)

        return MemoryUpdate(
            accepted_patterns=accepted_patterns,
            rejected_patterns=rejected_patterns,
            known_risks=known_risks,
            strategy_notes=strategy_notes,
        )
8. ChangeGuardService 설계
8.1 ChangeGuardService가 필요한 이유

현재까지의 구조에서 implement 이후 바로 tests/eval로 가면
아래 문제가 생긴다.

forbidden file을 수정했는데 뒤늦게 발견
scope를 과도하게 넘은 변경을 감지 못함
변경 파일 수가 너무 많은데 통제 안 됨
diff line 폭증

그래서 implement 직후에
"이 변경이 규칙상 허용 가능한지"를 먼저 검사해야 한다.

8.2 책임 상세

ChangeGuardService는 아래를 검사한다.

forbidden path touched?
allowed scope 밖 수정?
changed files count 초과?
diff line count 초과?
8.3 출력

ChangeGuardResult

8.4 원칙

ChangeGuard는 reject를 직접 실행하지 않는다.
그냥 "위험/위반 결과"를 반환한다.

8.5 ChangeGuardService 초안

파일: orchestrator/change_guard.py

from __future__ import annotations

import subprocess
from pathlib import Path

from orchestrator.models import ChangeGuardResult


class ChangeGuardService:
    def __init__(
        self,
        root: Path,
        *,
        forbidden_paths: set[str] | None = None,
        max_changed_files: int = 3,
        max_diff_lines: int = 120,
    ) -> None:
        self.root = root
        self.forbidden_paths = forbidden_paths or {
            "eval/frozen_eval.py",
            "eval/fixtures.json",
            "eval/baseline.json",
            "agent/RESULTS.tsv",
            "agent/DECISIONS.md",
        }
        self.max_changed_files = max_changed_files
        self.max_diff_lines = max_diff_lines

    def _git_diff_name_only(self) -> list[str]:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def _git_diff_numstat_total(self) -> int:
        result = subprocess.run(
            ["git", "diff", "--numstat"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        total = 0
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    total += int(parts[0]) + int(parts[1])
                except ValueError:
                    pass
        return total

    def check(self, *, allowed_scope: list[str]) -> ChangeGuardResult:
        changed_files = self._git_diff_name_only()
        diff_lines = self._git_diff_numstat_total()

        forbidden_touched = sorted(set(changed_files) & self.forbidden_paths)

        allowed_scope_set = set(allowed_scope)
        out_of_scope = sorted(
            f for f in changed_files
            if f not in allowed_scope_set and f not in self.forbidden_paths
        )

        if forbidden_touched:
            return ChangeGuardResult(
                ok=False,
                forbidden_paths_touched=forbidden_touched,
                out_of_scope_files=out_of_scope,
                changed_files_count=len(changed_files),
                diff_lines=diff_lines,
                reason_code="FORBIDDEN_FILE",
                reason="forbidden file was modified",
            )

        if out_of_scope:
            return ChangeGuardResult(
                ok=False,
                forbidden_paths_touched=forbidden_touched,
                out_of_scope_files=out_of_scope,
                changed_files_count=len(changed_files),
                diff_lines=diff_lines,
                reason_code="SCOPE_VIOLATION",
                reason="change exceeded allowed scope",
            )

        if len(changed_files) > self.max_changed_files:
            return ChangeGuardResult(
                ok=False,
                forbidden_paths_touched=[],
                out_of_scope_files=[],
                changed_files_count=len(changed_files),
                diff_lines=diff_lines,
                reason_code="SCOPE_VIOLATION",
                reason="changed files count exceeded budget",
            )

        if diff_lines > self.max_diff_lines:
            return ChangeGuardResult(
                ok=False,
                forbidden_paths_touched=[],
                out_of_scope_files=[],
                changed_files_count=len(changed_files),
                diff_lines=diff_lines,
                reason_code="SCOPE_VIOLATION",
                reason="diff line budget exceeded",
            )

        return ChangeGuardResult(
            ok=True,
            forbidden_paths_touched=[],
            out_of_scope_files=[],
            changed_files_count=len(changed_files),
            diff_lines=diff_lines,
            reason_code="",
            reason="",
        )
9. IterationService에 서비스 주입

이제 IterationService 생성자에 아래를 추가한다.

reporting_service: ReportingService
memory_service: MemoryService
change_guard_service: ChangeGuardService

예:

class IterationService:
    def __init__(
        self,
        *,
        root: Path,
        config: OrchestratorConfig,
        store: FileStore,
        runner: CommandRunner,
        decision_engine: DecisionEngine,
        codex_adapter: CodexAdapter,
        reporting_service: ReportingService,
        memory_service: MemoryService,
        change_guard_service: ChangeGuardService,
    ) -> None:
        self.root = root
        self.config = config
        self.store = store
        self.runner = runner
        self.decision_engine = decision_engine
        self.codex_adapter = codex_adapter
        self.reporting_service = reporting_service
        self.memory_service = memory_service
        self.change_guard_service = change_guard_service
10. IterationService implement 이후 guard 검사 추가

Implement 직후에 아래 흐름을 넣는다.

implement
→ change_guard.check()
→ guard fail이면 early reject candidate
→ tests/eval/decision에 반영

예시 코드 조각:

allowed_scope = self.store.read_tmp_json("planner_result.json").get("change_scope", [])
guard_result = self.change_guard_service.check(allowed_scope=allowed_scope)

if not guard_result.ok:
    implementer_result.scope_respected = False
    implementer_result.forbidden_paths_touched = guard_result.forbidden_paths_touched
11. DecisionEngine과 ChangeGuard 연결

기존 DecisionEngine 은 이미

forbidden file
scope violation

을 처리하도록 되어 있으므로,
ChangeGuard 결과를 ImplementerResult 에 주입하면 된다.

예:

implementer_result.scope_respected = guard_result.ok and not guard_result.out_of_scope_files
implementer_result.forbidden_paths_touched = guard_result.forbidden_paths_touched

또는 DecisionEngine 에 guard_result 를 직접 넘겨도 된다.

초기 버전은 ImplementerResult에 합치는 편이 단순하다.

12. ReportingService / MemoryService 적용 후 archive 단순화

기존 _archive() 내부는 길었다.
이제 아래처럼 단순화할 수 있다.

def _archive(
    self,
    *,
    iteration: int,
    result_row: ResultRow,
    summary: DecisionSummary,
    tests_result: TestsResult,
    eval_result: EvalResult,
    critic_result: CriticResult,
) -> None:
    self.reporting_service.append_result_row(result_row)
    self.reporting_service.append_decision(summary)
    self.reporting_service.write_iteration_report(
        iteration=iteration,
        summary=summary,
        tests_result=tests_result,
        eval_result=eval_result,
        critic_result=critic_result,
    )

    memory_update = self.memory_service.build_update(
        summary=summary,
        risk_note="",
        strategy_note="prefer small, low-risk follow-up changes" if summary.status == "accepted" else "",
    )
    self.memory_service.update(memory_update)

이렇게 되면 IterationService 는 흐름 제어에 훨씬 집중할 수 있다.

13. main.py에 서비스 생성 추가

파일: orchestrator/main.py

from orchestrator.change_guard import ChangeGuardService
from orchestrator.memory_service import MemoryService
from orchestrator.reporting import ReportingService

그리고 생성 부분:

reporting_service = ReportingService(store=store)
memory_service = MemoryService(store=store)
change_guard_service = ChangeGuardService(root=root)

service = IterationService(
    root=root,
    config=config,
    store=store,
    runner=runner,
    decision_engine=decision_engine,
    codex_adapter=codex_adapter,
    reporting_service=reporting_service,
    memory_service=memory_service,
    change_guard_service=change_guard_service,
)
14. 서비스 분리 후 얻는 장점
14.1 IterationService 단순화

핵심 흐름만 읽으면 되므로 디버깅이 쉬워진다.

14.2 독립 테스트 가능
ReportingService 단위 테스트
MemoryService 단위 테스트
ChangeGuardService 단위 테스트
14.3 정책 변경 용이

예:

메모리 최대 길이 변경
diff budget 변경
report 템플릿 변경
14.4 장기 확장성 향상

이후:

DB-backed reporting
vector memory
UI dashboard
project-level policy override

로 가기 쉬워진다.

15. 권장 단위 테스트 포인트
15.1 ReportingService

테스트:

RESULTS.tsv 헤더 생성
result row append 정상 여부
decision block append 정상 여부
iteration report 파일 생성 여부
15.2 MemoryService

테스트:

placeholder 상태에서 정상 렌더링
중복 제거
최대 항목 수 제한
accepted/rejected 올바른 섹션 반영
15.3 ChangeGuardService

테스트:

forbidden file 수정 감지
out-of-scope 파일 감지
changed files count budget 감지
diff lines budget 감지
정상 변경은 ok=True
16. 향후 더 분리할 수 있는 서비스

이 문서 이후 더 잘게 나누고 싶다면:

16.1 PlannerService
hypothesis 선택
planner_result 생성
16.2 CriticService
규칙 기반 critic
LLM critic
hybrid critic
16.3 BaselineService
baseline 로드/갱신
accept된 baseline history 관리
16.4 PolicyService
프로젝트별 제한 정책
MCP 도구 권한 정책
mode별 허용 범위

하지만 지금 단계에서는
Reporting / Memory / ChangeGuard 세 개만 분리해도 충분히 크다.

17. 현실적인 추천 리팩터링 순서

아래 순서가 가장 안전하다.

ReportingService 분리
MemoryService 분리
ChangeGuardService 분리
IterationService 에 주입
_archive() 간소화
implement 직후 guard 검사 추가
단위 테스트 작성

이 순서가 좋은 이유는:

기록/메모리/검사가 서로 의존성이 낮기 때문이다.
18. 핵심 요약

이번 문서의 핵심은 아래다.

IterationService 는 너무 많은 책임을 가지면 안 된다
기록은 ReportingService
요약 기억은 MemoryService
변경 검증은 ChangeGuardService
이 세 서비스를 분리하면 오케스트레이터가 훨씬 읽기 쉽고 테스트하기 쉬워진다
이후 UI/DB/대시보드/정교한 정책 확장도 훨씬 쉬워진다

즉 현재 구조는 아래처럼 진화한다.

단일 큰 IterationService
→
흐름 제어 IterationService
+ ReportingService
+ MemoryService
+ ChangeGuardService

이 단계까지 오면
설계가 꽤 실전적인 서비스 구조로 들어온 상태다.


다음 문서는 `PlannerService / CriticService / BaselineService 분리 설계 + IterationService 리팩터링 최종판`으로 이어가는 게 가장 자연스럽다.
다음문서 작성
# 다음 단계 문서 11
# PlannerService / CriticService / BaselineService 분리 설계 + IterationService 리팩터링 최종판
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 현재까지 분리한 구조를 한 단계 더 밀어붙여서,
반복개선 시스템의 핵심 운영 서비스들을 거의 완성형에 가깝게 정리하는 문서다.

이번 문서 범위:

1. `PlannerService`
2. `CriticService`
3. `BaselineService`
4. `IterationService` 최종 리팩터링 구조
5. 서비스 간 의존 관계 정리
6. 최종 실행 흐름 재정의

이 문서의 목표는
단순히 서비스를 더 많이 만드는 것이 아니라,
**각 서비스가 “딱 하나의 책임”만 갖도록 정리해서
IterationService를 정말 오케스트레이터답게 만드는 것**이다.

---

## 1. 현재까지의 구조와 남은 문제

이전 단계까지 분리된 구조는 아래와 같다.

```text
IterationService
├─ ReportingService
├─ MemoryService
└─ ChangeGuardService

이 구조만으로도 많이 나아졌지만,
아직 IterationService 안에는 아래 책임이 남아 있다.

hypothesis 선택
plan 생성
critic 생성
baseline 갱신 결정 및 관리

즉 아직도 IterationService 는
흐름 제어 외에 “내용 생성/판단 보조” 책임을 일부 갖고 있다.

이 문서에서는 그 부분까지 떼어낸다.

2. 최종 목표 구조

권장 최종 구조는 아래와 같다.

IterationService
├─ PlannerService
├─ CriticService
├─ BaselineService
├─ ReportingService
├─ MemoryService
├─ ChangeGuardService
├─ DecisionEngine
├─ CodexAdapter
├─ FileStore
└─ CommandRunner

즉:

IterationService = 흐름만 조율
PlannerService = hypothesis 선택 + plan 산출
CriticService = 결과에 대한 비판/리스크 분석
BaselineService = baseline 조회/갱신/정책 관리
DecisionEngine = 최종 accept/reject/hold 판단
나머지 서비스 = 보조 계층

이 단계가 되면 IterationService 는 진짜로
“복잡한 일을 직접 하는 클래스”가 아니라
단계들을 연결하는 coordinator 가 된다.

3. PlannerService 설계
3.1 PlannerService의 역할

PlannerService는 다음을 담당한다.

현재 hypothesis 후보를 읽는다
이번 iteration에 실행할 hypothesis를 고른다
그것을 작은 변경 단위의 plan으로 바꾼다
planner_result.json 또는 내부 모델로 반환한다

즉 PlannerService는:

"무엇을, 얼마나 작은 범위로, 어떤 방식으로 시도할지"
결정하는 서비스다.

3.2 PlannerService가 하지 말아야 할 일
실제 코드 수정
tests 실행
eval 실행
accept/reject 결정
baseline 갱신

즉 Planner는 “계획”만 담당한다.

3.3 PlannerService 입력

권장 입력:

IterationContext
최근 MEMORY.md
최근 RESULTS.tsv 일부 요약
현재 baseline
optional: Explorer가 만든 hypothesis set

초기 버전에서는
agent/HYPOTHESES.md 와 agent/PLAN.md 를 source of truth로 써도 충분하다.

3.4 PlannerService 출력 모델

파일: orchestrator/models.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlannerResult:
    selected_hypothesis: str
    change_scope: list[str] = field(default_factory=list)
    planned_change: str = ""
    expected_effect: str = ""
    risks: list[str] = field(default_factory=list)
    tests_to_run: list[str] = field(default_factory=list)
    reject_conditions: list[str] = field(default_factory=list)
3.5 PlannerService 초기 구현 전략

초기 구현에서는 아주 공격적으로 자동화할 필요가 없다.

권장 초기 전략:

agent/HYPOTHESES.md 에서 status: selected 인 항목 사용
없으면 H-001 fallback
agent/PLAN.md 를 읽어서 최소 계획 구조 생성
tmp/planner_result.json 에 기록

즉 처음엔 “AI planner”라기보다
파일 기반 planner adapter 로 시작해도 충분하다.

3.6 PlannerService 초안

파일: orchestrator/planner_service.py

from __future__ import annotations

from dataclasses import asdict
import re

from orchestrator.file_store import FileStore
from orchestrator.models import IterationContext, PlannerResult


class PlannerService:
    def __init__(self, store: FileStore) -> None:
        self.store = store

    def build_plan(self, *, context: IterationContext) -> PlannerResult:
        hypothesis_id = self._select_hypothesis(context.hypotheses)
        change_scope = self._extract_change_scope(context.plan)
        tests_to_run = self._extract_tests_to_run(context.plan)

        result = PlannerResult(
            selected_hypothesis=hypothesis_id,
            change_scope=change_scope or ["src/search/normalize.py"],
            planned_change="focused change from PLAN.md",
            expected_effect="small measurable improvement",
            risks=["scope drift", "score regression"],
            tests_to_run=tests_to_run or [
                "bash scripts/run_tests.sh",
                "bash scripts/run_eval.sh",
            ],
            reject_conditions=[
                "tests fail",
                "constraints fail",
                "score regression",
            ],
        )

        self.store.write_tmp_json("planner_result.json", asdict(result))
        return result

    def _select_hypothesis(self, hypotheses_text: str) -> str:
        if "status: selected" in hypotheses_text:
            match = re.search(r"-\s*(H-\d+)", hypotheses_text)
            if match:
                return match.group(1)
        match = re.search(r"(H-\d+)", hypotheses_text)
        if match:
            return match.group(1)
        return "H-001"

    def _extract_change_scope(self, plan_text: str) -> list[str]:
        lines = []
        capture = False
        for raw in plan_text.splitlines():
            line = raw.strip()
            if line.lower().startswith("## change scope"):
                capture = True
                continue
            if capture and line.startswith("## "):
                break
            if capture and line.startswith("- "):
                lines.append(line[2:].strip().strip("`"))
        return lines

    def _extract_tests_to_run(self, plan_text: str) -> list[str]:
        lines = []
        capture = False
        for raw in plan_text.splitlines():
            line = raw.strip()
            if line.lower().startswith("## tests to run"):
                capture = True
                continue
            if capture and line.startswith("## "):
                break
            if capture and line.startswith("- "):
                lines.append(line[2:].strip())
        return lines
4. CriticService 설계
4.1 CriticService의 역할

CriticService는 단순히 “반대하는 역할”이 아니다.

실제 책임은 아래다.

점수 개선이 진짜인지 의심한다
hidden regression 가능성을 점검한다
narrow win / fixture overfitting 가능성을 표시한다
scope 초과/과도한 복잡도 증가를 경고한다
recommendation을 낸다

즉 CriticService는:

"좋아 보이는 결과를 바로 믿지 않게 만드는 안전 필터"

다.

4.2 CriticService가 하지 말아야 할 일
rollback 실행
baseline 갱신
최종 accept/reject 결정
보고서 작성

즉 Critic은 비판 의견만 제공한다.

4.3 CriticService 입력

권장 입력:

score_before
TestsResult
EvalResult
ImplementerResult
optional: ChangeGuardResult
optional: PlannerResult
4.4 CriticService 출력

이미 있는 CriticResult 사용:

@dataclass
class CriticResult:
    severity: str
    objections: list[str]
    recommendation: str
    reasoning: str
4.5 CriticService 초기 구현 철학

초기 버전에서는 LLM critic을 꼭 넣지 않아도 된다.

규칙 기반 critic만으로도 시작 가능하다.

예:

tests fail → high / reject
constraints fail → high / reject
score regression → high / reject
score no improvement → medium / reject
forbidden touched → high / reject
diff too large → medium / hold 또는 reject

즉 CriticService는 처음엔
규칙 기반 critic 으로 충분하다.

4.6 CriticService 초안

파일: orchestrator/critic_service.py

from __future__ import annotations

from orchestrator.models import (
    ChangeGuardResult,
    CriticResult,
    EvalResult,
    ImplementerResult,
    PlannerResult,
    TestsResult,
)


class CriticService:
    def critique(
        self,
        *,
        score_before: float,
        tests_result: TestsResult,
        eval_result: EvalResult,
        implementer_result: ImplementerResult,
        planner_result: PlannerResult,
        guard_result: ChangeGuardResult | None = None,
    ) -> CriticResult:
        objections: list[str] = []
        severity = "low"
        recommendation = "accept"
        reasoning = "automatic critic review completed"

        if not tests_result.passed:
            severity = "high"
            recommendation = "reject"
            objections.append("tests failed")

        if not eval_result.constraints_ok:
            severity = "high"
            recommendation = "reject"
            objections.append("constraints failed")

        if eval_result.score < score_before:
            severity = "high"
            recommendation = "reject"
            objections.append("score regressed")

        if eval_result.score == score_before:
            if severity != "high":
                severity = "medium"
            recommendation = "reject"
            objections.append("score did not improve")

        if guard_result and not guard_result.ok:
            severity = "high"
            recommendation = "reject"
            objections.append(guard_result.reason)

        if len(implementer_result.changed_files) > max(3, len(planner_result.change_scope) + 1):
            if severity == "low":
                severity = "medium"
            if recommendation == "accept":
                recommendation = "accept_with_monitoring"
            objections.append("changed files count is larger than expected scope")

        if implementer_result.estimated_risk == "high" and severity == "low":
            severity = "medium"
            recommendation = "accept_with_monitoring"
            objections.append("implementer estimated risk is high")

        return CriticResult(
            severity=severity,
            objections=objections,
            recommendation=recommendation,
            reasoning=reasoning,
        )
5. BaselineService 설계
5.1 BaselineService가 필요한 이유

기존 구조에서는 baseline 관련 책임이 여기저기 흩어질 수 있다.

예:

baseline 로드
accept 시 baseline 저장
reject 시 baseline 유지
target score 비교
baseline history 관리

이걸 별도 서비스로 빼면 정책이 선명해진다.

5.2 BaselineService 역할
현재 baseline 읽기
accept 시 baseline 갱신
reject/hold 시 baseline 유지
target score 달성 여부 판단
optional: baseline history 저장

즉:

"공식 성능 기준점"을 관리하는 서비스

다.

5.3 BaselineService가 하지 말아야 할 일
tests 실행
eval 실행
Codex 호출
보고서 작성
change guard 검사
5.4 BaselineService 초안

파일: orchestrator/baseline_service.py

from __future__ import annotations

from dataclasses import dataclass

from orchestrator.file_store import FileStore


@dataclass
class BaselineUpdateResult:
    old_baseline: float
    new_baseline: float
    updated: bool


class BaselineService:
    def __init__(self, store: FileStore) -> None:
        self.store = store

    def load(self) -> float:
        return self.store.load_baseline()

    def update_if_accepted(
        self,
        *,
        accepted: bool,
        score: float,
        iteration: int,
        current_baseline: float,
    ) -> BaselineUpdateResult:
        if accepted:
            self.store.save_baseline(score=score, iteration=iteration)
            return BaselineUpdateResult(
                old_baseline=current_baseline,
                new_baseline=score,
                updated=True,
            )

        return BaselineUpdateResult(
            old_baseline=current_baseline,
            new_baseline=current_baseline,
            updated=False,
        )

    def target_reached(self, *, baseline: float, target_score: float | None) -> bool:
        if target_score is None:
            return False
        return baseline >= target_score
6. DecisionEngine과 역할 경계 재정리

이제 역할 경계는 아래처럼 명확해진다.

PlannerService → 무엇을 시도할지 정리
CodexAdapter → 실제 구현 수행
ChangeGuardService → 구현 결과가 규칙 위반인지 검사
CriticService → 결과를 비판적으로 검토
DecisionEngine → 최종 판정
BaselineService → accept된 결과만 기준점으로 반영
ReportingService → 로그/리포트 작성
MemoryService → 요약 기억 갱신

이 구조가 되면 IterationService 는 진짜 orchestration만 남는다.

7. IterationService 최종 책임 재정의

이 시점에서 IterationService 책임은 아래 7개면 충분하다.

현재 iteration 시작
상태 phase 갱신
각 서비스 순서대로 호출
accept/reject 분기
baseline update 위임
reporting/memory 위임
최종 IterationRunResult 반환

즉 IterationService는
"각 서비스의 출력들을 연결하는 coordinator" 다.

8. IterationService 최종판 구조

권장 생성자:

class IterationService:
    def __init__(
        self,
        *,
        root: Path,
        config: OrchestratorConfig,
        store: FileStore,
        runner: CommandRunner,
        planner_service: PlannerService,
        critic_service: CriticService,
        baseline_service: BaselineService,
        reporting_service: ReportingService,
        memory_service: MemoryService,
        change_guard_service: ChangeGuardService,
        decision_engine: DecisionEngine,
        codex_adapter: CodexAdapter,
    ) -> None:
        ...
9. IterationService 최종 run 흐름
load/create state
→ load context
→ planner_service.build_plan()
→ codex_adapter.run_implement()
→ change_guard_service.check()
→ run tests
→ run eval
→ critic_service.critique()
→ decision_engine.decide()
→ accept_change.sh or rollback_change.sh
→ baseline_service.update_if_accepted()
→ reporting_service.append_*
→ memory_service.update()
→ return IterationRunResult

이게 현재 문서 시점의 거의 최종 실전 구조다.

10. IterationService 리팩터링 최종판 초안

파일: orchestrator/iteration_service.py

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from orchestrator.baseline_service import BaselineService
from orchestrator.change_guard import ChangeGuardService
from orchestrator.codex_adapter import CodexAdapter
from orchestrator.command_runner import CommandRunner
from orchestrator.critic_service import CriticService
from orchestrator.decision_engine import DecisionEngine
from orchestrator.enums import Decision, Phase
from orchestrator.file_store import FileStore
from orchestrator.memory_service import MemoryService
from orchestrator.models import (
    EvalResult,
    ImplementerResult,
    IterationContext,
    IterationRunResult,
    IterationState,
    OrchestratorConfig,
    PlannerResult,
    ResultRow,
    TestsResult,
    DecisionSummary,
)
from orchestrator.planner_service import PlannerService
from orchestrator.reporting import ReportingService
from orchestrator.state_machine import IterationStateMachine


class IterationService:
    def __init__(
        self,
        *,
        root: Path,
        config: OrchestratorConfig,
        store: FileStore,
        runner: CommandRunner,
        planner_service: PlannerService,
        critic_service: CriticService,
        baseline_service: BaselineService,
        reporting_service: ReportingService,
        memory_service: MemoryService,
        change_guard_service: ChangeGuardService,
        decision_engine: DecisionEngine,
        codex_adapter: CodexAdapter,
    ) -> None:
        self.root = root
        self.config = config
        self.store = store
        self.runner = runner
        self.planner_service = planner_service
        self.critic_service = critic_service
        self.baseline_service = baseline_service
        self.reporting_service = reporting_service
        self.memory_service = memory_service
        self.change_guard_service = change_guard_service
        self.decision_engine = decision_engine
        self.codex_adapter = codex_adapter

    def run(self, *, iteration: int, baseline: float) -> IterationRunResult:
        state = self._load_or_create_state(
            iteration=iteration,
            baseline=baseline,
            mode=self.config.mode,
        )
        machine = IterationStateMachine(state)
        self.store.save_iteration_state(machine.state)

        try:
            machine.set_phase(Phase.READ_CONTEXT)
            self.store.save_iteration_state(machine.state)
            context = self._load_context()

            machine.set_phase(Phase.PLAN)
            self.store.save_iteration_state(machine.state)
            planner_result = self.planner_service.build_plan(context=context)

            machine.state.selected_hypothesis = planner_result.selected_hypothesis
            self.store.save_iteration_state(machine.state)

            machine.set_phase(Phase.IMPLEMENT)
            self.store.save_iteration_state(machine.state)
            implementer_result = self.codex_adapter.run_implement()

            guard_result = self.change_guard_service.check(
                allowed_scope=planner_result.change_scope
            )
            if not guard_result.ok:
                implementer_result.scope_respected = False
                implementer_result.forbidden_paths_touched = guard_result.forbidden_paths_touched

            machine.set_phase(Phase.RUN_TESTS)
            self.store.save_iteration_state(machine.state)
            tests_result = self._run_tests()
            machine.state.tests_pass = tests_result.passed
            self.store.save_iteration_state(machine.state)

            machine.set_phase(Phase.RUN_EVAL)
            self.store.save_iteration_state(machine.state)
            eval_result = self._run_eval()
            machine.state.candidate_score = eval_result.score
            machine.state.constraints_ok = eval_result.constraints_ok
            self.store.save_iteration_state(machine.state)

            machine.set_phase(Phase.CRITIQUE)
            self.store.save_iteration_state(machine.state)
            critic_result = self.critic_service.critique(
                score_before=baseline,
                tests_result=tests_result,
                eval_result=eval_result,
                implementer_result=implementer_result,
                planner_result=planner_result,
                guard_result=guard_result,
            )

            machine.set_phase(Phase.DECIDE)
            self.store.save_iteration_state(machine.state)
            decision_result = self.decision_engine.decide(
                score_before=baseline,
                eval_result=eval_result,
                tests_result=tests_result,
                critic_result=critic_result,
                implementer_result=implementer_result,
            )
            machine.mark_decision(decision_result.decision)
            self.store.save_iteration_state(machine.state)

            accepted = decision_result.decision == Decision.ACCEPT.value

            if accepted:
                machine.set_phase(Phase.ACCEPT)
                self.store.save_iteration_state(machine.state)
                self._accept(iteration=iteration)
                rollback_reason = ""
                status = "accepted"
            else:
                machine.set_phase(Phase.REJECT)
                self.store.save_iteration_state(machine.state)
                self._reject_and_rollback()
                rollback_reason = decision_result.reason
                status = "rejected"

            baseline_update = self.baseline_service.update_if_accepted(
                accepted=accepted,
                score=eval_result.score,
                iteration=iteration,
                current_baseline=baseline,
            )

            result_row = ResultRow(
                iteration=iteration,
                hypothesis_id=planner_result.selected_hypothesis,
                status=status,
                decision_code=decision_result.decision_code,
                score_before=baseline,
                score_after=eval_result.score,
                score_delta=round(eval_result.score - baseline, 6),
                tests_pass=tests_result.passed,
                constraints_ok=eval_result.constraints_ok,
                critic_severity=critic_result.severity,
                critic_recommendation=critic_result.recommendation,
                changed_files_count=guard_result.changed_files_count or len(implementer_result.changed_files),
                change_summary=implementer_result.change_summary,
                rollback_reason=rollback_reason,
            )

            summary = DecisionSummary(
                iteration=iteration,
                status=status,
                decision_code=decision_result.decision_code,
                decision_reason=decision_result.reason,
                hypothesis_id=planner_result.selected_hypothesis,
                score_before=baseline,
                score_after=eval_result.score,
                score_delta=round(eval_result.score - baseline, 6),
                tests_pass=tests_result.passed,
                constraints_ok=eval_result.constraints_ok,
                critic_severity=critic_result.severity,
                critic_recommendation=critic_result.recommendation,
                changed_files_count=result_row.changed_files_count,
                change_summary=implementer_result.change_summary,
                rollback_reason=rollback_reason,
            )

            machine.set_phase(Phase.ARCHIVE)
            self.store.save_iteration_state(machine.state)

            self.reporting_service.append_result_row(result_row)
            self.reporting_service.append_decision(summary)
            self.reporting_service.write_iteration_report(
                iteration=iteration,
                summary=summary,
                tests_result=tests_result,
                eval_result=eval_result,
                critic_result=critic_result,
            )

            memory_update = self.memory_service.build_update(
                summary=summary,
                risk_note=guard_result.reason if guard_result.reason else "",
                strategy_note="prefer similarly small scoped changes next" if accepted else "",
            )
            self.memory_service.update(memory_update)

            machine.set_phase(Phase.DONE)
            self.store.save_iteration_state(machine.state)

            return IterationRunResult(
                iteration=iteration,
                decision=decision_result.decision,
                decision_code=decision_result.decision_code,
                score_before=baseline,
                score_after=eval_result.score,
                score_delta=round(eval_result.score - baseline, 6),
                new_baseline=baseline_update.new_baseline,
                tests_pass=tests_result.passed,
                constraints_ok=eval_result.constraints_ok,
                hypothesis_id=planner_result.selected_hypothesis,
                change_summary=implementer_result.change_summary,
            )

        except Exception:
            machine.set_phase(Phase.ERROR)
            self.store.save_iteration_state(machine.state)
            raise
11. IterationService 보조 메서드 최종판

위 클래스에 이어서 아래 helper들을 붙인다.

    def _load_or_create_state(self, *, iteration: int, baseline: float, mode: str) -> IterationState:
        try:
            state = self.store.load_iteration_state()
            state.iteration = iteration
            state.mode = mode
            state.phase = Phase.INIT.value
            state.baseline_score = baseline
            state.candidate_score = None
            state.tests_pass = None
            state.constraints_ok = None
            state.decision = None
            state.last_updated = self._now()
            return state
        except Exception:
            return IterationState(
                iteration=iteration,
                mode=mode,
                phase=Phase.INIT.value,
                selected_hypothesis=None,
                baseline_score=baseline,
                candidate_score=None,
                tests_pass=None,
                constraints_ok=None,
                decision=None,
                last_updated=self._now(),
            )

    def _load_context(self) -> IterationContext:
        return self.store.load_iteration_context()

    def _run_tests(self) -> TestsResult:
        result = self.runner.run(["bash", "scripts/run_tests.sh"])
        try:
            payload = self.store.read_tmp_json("tests_result.json")
            return TestsResult(**payload)
        except Exception:
            return TestsResult(
                passed=(result.returncode == 0),
                summary=result.stdout[-4000:] if result.stdout else "tests completed",
                failed_tests=[],
                duration_sec=0.0,
                stderr=result.stderr[-4000:],
            )

    def _run_eval(self) -> EvalResult:
        result = self.runner.run(["bash", "scripts/run_eval.sh"])
        try:
            payload = self.store.read_tmp_json("eval_result.json")
            return EvalResult(**payload)
        except Exception:
            if result.returncode != 0:
                return EvalResult(
                    score=0.0,
                    tests_pass=False,
                    constraints_ok=False,
                    latency_ms=None,
                    latency_delta_pct=None,
                    regressions=["eval execution failed"],
                    notes=[result.stderr[-4000:]],
                )
            raise

    def _accept(self, *, iteration: int) -> None:
        result = self.runner.run(
            ["bash", "scripts/accept_change.sh", f"accepted iteration {iteration}"]
        )
        if result.returncode != 0:
            raise RuntimeError(f"accept_change failed: {result.stderr}")

    def _reject_and_rollback(self) -> None:
        result = self.runner.run(["bash", "scripts/rollback_change.sh"])
        if result.returncode != 0:
            raise RuntimeError(f"rollback failed: {result.stderr}")

    def write_final_report(self) -> None:
        self.reporting_service.write_final_report()

    def _now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
12. main.py 최종판 생성 예시

파일: orchestrator/main.py

from __future__ import annotations

from pathlib import Path

from orchestrator.baseline_service import BaselineService
from orchestrator.change_guard import ChangeGuardService
from orchestrator.codex_adapter import CodexAdapter
from orchestrator.command_runner import CommandRunner
from orchestrator.config import load_config
from orchestrator.critic_service import CriticService
from orchestrator.decision_engine import DecisionEngine
from orchestrator.file_store import FileStore
from orchestrator.iteration_service import IterationService
from orchestrator.memory_service import MemoryService
from orchestrator.planner_service import PlannerService
from orchestrator.reporting import ReportingService


def main() -> int:
    root = Path.cwd()
    config = load_config()

    store = FileStore(root)
    runner = CommandRunner(root)

    planner_service = PlannerService(store=store)
    critic_service = CriticService()
    baseline_service = BaselineService(store=store)
    reporting_service = ReportingService(store=store)
    memory_service = MemoryService(store=store)
    change_guard_service = ChangeGuardService(root=root)
    decision_engine = DecisionEngine()
    codex_adapter = CodexAdapter(root=root, runner=runner)

    service = IterationService(
        root=root,
        config=config,
        store=store,
        runner=runner,
        planner_service=planner_service,
        critic_service=critic_service,
        baseline_service=baseline_service,
        reporting_service=reporting_service,
        memory_service=memory_service,
        change_guard_service=change_guard_service,
        decision_engine=decision_engine,
        codex_adapter=codex_adapter,
    )

    baseline = baseline_service.load()
    no_improvement_streak = 0

    for iteration in range(1, config.max_iterations + 1):
        result = service.run(iteration=iteration, baseline=baseline)

        print(
            f"[iteration={iteration}] "
            f"decision={result.decision} "
            f"code={result.decision_code} "
            f"score_before={result.score_before} "
            f"score_after={result.score_after}"
        )

        if result.new_baseline > baseline:
            no_improvement_streak = 0
        else:
            no_improvement_streak += 1

        baseline = result.new_baseline

        if baseline_service.target_reached(
            baseline=baseline,
            target_score=config.target_score,
        ):
            print(f"[orchestrator] target score reached: {baseline}")
            break

        if result.decision == "hold" and config.stop_on_hold:
            print("[orchestrator] stopping because decision=hold")
            break

        if no_improvement_streak >= config.max_no_improvement_streak:
            print("[orchestrator] stopping due to no-improvement streak")
            break

    service.write_final_report()
    print("[orchestrator] final report written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
13. 서비스 간 의존 관계 요약

최종적으로 서비스 간 관계는 아래처럼 보면 된다.

IterationService가 직접 의존
PlannerService
CriticService
BaselineService
ReportingService
MemoryService
ChangeGuardService
DecisionEngine
CodexAdapter
FileStore
CommandRunner
PlannerService가 직접 의존
FileStore
ReportingService가 직접 의존
FileStore
MemoryService가 직접 의존
FileStore
BaselineService가 직접 의존
FileStore
CodexAdapter가 직접 의존
CommandRunner
FileStore(optional)

즉 FileStore와 CommandRunner는
여러 서비스가 공유하는 핵심 인프라 계층이다.

14. 최종 상태에서 IterationService가 얇아졌는지 확인

좋은 신호는 아래다.

얇아진 IterationService의 특징
복잡한 parsing이 없다
markdown formatting 로직이 거의 없다
memory 렌더링 로직이 없다
diff 검사 로직이 없다
baseline 정책이 없다
그냥 순서대로 서비스 호출하고 결과를 연결한다

이 상태가 되어야
나중에 기능 추가가 쉬워진다.

15. 이 구조의 장점
15.1 테스트 용이성

서비스별 단위 테스트가 가능하다.

15.2 정책 교체 용이성

예:

PlannerService를 LLM 기반으로 교체
CriticService를 하이브리드로 교체
BaselineService에 history 저장 추가
MemoryService에 더 강한 압축 정책 추가
15.3 IterationService 읽기 쉬움

흐름이 한눈에 보인다.

15.4 이후 Multi-Agent 구조로 확장 가능

지금은 단일 에이전트 기반 구조지만,
나중에 각 서비스 일부를 역할별 agent로 확장하기 쉬워진다.

16. 남은 핵심 과제

이제 구조는 꽤 정리됐다.
다음으로 남은 건 주로 아래다.

CodexAdapter 실제 CLI 환경 대응
PlannerService 고도화
CriticService 고도화
Baseline history 추가
단위 테스트 작성
실제 템플릿 프로젝트 파일 패키징

즉 이제부터는 “설계 구조”보다
실행 품질과 구현 완성도의 영역으로 넘어간다.

17. 추천 다음 단계

이 문서 다음으로 가장 자연스러운 단계는 아래 둘 중 하나다.

방향 A: 코드 완성도 강화
각 서비스 단위 테스트 문서
pytest 테스트 초안
mock 기반 테스트 전략
failure case 테스트
방향 B: 실행 패키지화
실제 폴더 구조 전체 코드 템플릿 묶음
bootstrap script
example project
설치/실행 가이드

실전적으로는 보통
B → A 순서도 좋다.

즉 먼저 템플릿을 돌려보고,
그 다음 테스트를 정교화하는 방식이다.

18. 핵심 요약

이번 문서의 핵심은 아래다.

PlannerService 는 hypothesis 선택과 계획 생성을 담당한다
CriticService 는 결과를 비판적으로 검토한다
BaselineService 는 공식 성능 기준점을 관리한다
이 세 서비스를 분리하면 IterationService 는 진짜 orchestration만 남는다
최종 구조는 실전적인 서비스 경계가 거의 완성된 형태다
이제부터는 구조 논의보다 실제 템플릿 코드/테스트/부트스트랩 품질을 높이는 단계다

즉 현재 구조는 아래처럼 정리된다.

IterationService
= 흐름 제어만 담당

세부 책임
- PlannerService
- CriticService
- BaselineService
- ReportingService
- MemoryService
- ChangeGuardService
- DecisionEngine
- CodexAdapter
로 분산

이 상태까지 오면
단순 문서 설계를 넘어
실제로 유지보수 가능한 아키텍처의 형태가 거의 갖춰진다.
