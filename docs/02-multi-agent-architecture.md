# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 완전 실전형 멀티 에이전트 구조 설계서
# 버전: v1.0
# 목적: "탐색 + 구현 + 평가 + 반복 개선"을 하나의 실행 가능한 시스템으로 묶는 아키텍처

---

## 0. 문서 목적

이 문서는 다음 4가지를 하나의 실전형 구조로 통합하기 위한 설계서다.

1. **Karpathy 스타일**
   - 열린 탐색
   - 가설 생성
   - 연구적 시도
   - "무엇을 시도해야 하는가?"를 확장하는 역할

2. **autoresearch 스타일**
   - 반복 개선
   - 작은 변경
   - 고정 평가
   - 롤백 / 유지 판단
   - "무엇이 실제로 좋아졌는가?"를 측정하는 역할

3. **Codex CLI**
   - 실제 코드/문서/설정 수정
   - 테스트 실행
   - 로컬 프로젝트 작업
   - "실행 주체" 역할

4. **MCP**
   - 외부 도구 연결 계층
   - 파일시스템 / git / 브라우저 / DB / 로그 / API / 배포 환경 연결
   - "손발" 역할

이 문서의 핵심 목표는:

> 단순히 "여러 AI를 붙였다" 수준이 아니라,
> 실제 프로젝트에 넣어도 동작 가능한 멀티 에이전트 운영 구조를 정의하는 것

이다.

---

## 1. 핵심 철학

이 시스템은 "모델 학습" 시스템이 아니다.

즉:
- 파라미터 업데이트 없음
- 파인튜닝 없음
- RLHF 없음

대신 다음을 반복적으로 개선한다.

- 코드
- 프롬프트
- 설정값
- 검색 전략
- 테스트 대응 방식
- 작업 전략 문서
- 실험 기록

즉 본질은:

> **모델이 진화하는 것이 아니라, 프로젝트 상태와 전략이 진화한다**

이다.

---

## 2. 왜 Karpathy 스타일과 autoresearch를 같이 써야 하는가

둘은 비슷해 보이지만 실제 역할이 다르다.

### 2.1 Karpathy 스타일이 하는 일
Karpathy 스타일은 보통 다음 성격을 가진다.

- 더 넓게 탐색
- 새로운 가설 만들기
- 기존 접근이 틀렸을 가능성을 열어둠
- 단순 튜닝이 아니라 방향 전환을 시도
- "지금 평가 기준 밖에서 더 나은 방법이 있지 않나?"를 고민

즉:

> **탐색형 사고 엔진**

이다.

### 2.2 autoresearch 스타일이 하는 일
autoresearch는 다음 역할에 가깝다.

- 현재 목표가 이미 있다
- 고정된 평가 기준이 있다
- 한 번에 작은 변경만 한다
- 실제 점수 개선이 있는지 측정한다
- 나빠지면 롤백한다

즉:

> **최적화형 실험 엔진**

이다.

### 2.3 둘을 결합하면
탐색만 하면:
- 아이디어는 많지만 수렴이 어렵다

최적화만 하면:
- 로컬 최적점에 갇힌다
- 방향 전환이 약하다

둘을 결합하면:
- 새로운 방향을 탐색하고
- 실제로 점수로 검증하며
- 살아남는 것만 축적하게 된다

즉 최종 구조는:

