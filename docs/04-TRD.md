# TRD
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 실전형 반복개선 에이전트 시스템 기술 요구사항 문서
# 버전: v1.0

---

## 1. 문서 목적

이 문서는 PRD에서 정의한 반복개선 에이전트 시스템을 실제 구현 가능한 수준으로 기술적으로 구체화한다.

핵심 목표는 다음과 같다.

- Codex CLI를 실행 엔진으로 사용
- MCP를 외부 도구 연결 레이어로 사용
- frozen eval 기반 반복 개선 루프 구현
- 역할 기반 단일/멀티 에이전트 구조 지원
- 기록, 롤백, 평가, 메모리 누적을 기술적으로 일관되게 설계

이 문서는 "아이디어 설명"이 아니라,
실제로 개발 가능한 구성 요소, 상태 전이, 파일 구조, 실행 흐름, 인터페이스를 정의하는 문서다.

---

## 2. 시스템 개요

본 시스템은 크게 6개 계층으로 구성된다.

1. Goal / Config Layer
2. Agent Orchestration Layer
3. Execution Layer (Codex CLI Runtime)
4. Tool Layer (MCP)
5. Evaluation Layer
6. State / Memory / Reporting Layer

전체 구조는 다음과 같다.

```text
[Goal / Rules / Memory Files]
            ↓
[Controller / Explorer / Planner / Implementer / Critic / Archivist]
            ↓
[Codex CLI Runtime]
            ↓
[MCP Tools]
  ├─ filesystem
  ├─ shell
  ├─ git
  ├─ browser
  ├─ logs
  ├─ db
  └─ api
            ↓
[Workspace / Code / Docs / Config]
            ↓
[Tests + Frozen Eval + Constraints Check]
            ↓
[Decision + Rollback + Log Update]
3. 기술 설계 원칙
3.1 single source of truth

각 상태는 가능하면 하나의 파일 또는 하나의 구조에 의해 대표되어야 한다.

예:

현재 목표: agent/TASK.md
운영 규칙: agent/RULES.md
장기 기억: agent/MEMORY.md
실험 기록: agent/RESULTS.tsv
실험 상태: agent/ITERATION_STATE.json
3.2 append-first logging

기록은 기본적으로 append 방식으로 저장한다.
실험 이력은 덮어쓰기보다 축적이 우선이다.

3.3 immutable evaluation

평가기(eval/frozen_eval.py)와 고정 입력(eval/fixtures.json)은 iteration 중 수정하면 안 된다.

3.4 small-step mutation

하나의 iteration은 하나의 핵심 변경만 허용한다.

3.5 rollback by default

수용되기 전까지 모든 변경은 임시 상태로 간주한다.
테스트/평가 실패 시 즉시 롤백 가능해야 한다.

3.6 file-based memory

모델 자체는 장기 기억을 가지지 않으므로,
파일이 메모리 역할을 수행해야 한다.

4. 런타임 모드

시스템은 크게 3개 모드로 동작할 수 있다.

4.1 Single-Agent Mode

하나의 Codex 세션이 다음 역할을 순차적으로 수행한다.

탐색
계획
구현
자기 검토
기록 요약

장점:

간단함
디버깅 쉬움
초기 MVP 적합

단점:

역할 혼선 가능
탐색/비판이 약해질 수 있음
4.2 Split-Role Mode

역할별로 프롬프트를 달리한 Codex 호출을 분리한다.

예:

Explorer 호출
Planner 호출
Implementer 호출
Critic 호출

장점:

역할 명확
판단 분리
가짜 개선 방지 강화

단점:

호출 수 증가
컨텍스트 전달 관리 필요
4.3 Multi-Agent Orchestration Mode

오케스트레이터가 역할별 실행을 별도 프로세스/세션으로 관리한다.

장점:

역할 확장 가능
병렬 탐색 가능
고급 운영 가능

단점:

구현 난이도 높음
상태 충돌 가능
초기에 과하다

실전 권장 순서는 아래와 같다.

Single-Agent Mode
    → Split-Role Mode
    → Multi-Agent Orchestration Mode
5. 디렉토리 구조

권장 디렉토리는 아래와 같다.

project/
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
│  ├─ run_eval.sh
│  ├─ run_tests.sh
│  ├─ accept_change.sh
│  ├─ rollback_change.sh
│  ├─ update_memory.py
│  ├─ log_result.py
│  └─ make_final_report.py
├─ mcp/
│  ├─ servers.json
│  ├─ tool-policies.md
│  └─ capabilities.json
├─ reports/
│  ├─ iteration/
│  └─ final/
└─ tmp/
6. 핵심 파일 정의
6.1 agent/PRODUCT_GOAL.md

역할:

시스템 최상위 목표 정의

필수 항목:

목표 설명
성공 지표
제약사항
금지사항
우선순위

예:

# Product Goal
검색 relevance를 baseline 0.72에서 0.80 이상으로 개선한다.

# Constraints
- latency 증가는 5% 이내
- public API 변경 금지
- frozen eval 수정 금지

# Priority
1. relevance
2. regression 방지
3. latency
6.2 agent/TASK.md

역할:

현재 iteration 또는 현재 cycle의 구체 작업 정의

필수 항목:

현재 집중 문제
적용 범위
이번 cycle의 성공 기준
범위 제외 항목
6.3 agent/RULES.md

역할:

시스템 운영 규칙

권장 항목:

frozen eval 수정 금지
fixtures 수정 금지
one-change-per-iteration
대규모 refactor 금지
테스트 실패 시 reject
score 미개선 시 reject
기록 누락 금지
6.4 agent/MEMORY.md

역할:

누적 요약 기억

구성:

최근 성공 패턴
최근 실패 패턴
위험 tradeoff
반복 금지 실수
현재 유망 방향

형식 예:

## Accepted Patterns
- query normalization은 recall 개선 경향
- title weight 조정은 precision 개선 가능성 높음

## Rejected Patterns
- aggressive synonym expansion은 false positive 위험 높음

## Constraints Reminder
- latency 예산 2.4% 여유
6.5 agent/HYPOTHESES.md

역할:

탐색 결과 목록 관리

권장 구조:

hypothesis id
설명
기대 효과
위험
우선순위
상태

예:

- H-001: query normalization 강화
  - expected: recall 상승
  - risk: precision 하락
  - priority: high
  - status: selected
6.6 agent/PLAN.md

역할:

Planner가 만든 실행 계획

권장 항목:

selected hypothesis
변경 범위
예상 효과
위험
테스트 계획
rollback 조건
6.7 agent/ITERATION_STATE.json

역할:

현재 상태머신 위치 및 iteration 메타 정보 저장

예시:

{
  "iteration": 12,
  "mode": "split-role",
  "phase": "implement",
  "selected_hypothesis": "H-004",
  "baseline_score": 0.741,
  "candidate_score": null,
  "tests_pass": null,
  "decision": null,
  "last_updated": "2026-03-25T10:15:00Z"
}
6.8 agent/RESULTS.tsv

역할:

모든 실험 결과 누적 로그

헤더 예:

iteration	hypothesis_id	status	score_before	score_after	score_delta	tests_pass	constraints_ok	change_summary	rollback_reason

행 예:

12	H-004	accepted	0.741	0.756	0.015	true	true	add query normalization layer	
13	H-007	rejected	0.756	0.748	-0.008	true	true	expand synonym map aggressively	score regressed
6.9 agent/DECISIONS.md

역할:

Controller 판단 요약

용도:

왜 accept/reject 됐는지 설명
Critic 이슈 기록
사람이 나중에 검토하기 쉽게 함
7. 평가 계층 설계
7.1 frozen eval 구성

필수 파일:

eval/frozen_eval.py
eval/fixtures.json
eval/rubric.md
eval/baseline.json
7.2 역할
frozen_eval.py
고정된 입력에 대해 결과를 측정
점수 반환
비교 가능성 유지
fixtures.json
테스트 입력 세트
정답 / 기대 기준
절대 수정 금지
rubric.md
점수 산정 기준 설명
왜 이 점수가 좋은지 문서화
baseline.json
현재 승인된 기준 점수
가장 최근 accepted baseline

예시:

{
  "score": 0.741,
  "measured_at": "2026-03-25T09:10:00Z",
  "iteration": 11
}
7.3 평가 출력 포맷

평가 스크립트는 아래 JSON 형태를 출력하는 것을 권장한다.

{
  "score": 0.756,
  "tests_pass": true,
  "constraints_ok": true,
  "latency_ms": 118,
  "latency_delta_pct": 2.1,
  "regressions": [],
  "notes": [
    "precision improved on category queries",
    "no visible regression in fixture set"
  ]
}
7.4 accept 조건 예시

최소 accept 조건:

tests_pass == true
constraints_ok == true
score > baseline_score

선택 조건:

critic severe objection 없음
diff size threshold 만족
특정 회귀 카테고리 없음
8. 상태 머신 설계

전체 시스템은 아래 상태를 가진다.

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
8.1 상태 전이
INIT → READ_CONTEXT
READ_CONTEXT → EXPLORE
EXPLORE → PLAN
PLAN → IMPLEMENT
IMPLEMENT → RUN_TESTS
RUN_TESTS → RUN_EVAL
RUN_EVAL → CRITIQUE
CRITIQUE → DECIDE
DECIDE → ACCEPT | REJECT
REJECT → ROLLBACK
ACCEPT → ARCHIVE
ROLLBACK → ARCHIVE
ARCHIVE → EXPLORE | FINALIZE
8.2 상태 전이 조건
READ_CONTEXT → EXPLORE
목표/규칙/기록 파일 로드 성공
PLAN → IMPLEMENT
selected hypothesis 존재
plan validation 통과
IMPLEMENT → RUN_TESTS
candidate patch 생성 완료
RUN_TESTS → RUN_EVAL
테스트 러너 실행 완료
fatal error 없음
RUN_EVAL → CRITIQUE
score 계산 완료
DECIDE → ACCEPT
accept 조건 충족
DECIDE → REJECT
accept 조건 미충족 또는 critic severe warning
9. 에이전트 인터페이스 정의

실전 구현에서는 "에이전트"를 별도 프로세스로 만들 수도 있고,
프롬프트 역할 호출로 만들 수도 있다.
어떤 방식이든 인터페이스는 명확해야 한다.

9.1 Controller Interface

입력:

PRODUCT_GOAL.md
TASK.md
RULES.md
MEMORY.md
latest result
critic summary

출력:

{
  "selected_hypothesis": "H-004",
  "decision": "accept",
  "reason": "score improved without constraint violation",
  "next_action": "archive_and_continue"
}
9.2 Explorer Interface

입력:

PRODUCT_GOAL.md
MEMORY.md
RESULTS.tsv

출력:

{
  "hypotheses": [
    {
      "id": "H-010",
      "title": "normalize punctuation in queries",
      "expected_effect": "improve recall",
      "risk": "minor precision drop",
      "priority": "high"
    }
  ]
}
9.3 Planner Interface

입력:

selected hypothesis
rules
memory
current code context

출력:

{
  "selected_hypothesis": "H-010",
  "change_scope": [
    "src/search/normalize.py"
  ],
  "tests_to_run": [
    "pytest tests/search",
    "python eval/frozen_eval.py"
  ],
  "rollback_conditions": [
    "score regression",
    "tests fail",
    "latency increase > 5%"
  ]
}
9.4 Implementer Interface

입력:

plan
codebase
tool access

출력:

{
  "changed_files": [
    "src/search/normalize.py"
  ],
  "change_summary": "added punctuation normalization before tokenization",
  "local_notes": [
    "kept diff minimal",
    "no api surface change"
  ]
}
9.5 Critic Interface

입력:

eval result
diff summary
memory
hypothesis

출력:

{
  "severity": "medium",
  "objections": [
    "score improvement may be concentrated in punctuation-heavy queries only"
  ],
  "recommendation": "accept_with_monitoring"
}
9.6 Archivist Interface

입력:

final iteration result
decision
change summary
critic summary

출력:

{
  "memory_updates": [
    "punctuation normalization appears beneficial with low risk"
  ],
  "result_row_ready": true
}
10. Codex CLI 실행 구조

Codex CLI는 실제 수정 담당 런타임이다.
TRD 관점에서 중요한 건 "어떻게 호출하고 어떤 컨텍스트를 넣을지"다.

10.1 호출 컨텍스트 최소 구성

Implementer 호출 시 포함할 내용:

current TASK
RULES
selected PLAN
relevant code files
forbidden paths
required commands to run after edit
10.2 forbidden path 정책

다음 경로는 기본적으로 수정 금지:

eval/frozen_eval.py
eval/fixtures.json
eval/baseline.json
agent/RESULTS.tsv (에이전트가 직접 임의 편집 금지, logger가 관리)
agent/DECISIONS.md (Archivist/Controller만 수정)
10.3 변경 단위 제한

초기에는 다음 제한을 두는 것이 좋다.

한 iteration당 최대 파일 수 제한
diff line upper bound
rename / delete는 특별 승인 필요
11. MCP 통합 설계
11.1 MCP 필수 도구
filesystem

역할:

파일 읽기/쓰기
디렉토리 탐색
대상 파일 patch 적용
shell

역할:

테스트 실행
eval 실행
lint/build 실행
git

역할:

diff 조회
상태 확인
commit
rollback
11.2 MCP 권장 도구
browser
UI 테스트
렌더링 확인
페이지 오류 확인
logs
runtime 로그 수집
에러 패턴 확인
db
쿼리 검증
데이터 상태 확인
11.3 MCP 정책 문서 예시

mcp/tool-policies.md

# Tool Policies

## Allowed by default
- filesystem read/write within workspace
- shell test commands
- git status, diff, restore, commit

## Restricted
- destructive shell commands outside workspace
- force push
- production db mutation
- deployment actions

## Requires explicit controller approval
- file deletion
- mass rename
- dependency upgrade
- schema change
12. 스크립트 설계
12.1 scripts/run_loop.sh

역할:

전체 반복 루프 관리

책임:

상태 파일 초기화
iteration 시작
하위 스크립트 호출
종료 조건 확인

의사 흐름:

load baseline
while budget remains:
  run_iteration
  if target reached: finalize
  if stagnation: finalize
done
12.2 scripts/run_iteration.sh

역할:

한 iteration 전체 수행

순서:

context load
hypothesis selection
planning
implementation
tests
eval
critique
decision
accept or rollback
archive
12.3 scripts/run_tests.sh

역할:

테스트 실행
structured result 반환

권장 출력:

{
  "passed": true,
  "summary": "24 passed, 0 failed"
}
12.4 scripts/run_eval.sh

역할:

frozen eval + constraints 실행
structured result 생성
12.5 scripts/accept_change.sh

역할:

baseline 업데이트
git commit
결정 로그 기록
12.6 scripts/rollback_change.sh

역할:

working tree 복구
rollback reason 저장
12.7 scripts/update_memory.py

역할:

accepted/rejected 결과 요약
MEMORY.md 갱신
12.8 scripts/log_result.py

역할:

RESULTS.tsv append
structured → tsv 변환
12.9 scripts/make_final_report.py

역할:

최종 요약 리포트 생성

출력:

best score
accepted changes
rejected changes
recommended next steps
13. 결정 로직 설계

의사코드는 아래와 같다.

if tests_pass is false:
    reject

elif constraints_ok is false:
    reject

elif score <= baseline_score:
    reject

elif critic.severity == "high" and critic recommends reject:
    reject_or_hold

else:
    accept
13.1 hold 상태

초기 MVP에서는 hold를 생략할 수 있다.
확장 시에만 도입 권장:

사람이 검토해야 하는 경우
점수는 올랐지만 회귀 가능성이 큰 경우
14. 메모리 갱신 규칙

메모리는 원본 로그 전체를 복사하지 않고,
"다음 시도 품질을 높이는 요약"만 남겨야 한다.

좋은 메모리 예:

normalization은 recall 개선에 유리
synonym expansion은 precision 저하 가능성 큼
title boost 조정은 낮은 비용으로 효과 있음

나쁜 메모리 예:

장황한 iteration 전체 transcript
불필요한 감상문
재사용 가치 없는 로그
15. 병렬화 전략

초기에는 병렬화보다 일관성이 우선이다.
그래도 확장 가능성을 위해 병렬화 전략을 정의한다.

15.1 병렬 가능한 단계
Explorer의 가설 생성
Critic의 독립 검토
후보 branch별 sandbox evaluation
15.2 병렬 위험
같은 파일 충돌
baseline 기준 혼란
memory 동시 갱신 충돌
15.3 권장 방식

병렬은 "가설 탐색"이나 "candidate branch 비교" 수준으로 제한하고,
최종 accept는 반드시 단일 Controller가 결정한다.

16. 오류 처리 전략
16.1 평가 실패

상황:

eval script crash
malformed output
fixture read fail

대응:

iteration reject
baseline 유지
error log 저장
16.2 테스트 실패

대응:

reject
rollback
실패 요약 기록
16.3 git rollback 실패

대응:

emergency snapshot restore
loop 중단
manual intervention required 표시
16.4 MCP 도구 실패

대응:

해당 tool failure 기록
tool retry budget 적용
핵심 도구 실패 시 iteration 중단
17. 관측성(Observability)

이 시스템은 반복 루프이므로 관측성이 중요하다.

필수 관측 포인트:

iteration 시작/종료 시각
selected hypothesis
changed files
tests result
eval score
accept/reject decision
rollback reason
latency delta
constraint violations

권장 저장 위치:

reports/iteration/
agent/RESULTS.tsv
agent/DECISIONS.md
18. 보안 및 안전
18.1 파일 보호
frozen eval 관련 파일은 write-protect 정책 권장
18.2 명령 실행 제한
shell 명령은 workspace 범위 제한
destructive command denylist 적용 권장
18.3 외부 자원 접근 제한
production credential 미노출
production DB mutation 기본 금지
deployment 권한 분리
19. 성능 고려사항
19.1 iteration 비용 관리

iteration당 다음을 기록하면 좋다.

Codex 호출 횟수
테스트 실행 시간
eval 실행 시간
총 wall clock time
19.2 최적화 포인트
전체 테스트 대신 관련 테스트 우선 실행
eval fixture 수 계층화
quick eval / full eval 이원화 가능
19.3 quick eval / full eval

실전에서는 다음 구조가 유용하다.

quick eval:
iteration마다 빠르게 돌림
full eval:
accept 직전 또는 주기적으로 돌림

단, full eval이 최종 판정 기준이어야 한다.

20. 구현 우선순위
Phase 1
file-based state
run_iteration
tests/eval/rollback
results logging
Phase 2
split-role prompts
critic separation
structured JSON outputs
Phase 3
richer MCP integration
candidate branch comparison
dashboard/report improvements
Phase 4
multi-agent orchestration
parallel exploration
human approval gates
21. 기술적 성공 기준

구현 성공으로 판단하기 위한 최소 기준은 아래와 같다.

baseline 측정이 가능하다
한 iteration이 end-to-end로 돈다
tests/eval 결과를 구조화된 데이터로 읽을 수 있다
score 개선 시 accept 가능하다
점수 악화 시 rollback 가능하다
RESULTS.tsv와 MEMORY.md가 자동 갱신된다
동일 실수를 반복하지 않도록 최근 기록이 반영된다
22. 최종 기술 정의

이 시스템은 기술적으로 다음과 같이 정의된다.

목표/규칙/기억/계획 파일을 기반으로, Codex CLI가 MCP 도구를 사용해 작은 변경을 적용하고, frozen eval과 테스트로 결과를 측정하며, Controller가 유지/롤백을 결정하고, 모든 결과를 파일 기반 상태와 로그로 축적하는 반복개선형 실행 시스템

23. 다음 단계 문서

이 TRD 다음 단계는 바로 구현에 들어갈 수 있도록 아래 순서로 이어지는 것이 가장 좋다.

폴더별 실제 파일 초안
prompts/*.md 초안
run_loop.sh / run_iteration.sh 초안
frozen_eval.py 예제
RESULTS.tsv 샘플
MCP servers.json 예시
최소 동작 서버/스크립트 템플릿
다음 단계 문서 작성 진행