```text
탐색(Explorer)
    ↓
가설(Hypothesis)
    ↓
구현(Implementer)
    ↓
평가(Evaluator)
    ↓
유지/롤백(Controller)
    ↓
기록(Memory/Results)
    ↓
다음 탐색
3. 시스템의 최상위 목표

이 시스템의 실전 목표는 다음과 같다.

3.1 가능한 목표 예시
검색 relevance 개선
RAG 응답 품질 향상
테스트 통과율 상승
latency 악화 없이 품질 향상
prompt quality 향상
UI consistency 개선
bug reproduction 및 수정 자동화
문서 정확도/완성도 개선
3.2 적합하지 않은 목표
감성 브랜딩
측정 불가능한 "멋짐"
사람 취향에만 의존하는 작업
평가가 숫자로 떨어지지 않는 작업
3.3 시스템 적합 조건

다음이 만족되어야 한다.

자동 실행 가능
자동 평가 가능
결과를 수치/등급으로 저장 가능
실패 시 롤백 가능
작업 단위를 나눌 수 있음
4. 전체 아키텍처 개요

전체 구조는 아래와 같다.

[User / Product Goal]
        ↓
[Controller Agent]
        ├── [Explorer Agent]        : 방향 탐색, 가설 생성
        ├── [Planner Agent]         : 실험 계획, 작업 분해
        ├── [Implementer Agent]     : 실제 코드/문서/설정 변경
        ├── [Evaluator Agent]       : frozen eval, 테스트, 품질 점수
        ├── [Critic Agent]          : 실패 원인 분석, 반례 제시
        └── [Archivist Agent]       : 결과 기록, memory 정리
                ↓
         [Codex CLI Runtime]
                ↓
              [MCP]
   ├── filesystem
   ├── shell/test runner
   ├── git
   ├── browser
   ├── database
   ├── logs
   ├── API client
   └── deployment checker
                ↓
         [Project Workspace]
5. 에이전트별 역할 정의
5.1 Controller Agent
역할

전체 루프를 통제하는 상위 오케스트레이터다.

책임
목표 읽기
현재 baseline 읽기
어떤 가설을 먼저 실행할지 결정
iteration 예산 관리
승인/거절 판단
점수 개선 여부에 따라 유지/롤백
에이전트들 간 충돌 해결
종료 조건 판단
입력
PRODUCT_GOAL.md
TASK.md
RESULTS.tsv
MEMORY.md
latest eval summary
출력
iteration directive
선택된 hypothesis
accept/reject decision
다음 루프 지시
금지
직접 큰 코드 수정
frozen eval 수정
자신의 판단을 증거 없이 강행
5.2 Explorer Agent
역할

Karpathy 스타일의 탐색형 에이전트다.

책임
새로운 접근법 제안
기존 방식의 한계 지적
가설 후보 생성
비주류 접근 발굴
"지금 측정하는 방식이 놓치고 있는 것이 무엇인지" 탐색
예시 출력
BM25 weight 변경 가설
query rewrite 추가 가설
reranker feature 추가 가설
retrieval 전처리 normalization 가설
evaluator blind spot 분석
특징
실험 자체는 하지 않음
넓게 제안하되, 실제 적용 전 Planner/Controller 검토 필요
금지
구현 세부 diff 직접 작성 강요
검증되지 않은 대규모 rewrite 강행
5.3 Planner Agent
역할

탐색 결과를 실제 실험 가능한 단위로 잘게 나눈다.

책임
hypothesis를 작업 단위로 분해
한 iteration 당 변경 범위를 제한
test plan 작성
success/failure 조건 정의
위험도 표시
dependency 확인
출력 예시
Iteration 12:
change scope: query normalization only
expected effect: recall 소폭 상승
risks: false positive 증가
test plan:
unit tests
frozen eval
latency budget check
금지
측정 불가능한 작업 제안
한 iteration에 너무 많은 변경 묶기
5.4 Implementer Agent
역할

실제 수정 담당이다.

책임
Codex CLI를 사용해 코드 수정
문서 수정
설정 변경
로컬 테스트 실행
작은 단위 diff 생성
원칙
한 번에 하나의 핵심 변경
변경 이유를 반드시 기록
eval 전 speculative cleanup 금지
필요 시만 MCP 호출
출력
patch summary
changed files
local test result
implementation note
금지
frozen eval 수정
fixture 수정
대규모 무단 리팩터링
근거 없는 광범위 rename
5.5 Evaluator Agent
역할

결과를 판정하는 심판이다.

책임
frozen eval 실행
일반 테스트 실행
latency / memory budget 점검
score 계산
baseline 대비 개선 여부 판단용 데이터 제공
절대 원칙
평가 기준은 고정
평가기는 수정 금지
측정 공정성 유지
출력 예시
score: 0.781 → 0.803
tests: pass
latency delta: +2.1%
regression: none
decision input: acceptable
금지
수정 방향 제안이 주 역할이 되면 안 됨
평가 기준을 iteration에 따라 바꾸면 안 됨
5.6 Critic Agent
역할

반례/실패 분석 담당이다.

책임
왜 좋아진 것처럼 보이는지 의심
overfitting 가능성 점검
false positive 증가 여부 추적
테스트 구멍 찾기
잘못된 성공 판정 방지
예시 질문
이 개선이 특정 fixture에만 먹힌 것 아닌가?
score는 올랐지만 운영 비용이 늘어난 것 아닌가?
일반화 성능이 오히려 악화된 것 아닌가?
hidden regression 가능성은 없는가?
금지
모든 시도를 무조건 반대만 하기
주관적 느낌만으로 반박하기
5.7 Archivist Agent
역할

기록과 메모리를 정리한다.

책임
RESULTS.tsv 갱신
MEMORY.md 요약
accepted/rejected changes 기록
실패 패턴 축적
이후 iteration이 같은 실수를 반복하지 않게 정리
중요성

이 시스템은 장기 파라미터 학습이 없으므로,
파일 기반 기억 체계가 사실상 메모리 역할을 한다.

6. Codex CLI의 위치

Codex CLI는 "하나의 에이전트"가 아니라,
이 설계 안에서는 실제 실행 런타임이다.

즉 각 에이전트가 Codex를 쓰는 방식이 아니라,
현실적으로는 다음 둘 중 하나다.

방식 A. 단일 Codex 세션 + 역할 프롬프트 스위칭
Controller가 각 단계별 프롬프트를 바꿔 같은 Codex 세션을 사용
구현 난이도 낮음
컨텍스트 오염 가능성 있음
방식 B. 역할별 Codex 호출 세션 분리
Explorer용 Codex 호출
Planner용 Codex 호출
Implementer용 Codex 호출
Evaluator/Critic는 shell/MCP 중심
더 안정적이지만 비용/속도 부담 있음
실전 추천

초기 MVP는:

Explorer = 짧은 별도 호출
Planner = 짧은 별도 호출
Implementer = 메인 Codex 세션
Evaluator = shell + eval script
Critic = 별도 짧은 검증 호출
Archivist = 스크립트 + 요약 호출

이 구성이 좋다.

7. MCP의 위치

MCP는 에이전트가 아니다.
MCP는 도구 연결 계층이다.

7.1 필수 MCP
filesystem
shell/test runner
git
7.2 추천 MCP
browser
logs
database
7.3 선택 MCP
deployment checker
API client
screenshot / DOM inspector
7.4 원칙

에이전트 수보다 MCP 수가 많아질수록 복잡성이 급증한다.
처음부터 모든 도구를 연결하지 말고,
실제 목표 달성에 필요한 최소 도구만 연결해야 한다.

8. 디렉토리 구조

실전형 권장 구조는 아래와 같다.

project/
├─ src/
├─ tests/
├─ eval/
│  ├─ frozen_eval.py
│  ├─ fixtures.json
│  ├─ rubric.md
│  └─ baseline.json
├─ agent/
│  ├─ PRODUCT_GOAL.md
│  ├─ TASK.md
│  ├─ RULES.md
│  ├─ MEMORY.md
│  ├─ HYPOTHESES.md
│  ├─ PLAN.md
│  ├─ ITERATION_STATE.json
│  └─ RESULTS.tsv
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
│  ├─ accept_change.sh
│  ├─ rollback_change.sh
│  ├─ update_memory.py
│  └─ summarize_results.py
├─ mcp/
│  ├─ servers.json
│  └─ tool-policies.md
├─ reports/
│  ├─ iteration/
│  └─ final/
└─ README.md
9. 핵심 파일 설명
9.1 PRODUCT_GOAL.md

프로젝트 최상위 목적

예:

검색 relevance 향상
precision/recall tradeoff 제어
latency budget 5% 이내 유지
9.2 TASK.md

현재 사이클에서 해결할 구체적 문제

예:

query normalization으로 recall 개선 시도
9.3 RULES.md

에이전트 공통 운영 규칙

예:

frozen eval 수정 금지
fixture 수정 금지
한 iteration당 하나의 핵심 변경
score 악화 시 롤백
대규모 구조 변경은 Controller 승인 필요
9.4 MEMORY.md

최근 실험 히스토리 요약

9.5 HYPOTHESES.md

Explorer가 낸 후보들 목록

9.6 PLAN.md

Planner가 만든 실행 계획

9.7 RESULTS.tsv

모든 iteration 기록

예:

iteration	status	score_before	score_after	tests_pass	change_summary
1	accepted	0.701	0.724	true	add query normalization
2	rejected	0.724	0.715	true	aggressive synonym expansion
3	accepted	0.724	0.741	true	tune ranking feature weights
10. 멀티 에이전트 실행 루프

아래가 전체 반복 루프다.

1. Controller가 현재 목표/상태 확인
2. Explorer가 새 가설 후보 제안
3. Planner가 이번 iteration용 단일 실험 선택
4. Implementer가 Codex CLI로 작은 수정 적용
5. Evaluator가 테스트 + frozen eval 실행
6. Critic이 결과가 진짜 개선인지 검증
7. Controller가 accept/reject 결정
8. Archivist가 기록 및 memory 갱신
9. 다음 iteration 진행

이걸 좀 더 엄밀하게 쓰면:

Initialize baseline
While budget remains:
    Controller reads goal, rules, memory
    Explorer proposes hypotheses
    Planner selects one small testable change
    Implementer applies patch via Codex CLI
    Evaluator runs tests and frozen eval
    Critic checks for fake wins / regressions
    Controller accepts or rejects
    Archivist logs results and updates memory
End
Generate final report
11. iteration 단위 설계 원칙
11.1 한 번에 하나의 핵심 변경

좋은 예:

query normalization 추가
stopword rule 수정
reranking weight 조정

나쁜 예:

normalization + tokenizer + reranker + cache rewrite 동시 변경
11.2 변경은 작고 검증 가능해야 함
diff가 작아야 원인 추적 가능
실패 시 롤백이 쉬워야 함
11.3 실패도 자산

실패 기록은 반드시 남겨야 한다.

왜냐하면:

실패 패턴 누적이 없으면 같은 실수를 반복한다
실제로 "무엇이 안 되는가"가 전략 품질을 결정한다
12. 평가 체계
12.1 평가 종류
unit/integration tests
frozen eval score
latency/memory/resource check
optional manual review queue
12.2 frozen eval의 역할

frozen eval은 이 시스템의 "심판"이다.

원칙:

절대 수정 금지
iteration마다 동일 입력 사용
scoring logic 고정
비교 가능해야 함
12.3 평가 실패 시
코드가 좋아 보여도 reject 가능
테스트 통과 못 하면 reject
resource budget 초과 시 reject
hidden regression이 의심되면 hold/review
13. 롤백 전략

이 시스템에서 롤백은 선택이 아니라 필수다.

13.1 롤백 조건
score 악화
tests fail
latency budget 초과
Critic이 심각한 regression 제시
Planner 범위를 넘는 변경 발생
13.2 롤백 방식
git reset / restore
patch discard
state snapshot 복원
13.3 중요성

롤백이 없는 autoresearch는 금방 망가진다.
좋은 구조는 "실패를 싸게 만드는 구조"다.

14. 메모리 구조

모델이 장기 학습을 하지 않기 때문에,
파일 기반 메모리가 중요하다.

14.1 MEMORY.md에 들어갈 것
최근 accepted changes
최근 rejected changes
반복 실수
주의할 tradeoff
현재 유망 hypothesis
14.2 요약 원칙

장황한 로그를 그대로 두면 다음 루프 품질이 떨어진다.
따라서 Archivist가 아래처럼 정리해야 한다.

예:

normalization 계열은 recall 개선 효과 있음
synonym expansion은 false positive 위험 큼
reranker weight 조정은 precision 개선 여지 있음
latency budget은 현재 여유 2.3% 남음
15. 실제 운영 모드
15.1 Research Mode

목적:

방향 탐색
hypothesis pool 확장

특징:

Explorer 비중 큼
평가보다 가설 확장이 우선
15.2 Optimization Mode

목적:

score를 실제로 올리기

특징:

Planner/Implementer/Evaluator 비중 큼
작은 실험 반복
15.3 Hardening Mode

목적:

개선을 운영 안정성까지 검증

특징:

Critic/Evaluator 강화
regression 방지
resource budget 엄격 적용

실전에서는 대체로:

Research → Optimization → Hardening

순으로 운용한다.

16. 운영 예시: 검색 품질 개선 프로젝트
목표

전자상거래 검색 relevance 향상

baseline
score: 0.712
latency: 112ms
iteration 흐름 예시
Iteration 1
Explorer:
query normalization이 recall에 도움될 수 있음
Planner:
lowercase + punctuation normalize만 적용
Implementer:
parser 전처리 함수 수정
Evaluator:
score: 0.726
latency: 113ms
Critic:
큰 regression 없음
Controller:
accept
Archivist:
accepted 기록
Iteration 2
Explorer:
synonym expansion 제안
Planner:
상위 빈도 synonym만 제한 적용
Implementer:
synonym map 추가
Evaluator:
score: 0.719
Critic:
false positive 증가
Controller:
reject
Archivist:
"공격적 synonym 확장은 위험" 기록
Iteration 3
Explorer:
reranker feature weight 조정 제안
Planner:
title boost만 미세 조정
Implementer:
ranking weight 수정
Evaluator:
score: 0.738
Critic:
latency 영향 미미
Controller:
accept

이렇게 누적한다.

17. 프롬프트 구조 예시
17.1 Controller Prompt

역할:

iteration 통제
accept/reject
다음 행동 결정

핵심 지시:

goal, rules, memory, latest eval를 읽고 판단
한 번에 하나의 실험만 승인
증거 기반으로 accept/reject
score improvement 없는 변경은 거절 우선
17.2 Explorer Prompt

역할:

가설 생성

핵심 지시:

기존 accepted/rejected history를 읽고
새로운 유망 가설 3~5개 제안
각 가설의 기대 효과, 위험, 검증 방법 설명
17.3 Planner Prompt

역할:

실행 단위 설계

핵심 지시:

가장 유망한 가설 하나를 선택
한 iteration에 맞는 작은 변경으로 분해
성공/실패 조건 명시
필요한 테스트와 rollback 조건 정의
17.4 Implementer Prompt

역할:

실제 수정

핵심 지시:

frozen eval, fixtures 수정 금지
계획된 범위만 수정
변경 후 테스트 실행
변경 내용과 이유 요약
17.5 Critic Prompt

역할:

반례/오판 방지

핵심 지시:

score 상승이 진짜인지 의심
regression 가능성 찾기
overfitting 위험 검토
acceptance에 필요한 반대 관점 제시
17.6 Archivist Prompt

역할:

기록 정리

핵심 지시:

accepted/rejected 결과를 짧고 유용하게 요약
다음 iteration에서 중요한 주의사항만 남기기
불필요한 장문 제거
18. 상태 머신 관점

이 시스템은 사실상 상태 머신이다.

IDLE
  ↓
READ_STATE
  ↓
EXPLORE
  ↓
PLAN
  ↓
IMPLEMENT
  ↓
EVALUATE
  ↓
CRITIQUE
  ↓
DECIDE
  ├── ACCEPT → ARCHIVE → NEXT_ITERATION
  └── REJECT → ROLLBACK → ARCHIVE → NEXT_ITERATION
  ↓
FINALIZE

이렇게 명시해야 운영 중 꼬이지 않는다.

19. 종료 조건
19.1 정상 종료
목표 score 도달
iteration 예산 소진
최근 N회 개선 없음
Controller가 diminishing returns 판단
19.2 비정상 종료
eval system failure
environment corruption
repeated unexplained regression
project constraints 위반
19.3 종료 시 출력
final score
accepted changes 목록
rejected hypothesis 목록
remaining open questions
next recommended direction
20. 실전 구현 단계별 추천
1단계: 단일 에이전트 MVP
Controller/Planner/Implementer를 사실상 하나로 운용
Evaluator는 script
Archivist는 간단 요약
2단계: Critic 분리
가짜 개선 방지 강화
3단계: Explorer 분리
Karpathy 스타일 탐색성 추가
4단계: 완전 멀티 에이전트
역할별 호출 분리
로그/메모리 정교화

가장 중요한 건:

처음부터 풀 멀티 에이전트로 가지 말고, 반드시 단계적으로 키워야 한다.

21. 가장 자주 망하는 원인
21.1 frozen eval을 건드림

즉시 신뢰 붕괴

21.2 iteration 범위가 너무 큼

원인 추적 불가

21.3 기록이 없음

동일 실패 반복

21.4 Explorer가 너무 강함

탐색은 많지만 수렴 안 됨

21.5 Critic이 너무 강함

모든 시도가 reject됨

21.6 Controller가 약함

각 agent 결과를 그냥 나열만 하고 결정을 못 내림

21.7 MCP 남용

도구가 많아질수록 혼란 증가

22. 실전 권장 밸런스

초기 권장 비중은 아래와 같다.

Controller: 강함
Planner: 강함
Implementer: 강함
Evaluator: 매우 강함
Critic: 중간
Explorer: 약~중간
Archivist: 중간

이유:

실전에서는 "탐색"보다 "안전한 개선 루프"가 먼저다.
23. 한 줄 핵심 정의

이 구조를 한 줄로 정의하면:

Explorer가 가설을 넓히고, Planner가 잘게 쪼개고, Implementer가 Codex CLI로 바꾸고, Evaluator가 고정 기준으로 재고, Critic이 가짜 개선을 막고, Controller가 유지/롤백을 결정하며, Archivist가 기억을 남기는 멀티 에이전트 반복 개선 시스템

이다.

24. 최종 결론

이 구조는 단순한 "AI 여러 개 붙이기"가 아니다.

진짜 핵심은 아래 네 가지다.

탐색과 최적화를 분리한다
평가를 고정한다
작은 실험만 반복한다
기억을 파일로 축적한다

즉:

Karpathy 스타일은 "가능성 탐색"
autoresearch는 "반복 최적화"
Codex CLI는 "실행"
MCP는 "도구 연결"

을 맡는다.

실전에서 살아남는 구조는
화려한 멀티 에이전트가 아니라,

강한 평가 + 작은 변경 + 명확한 롤백 + 좋은 기록

을 가진 구조다.

25. 다음 문서로 바로 이어져야 할 것

이 설계 다음 단계로 바로 필요한 문서는 아래다.

PRD
TRD
폴더별 실제 파일 초안
prompts/controller.md ~ archivist.md
run_loop.sh / run_iteration.sh
MCP server config
RESULTS.tsv 포맷
frozen_eval.py 예제

가장 실전적인 다음 단계는
이 설계를 기반으로 바로 실행 가능한 형태로 만드는 것이다.

다음
