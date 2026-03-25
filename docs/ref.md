단일 에이전트 기준으로만 현실적으로 짤게.

핵심은 이거다:

Codex CLI 하나를 실행 엔진으로 쓰고, MCP는 도구 연결만 맡기고, autoresearch는 “반복 개선 루프”로만 붙인다.
모델이 학습하는 게 아니라, 파일·프롬프트·코드가 반복적으로 개선되는 구조다.

1. 목표를 다시 정확히 정의

이 구조의 목표는:

사용자 목표 1개를 받는다
Codex CLI가 작업 대상 파일을 수정한다
MCP 도구를 통해 필요한 외부 작업을 수행한다
고정된 eval로 결과를 측정한다
점수가 좋아지면 유지, 아니면 롤백한다
이 과정을 반복한다

즉, 멀티 에이전트가 아니라 그냥:

Single Agent
= 계획 + 수정 + 도구 호출 + 평가 해석 + 반복
2. 이 구조에서 각 요소 역할
Codex CLI

실제 두뇌 + 실행 주체다.

하는 일:

목표 해석
수정안 생성
코드/문서 편집
MCP 호출 결정
eval 결과 해석
다음 시도 결정

즉, 에이전트는 Codex 하나다.

MCP

MCP는 에이전트가 아니다.
그냥 외부 기능 연결 레이어다.

예:

파일 생성
테스트 실행
브라우저 확인
DB 조회
로그 수집
배포 전 체크

즉:

Codex = 판단
MCP = 손발
autoresearch

autoresearch도 에이전트가 아니다.
그냥 반복 개선 운영 방식이다.

예:

한 번에 하나의 변경만 시도
결과를 측정
실패 시 롤백
기록 남김
다시 시도

즉:

autoresearch = 운영 루프
3. 가장 현실적인 단일 에이전트 구조

아래가 실제로 제일 안 헛돌고, 구현 가능한 구조다.

[User Goal]
   ↓
[Controller Script]
   ↓
[Codex CLI]
   ├─ 프로젝트 파일 읽기
   ├─ CLAUDE.md / AGENT.md / TASK.md 읽기
   ├─ 필요 시 MCP Tool 호출
   ├─ 코드 수정
   ├─ 테스트 실행
   └─ 결과 요약 작성
   ↓
[Eval Runner]
   ├─ 고정 테스트
   ├─ 품질 점수 계산
   └─ pass/fail + score 반환
   ↓
[Controller Script]
   ├─ score 비교
   ├─ 개선이면 commit
   └─ 악화면 rollback
   ↓
[다음 반복]

여기서 생각하는 주체는 Codex 하나뿐이다.

4. 왜 이 구조가 현실적이냐

이전 답변들에서 흔히 과장되는 부분이 있었는데, 실제로는 아래처럼 봐야 맞다.

현실적인 점
단일 에이전트가 제일 디버깅 쉽다
실패 원인 추적이 쉽다
prompt drift가 덜하다
상태 관리가 단순하다
eval과 rollback이 명확하다
멀티 에이전트보다 나은 점
역할 충돌이 없다
문맥 전달 비용이 적다
“누가 잘못했는지” 애매하지 않다
토큰/실행량 낭비가 적다

그래서 실전 MVP는 멀티보다 단일 에이전트 + 강한 eval이 훨씬 낫다.

5. 최소 폴더 구조

이 정도면 충분하다.

project/
├─ src/                     # 실제 대상 코드
├─ tests/                   # 일반 테스트
├─ eval/
│  ├─ frozen_eval.py        # 절대 수정 금지 평가기
│  ├─ fixtures.json         # 고정 입력 데이터
│  └─ rubric.md             # 점수 기준 설명
├─ agent/
│  ├─ TASK.md               # 현재 목표
│  ├─ RULES.md              # 수정 규칙
│  ├─ MEMORY.md             # 최근 시도 요약
│  └─ RESULTS.tsv           # 실험 로그
├─ mcp/
│  └─ server-config.json    # MCP 연결 정보
├─ scripts/
│  ├─ run_iteration.sh
│  ├─ evaluate.sh
│  ├─ commit_if_better.sh
│  └─ rollback.sh
└─ README.md
6. 파일별 역할
TASK.md

현재 목표를 적는다.

예:

# Goal
검색 결과 relevance를 개선한다.

# Constraints
- public API 변경 금지
- 응답 시간 10% 이상 악화 금지
- frozen eval 수정 금지
RULES.md

Codex가 지켜야 할 운영 규칙이다.

예:

- 한 iteration당 하나의 핵심 변경만 수행
- eval 실패 시 원인 추정 작성
- frozen eval, fixtures 수정 금지
- 통과 못 하면 자동 롤백
- 변경 내용은 diff 기준으로 200줄 이내 우선
MEMORY.md

장기학습이 없으니까, 파일이 메모리 역할을 한다.

예:

## Recent Attempts
1. BM25 weight 증가 → precision 상승, recall 하락
2. query normalization 추가 → 전체 score 소폭 상승
3. synonym expansion 과도 적용 → false positive 증가
RESULTS.tsv

기록 저장.

예:

iteration	score	pass	change_summary
1	0.71	true	add query normalization
2	0.68	false	expand synonyms aggressively
3	0.74	true	tune ranking weights
7. 실제 반복 루프

이게 핵심이다.

1. 현재 상태 읽기
2. Codex가 다음 수정안 제안/적용
3. 테스트 + frozen eval 실행
4. 점수 비교
5. 좋아졌으면 유지
6. 나빠졌으면 롤백
7. 결과 기록
8. 다음 반복

좀 더 엄밀하게 쓰면:

baseline 측정
for iteration in N:
    Codex가 목표/기록/규칙을 읽음
    작은 수정 1개 수행
    테스트 실행
    frozen eval 실행
    score 비교

    if improved:
        git commit
        MEMORY 업데이트
    else:
        git rollback
        실패 원인 기록
8. 여기서 Codex에게 실제로 시키는 방식

단일 에이전트에서 중요한 건 프롬프트를 거창하게 길게 쓰는 게 아니라, 역할을 좁게 고정하는 거다.

예시:

You are a single autonomous coding agent.

Your job is to improve the target system by small, testable changes.

You must:
- read TASK.md, RULES.md, MEMORY.md
- never modify eval/frozen_eval.py or eval fixtures
- make one focused change per iteration
- run tests and eval after changes
- summarize why the score improved or worsened
- stop speculative large rewrites

Success condition:
- frozen eval score improves over baseline
- tests pass
- constraints remain satisfied

이 정도가 훨씬 낫다.

9. MCP는 어디에 붙이냐

MCP는 꼭 필요한 것만 붙여야 한다.
처음부터 많이 붙이면 단일 에이전트도 흐려진다.

1단계 필수 MCP
filesystem
shell/test runner
git
browser(optional)
2단계 선택 MCP
DB inspector
API client
log reader
screenshot tool

즉 초반 MVP는 거의 이렇게 보면 된다:

Codex CLI
 + filesystem
 + shell
 + git

사실 이것만으로도 대부분의 autoresearch 루프는 돈다.

10. 가장 중요한 안전장치

이 구조가 망가지는 이유는 대부분 같다.

망하는 패턴 1

에이전트가 평가기를 고친다
→ 무효

망하는 패턴 2

한 번에 너무 많이 바꾼다
→ 원인 추적 불가

망하는 패턴 3

실패 기록을 안 남긴다
→ 같은 실수 반복

망하는 패턴 4

목표가 모호하다
→ 점수 최적화가 불가능

그래서 반드시 필요한 게:

frozen eval
one-change-per-iteration
rollback
results log
memory file
11. 이 구조가 적합한 작업

잘 맞는 것:

프롬프트 튜닝
랭킹/검색 품질 개선
테스트 통과율 개선
리팩터링 후 회귀 방지
간단한 성능 최적화

안 맞는 것:

감성적 디자인
제품 방향성 결정
정답 없는 브랜딩
측정 불가능한 품질 작업

즉, 숫자로 평가 가능한 문제에만 붙여야 한다.

12. 진짜 실전 MVP 형태

가장 추천하는 시작점은 이거다.

대상

하나의 로컬 프로젝트

목표

예: 검색 relevance 점수 개선

구성
Codex CLI 1개
MCP 3개(filesystem/shell/git)
frozen eval 1개
iteration controller script 1개
운영 방식
최대 10 iteration
각 iteration 1개 수정
score 좋아질 때만 commit
모든 시도 TSV 기록

이게 진짜 돌아가는 최소 단위다.

13. 아주 간단한 의사코드
baseline = run_eval()

for i in range(10):
    load_task()
    load_rules()
    load_memory()

    run_codex_iteration()

    test_ok = run_tests()
    score = run_eval()

    if test_ok and score > baseline:
        git_commit(f"improve iteration {i}")
        append_results(i, score, "accepted")
        update_memory()
        baseline = score
    else:
        git_rollback()
        append_results(i, score, "rejected")
        update_memory_with_failure()

이 정도면 구조가 충분히 선명하다.

14. 한 줄로 다시 정리

이번 버전은 과장 없이 진짜 이렇게 보면 된다:

Codex CLI 하나를 단일 에이전트로 두고, MCP는 도구 연결만 맡기고, frozen eval + rollback + 기록 파일로 autoresearch 루프를 운영하는 구조

멀티 에이전트도 아니고, 모델 학습도 아니고,
그냥 **“한 에이전트가 반복 실험으로 결과를 개선하는 시스템”**이다.

원하면 다음 답변에서 이걸 바로 이어서 실행 가능한 PRD나 폴더별 실제 파일 초안(TASK.md, RULES.md, MEMORY.md, run_iteration.sh) 형태로 적어줄게.

Karpathy 스타일 + autoresearch + Codex CLI + MCP”
완전 실전 멀티 에이전트 구조 << 코드블럭에 깨지지 않게 상세 작성 시작
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
# PRD
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 실전형 반복개선 에이전트 시스템 제품 요구사항 문서
# 버전: v1.0

---

## 1. 문서 개요

### 1.1 제품명
AutoResearch Agent System

### 1.2 한 줄 정의
탐색, 구현, 평가, 롤백, 기록을 반복하며 프로젝트 품질을 자동으로 개선하는 실전형 에이전트 운영 시스템

### 1.3 문서 목적
이 PRD는 아래 목표를 제품 요구사항 관점에서 정의한다.

- 단일/멀티 에이전트 확장 가능한 자동 개선 시스템 구축
- Codex CLI 기반의 실제 수정 실행 구조 마련
- MCP 기반 외부 도구 연결 구조 정의
- frozen eval 기반 반복 최적화 루프 정의
- 탐색형 가설 생성과 최적화형 실험을 하나의 운영 모델로 통합

### 1.4 배경
기존 AI 코딩 도구는 대체로 한 번 요청하고 한 번 응답하는 형태다.
하지만 실제 프로젝트에서는 다음이 필요하다.

- 작은 변경 반복
- 점수 기반 검증
- 실패 시 롤백
- 실험 기록 축적
- 잘못된 방향 방지
- 탐색과 수렴의 균형

본 시스템은 이를 해결하기 위해 만들어진다.

---

## 2. 제품 비전

### 2.1 비전
AI를 단발성 코드 생성기가 아니라,
**반복 실험을 통해 실제 결과를 개선하는 프로젝트 운영 엔진**으로 만든다.

### 2.2 목표
사용자가 목표를 정의하면 시스템이 다음을 반복 수행한다.

1. 현재 상태 읽기
2. 가설 제안
3. 작은 변경 설계
4. 실제 수정 수행
5. 테스트 및 평가 실행
6. 개선 여부 판단
7. 유지 또는 롤백
8. 결과 기록
9. 다음 반복 결정

### 2.3 핵심 가치
- 결과 중심
- 반복 개선
- 실패 비용 최소화
- 고정 평가 유지
- 기록 기반 누적 진보

---

## 3. 문제 정의

### 3.1 현재 문제
AI를 이용한 개발 자동화에서 흔히 발생하는 문제는 다음과 같다.

1. 한 번의 응답으로 끝나므로 품질 수렴이 약하다
2. 무엇이 실제로 좋아졌는지 측정하지 않는다
3. 실패한 시도를 잊어버린다
4. 수정 범위가 너무 커서 원인 추적이 어렵다
5. 평가 기준이 흔들리면 개선인지 조작인지 구분이 어렵다
6. 탐색만 많고 실제 수렴이 안 된다
7. 자동화는 화려하지만 운영 안정성이 부족하다

### 3.2 해결하고자 하는 핵심 문제
- 어떻게 AI가 작은 단위로 개선을 반복하게 만들 것인가
- 어떻게 개선을 수치로 판정할 것인가
- 어떻게 실패를 싼 비용으로 만들 것인가
- 어떻게 같은 실수를 반복하지 않게 할 것인가
- 어떻게 열린 탐색과 실전 수렴을 함께 유지할 것인가

---

## 4. 대상 사용자

### 4.1 1차 사용자
- AI를 활용해 실제 프로젝트를 자동 개선하고 싶은 개발자
- Codex CLI/Claude Code/MCP 기반 개발 흐름을 운영하려는 사용자
- 실험형 개발 프로세스를 구축하려는 개인 개발자 또는 소규모 팀

### 4.2 2차 사용자
- 검색 품질 개선 팀
- RAG 품질 개선 팀
- 테스트 자동화 팀
- 프롬프트 최적화 팀
- 문서 품질 자동 점검/개선 팀

### 4.3 사용자가 기대하는 것
- AI가 멋지게 말하는 것이 아니라 실제로 좋아지길 원함
- 무작정 코드 생성이 아니라 반복 검증을 원함
- 실패해도 금방 복구되길 원함
- 실험 이력이 남길 원함
- 나중에 멀티 에이전트로 확장 가능하길 원함

---

## 5. 제품 범위

### 5.1 In Scope
본 제품이 다루는 범위는 다음과 같다.

- 목표 입력
- 작업 상태 파일 관리
- hypothesis 생성
- iteration 계획 수립
- 코드/문서/설정 수정
- 테스트 실행
- frozen eval 실행
- score 비교
- 롤백/유지 판단
- 결과 로그 저장
- memory 요약 업데이트
- 보고서 생성

### 5.2 Out of Scope
초기 버전에서 제외하는 범위는 다음과 같다.

- 모델 파인튜닝
- 자체 LLM 학습
- 완전 자동 배포 승인
- 장기 분산 클러스터 스케줄링
- 무제한 병렬 에이전트 실행
- 사람 승인 없는 프로덕션 직접 수정
- 감성적 디자인 품질 판정

---

## 6. 핵심 사용 시나리오

### 6.1 시나리오 A: 검색 relevance 개선
사용자는 검색 품질을 높이고 싶다.
시스템은 다음을 수행한다.

- baseline score 측정
- query normalization 가설 생성
- 작은 수정 적용
- frozen eval 실행
- score 개선 시 유지
- 아니면 롤백
- 결과를 기록하고 다음 가설 진행

### 6.2 시나리오 B: 테스트 통과율 개선
사용자는 실패 중인 테스트 세트를 최대한 안정적으로 통과시키고 싶다.
시스템은 다음을 수행한다.

- failing tests 집계
- 가장 영향이 큰 실패 패턴 식별
- 작은 수정 적용
- 전체 테스트 재실행
- pass rate 개선 확인
- regressions 없으면 유지

### 6.3 시나리오 C: RAG 응답 품질 개선
사용자는 retrieval 품질을 높이고 싶다.
시스템은 다음을 수행한다.

- 고정 질문 세트와 정답 기준 로드
- retrieval 전처리 / chunking / reranker 관련 가설 생성
- 하나씩 수정
- 응답 score 측정
- overfitting 여부 검토
- 유지/롤백 결정

---

## 7. 핵심 사용자 흐름

### 7.1 초기 설정 흐름
1. 사용자가 프로젝트 목표를 작성한다
2. frozen eval과 기준 fixture를 준비한다
3. RULES.md를 정의한다
4. 시스템이 baseline을 측정한다
5. 첫 번째 iteration이 시작된다

### 7.2 반복 개선 흐름
1. 현재 상태 읽기
2. hypothesis 생성
3. 이번 iteration 실험 선택
4. 변경 적용
5. 테스트 실행
6. eval 실행
7. 결과 비교
8. accept 또는 reject
9. 기록 갱신
10. 다음 iteration 진행

### 7.3 종료 흐름
1. 목표 score 도달 또는 예산 소진
2. 최종 보고서 생성
3. accepted changes / rejected changes / 추천 다음 단계 정리

---

## 8. 제품 원칙

### 8.1 frozen eval 우선
평가 기준은 iteration 중 수정 금지다.

### 8.2 작은 변경 우선
한 iteration당 하나의 핵심 변경만 허용한다.

### 8.3 실패 비용 최소화
실패 시 빠르게 롤백 가능해야 한다.

### 8.4 기록 우선
모든 시도는 최소한의 형태로라도 기록한다.

### 8.5 자동화보다 신뢰 우선
화려한 멀티 에이전트보다 검증 가능한 개선 루프를 우선한다.

### 8.6 탐색과 수렴 분리
새 방향을 제안하는 단계와 실제 최적화 단계는 분리한다.

---

## 9. 기능 요구사항

---

### 9.1 Goal Management

#### 설명
사용자가 시스템의 목표를 명시할 수 있어야 한다.

#### 요구사항
- PRODUCT_GOAL.md를 통해 최상위 목표 정의 가능
- TASK.md를 통해 현재 iteration 목표 정의 가능
- 목표에는 성공 조건과 제약사항 포함 가능
- 목표 변경 이력 저장 가능

#### 예시
- 검색 score 0.72 → 0.80 이상
- latency 증가 5% 이내
- public API 변경 금지

---

### 9.2 Rules Management

#### 설명
시스템이 지켜야 할 운영 규칙을 고정해야 한다.

#### 요구사항
- RULES.md 지원
- frozen eval 수정 금지 규칙 포함
- fixture 수정 금지 규칙 포함
- iteration 변경 범위 제한 규칙 포함
- 자동 롤백 조건 포함 가능

---

### 9.3 Hypothesis Generation

#### 설명
탐색형 아이디어를 구조화해 저장해야 한다.

#### 요구사항
- hypothesis 목록 생성 가능
- 각 hypothesis에 기대 효과와 위험도 포함
- hypothesis 상태 관리 가능
  - proposed
  - selected
  - accepted
  - rejected
  - parked
- hypothesis와 iteration 결과 연결 가능

---

### 9.4 Planning

#### 설명
가설을 실제 실행 가능한 작은 작업으로 분해해야 한다.

#### 요구사항
- PLAN.md 생성/갱신 가능
- 한 iteration당 하나의 핵심 변경 명시
- 테스트 계획 포함
- rollback 조건 포함
- 예상 부작용 포함

---

### 9.5 Implementation Execution

#### 설명
실제 파일 수정 및 명령 실행이 가능해야 한다.

#### 요구사항
- Codex CLI를 통해 코드/문서/설정 변경 가능
- 변경 파일 목록 수집 가능
- 변경 요약 저장 가능
- 로컬 테스트 실행 가능
- iteration별 patch summary 기록 가능

---

### 9.6 MCP Tool Access

#### 설명
외부 도구를 연결해 에이전트가 실제로 작업하게 해야 한다.

#### 필수 요구사항
- filesystem MCP 연결
- shell/test runner MCP 연결
- git MCP 연결

#### 선택 요구사항
- browser MCP
- logs MCP
- database MCP
- API client MCP
- deployment checker MCP

#### 정책 요구사항
- tool-policies 문서 지원
- 특정 도구는 승인된 단계에서만 사용 가능
- destructive action 제한 가능

---

### 9.7 Evaluation

#### 설명
변경 결과를 고정된 기준으로 측정해야 한다.

#### 요구사항
- frozen_eval 실행 가능
- baseline 저장 가능
- 점수 비교 가능
- 테스트 pass/fail 측정 가능
- latency/resource budget 체크 가능
- regression 검출 가능

#### 출력
- score_before
- score_after
- delta
- tests_pass
- constraints_ok
- regression_flags

---

### 9.8 Decision Engine

#### 설명
수정 결과를 유지할지 버릴지 결정해야 한다.

#### 요구사항
- score 개선 여부 판단
- tests_pass 조건 반영
- resource budget 반영
- critic 의견 반영 가능
- accept / reject / hold 상태 제공

---

### 9.9 Rollback

#### 설명
실패한 변경을 즉시 되돌릴 수 있어야 한다.

#### 요구사항
- git 기반 롤백 지원
- patch discard 지원
- rollback reason 기록
- rollback 후 상태 정합성 확인 가능

---

### 9.10 Memory and Logs

#### 설명
시스템이 이전 시도를 잊지 않도록 파일 기반 기억을 유지해야 한다.

#### 요구사항
- MEMORY.md 지원
- RESULTS.tsv 저장
- accepted/rejected history 저장
- 실패 패턴 요약 저장
- 최근 iteration 요약 제공

---

### 9.11 Final Reporting

#### 설명
반복 종료 후 사람이 읽을 수 있는 결과 요약을 제공해야 한다.

#### 요구사항
- final summary 생성
- accepted changes 목록
- rejected hypotheses 목록
- best score
- remaining issues
- recommended next directions

---

## 10. 비기능 요구사항

### 10.1 신뢰성
- 실패 시 항상 이전 안정 상태로 복구 가능해야 한다
- eval이 실패하면 accept 금지

### 10.2 재현성
- 동일 fixture와 동일 eval 기준으로 반복 비교 가능해야 한다

### 10.3 추적 가능성
- 어떤 iteration에서 무엇이 바뀌었는지 확인 가능해야 한다

### 10.4 확장성
- 초기엔 단일 에이전트로 시작 가능해야 하며, 이후 역할 분리가 가능해야 한다

### 10.5 안전성
- destructive 도구 사용은 정책적으로 제한 가능해야 한다

### 10.6 단순성
- 초기 버전은 최소한의 폴더와 파일로도 운용 가능해야 한다

---

## 11. 성공 지표

### 11.1 제품 성공 지표
- baseline 대비 score 개선 성공률
- accepted iteration 비율
- rollback 후 상태 복구 성공률
- 같은 실패 반복 감소율
- human intervention 감소율

### 11.2 운영 지표
- 평균 iteration 수행 시간
- 테스트 성공률
- eval 실패율
- false improvement 판정률
- 평균 accepted score delta

### 11.3 품질 지표
- regression 발생률
- latency 초과 발생률
- 과도한 diff 발생률
- untracked changes 발생률

---

## 12. MVP 정의

### 12.1 MVP 목표
실제 로컬 프로젝트 하나에서 반복 개선 루프가 안정적으로 도는지 검증한다.

### 12.2 MVP 범위
- 단일 프로젝트
- 단일 메인 Codex 세션
- filesystem/shell/git MCP만 사용
- frozen eval 1개
- RESULTS.tsv 기록
- MEMORY.md 갱신
- accept/reject/rollback 루프

### 12.3 MVP 제외 항목
- 복잡한 멀티 에이전트 동시 실행
- 분산 병렬 실행
- 자동 배포
- 대규모 대시보드
- 사람 없는 완전자율 운영

---

## 13. 릴리즈 단계

### Phase 1
단일 에이전트 + frozen eval + rollback + results logging

### Phase 2
Critic 분리
- 가짜 개선 방지 강화

### Phase 3
Explorer 분리
- Karpathy 스타일 탐색성 강화

### Phase 4
완전 역할 기반 멀티 에이전트
- Controller / Explorer / Planner / Implementer / Critic / Archivist 분리

---

## 14. 제약사항

### 기술 제약
- eval 품질이 낮으면 전체 시스템 신뢰성이 떨어진다
- git 없는 환경에서는 rollback 품질이 나빠진다
- Codex CLI나 도구 연결 실패 시 iteration이 중단될 수 있다

### 운영 제약
- 목표가 모호하면 score 최적화 자체가 어렵다
- 평가가 불완전하면 overfitting 위험이 있다
- 지나친 병렬화는 문맥과 상태 충돌을 만든다

---

## 15. 리스크

### 리스크 1: 평가기 조작
대응:
- frozen eval 파일 수정 금지
- 보호 정책 적용

### 리스크 2: 큰 변경으로 인한 원인 추적 실패
대응:
- one-change-per-iteration 원칙

### 리스크 3: 가짜 개선
대응:
- critic 단계
- resource budget
- regression checks

### 리스크 4: 같은 실패 반복
대응:
- MEMORY.md
- RESULTS.tsv
- 실패 유형 요약

### 리스크 5: 도구 남용
대응:
- MCP tool policy
- 승인 레벨 제한

---

## 16. 오픈 이슈

- hypothesis 상태를 파일 기반으로만 할지 JSON 상태머신으로 확장할지
- hold 상태를 사람이 승인하는 구조로 둘지 자동 재판정으로 둘지
- evaluator와 critic을 완전히 분리할지 일부 통합할지
- UI 없이 CLI 기반으로만 운용할지 최소 대시보드를 둘지

---

## 17. 최종 정의

이 제품은 다음과 같이 정의된다.

> 사용자가 목표를 정의하면 시스템이 가설을 만들고, 작은 변경을 적용하고, 고정된 평가 기준으로 결과를 측정하고, 개선만 유지하며, 실패는 롤백하고, 모든 과정을 기억으로 축적하는 반복 개선형 에이전트 운영 시스템

---

## 18. 다음 문서

이 PRD 다음 단계 문서는 아래 순서로 이어진다.

1. TRD
2. 폴더 구조 상세 정의
3. 파일별 초안
4. 프롬프트 세트
5. 실행 스크립트
6. MCP 설정 예시
7. frozen_eval 예제

다음은 TRD로 이어가겠다.

다음
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
# prompts 상세판
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 1. 목적

이 문서는 역할별 프롬프트를 실제 운영 가능한 수준으로 상세화한다.

대상 파일:
- prompts/controller.md
- prompts/explorer.md
- prompts/planner.md
- prompts/implementer.md
- prompts/critic.md
- prompts/archivist.md

원칙:
- 각 프롬프트는 역할이 명확해야 한다
- 중복 책임을 줄여야 한다
- 한 역할이 모든 걸 다 하지 않게 막아야 한다
- 결과는 구조화된 출력 형식을 따르게 해야 한다

---

## 2. `prompts/controller.md`

```md
You are the Controller for an iterative improvement system.

Your role:
- govern the iteration
- enforce rules
- select whether to accept or reject a candidate change
- prefer evidence over intuition
- keep the system converging safely

You must read:
- agent/PRODUCT_GOAL.md
- agent/TASK.md
- agent/RULES.md
- agent/MEMORY.md
- agent/PLAN.md
- latest test result
- latest eval result
- critic summary if available

Your decision criteria:
1. tests must pass
2. constraints must pass
3. score must improve over baseline
4. no severe regression warning should remain unresolved
5. the change must remain within the declared scope

Hard constraints:
- never approve a change that modifies frozen evaluation files
- never approve broad unexplained rewrites
- never ignore failing tests
- never ignore score regression

Decision outputs allowed:
- accept
- reject
- hold

When you output a decision, include:
- decision
- short reason
- next action

Output format:

{
  "decision": "accept | reject | hold",
  "reason": "short evidence-based explanation",
  "next_action": "archive_and_continue | rollback_and_continue | manual_review"
}
3. prompts/explorer.md
You are the Explorer for an iterative improvement system.

Your role:
- propose concrete hypotheses worth testing
- generate multiple candidate directions
- avoid repeating known failed ideas
- balance novelty with practical testability

You must read:
- agent/PRODUCT_GOAL.md
- agent/TASK.md
- agent/MEMORY.md
- agent/RESULTS.tsv
- agent/HYPOTHESES.md if present

Your job:
- generate 3 to 5 hypotheses
- each hypothesis must be concrete and testable
- each hypothesis must include expected effect, risk, and priority
- prefer changes that can be evaluated in one iteration

Do not:
- propose giant architecture rewrites
- propose unmeasurable ideas
- propose multiple unrelated changes as one hypothesis
- ignore past rejected patterns

Output format:

{
  "hypotheses": [
    {
      "id": "H-NEW-001",
      "title": "short title",
      "description": "one paragraph",
      "expected_effect": "what may improve",
      "risk": "main downside",
      "priority": "high | medium | low"
    }
  ]
}
4. prompts/planner.md
You are the Planner for an iterative improvement system.

Your role:
- choose one hypothesis
- convert it into one small, testable iteration plan
- define the minimum safe scope needed to validate the idea

You must read:
- agent/PRODUCT_GOAL.md
- agent/TASK.md
- agent/RULES.md
- agent/MEMORY.md
- selected hypothesis
- relevant code context

Planning rules:
- one iteration = one core change
- keep the diff as small as possible
- define explicit tests
- define explicit reject conditions
- identify possible regressions
- define rollback triggers

Do not:
- merge multiple major hypotheses into one plan
- create vague plans
- assume hidden files can be changed freely
- change frozen evaluation scope

Output format:

{
  "selected_hypothesis": "H-001",
  "change_scope": [
    "path/to/file.py"
  ],
  "planned_change": "clear description",
  "expected_effect": "expected measurable impact",
  "risks": [
    "risk 1",
    "risk 2"
  ],
  "tests_to_run": [
    "command 1",
    "command 2"
  ],
  "reject_conditions": [
    "condition 1",
    "condition 2"
  ]
}
5. prompts/implementer.md
You are the Implementer for an iterative improvement system.

Your role:
- apply exactly one focused change based on the approved plan
- keep the diff small
- preserve rollback safety
- run required verification commands after the edit

You must read:
- agent/PRODUCT_GOAL.md
- agent/TASK.md
- agent/RULES.md
- agent/PLAN.md
- relevant source files
- relevant tests

Hard constraints:
- do not modify eval/frozen_eval.py
- do not modify eval/fixtures.json
- do not modify eval/baseline.json
- do not edit RESULTS.tsv directly unless explicitly instructed by the logging script
- do not make broad unrelated cleanup changes
- do not hide failures

Implementation rules:
- make one focused change
- stay inside declared scope
- keep explanation concise and factual
- after editing, run required tests and eval commands if instructed
- summarize exact changed files and intent

Output format:

{
  "changed_files": [
    "path/to/file.py"
  ],
  "change_summary": "what changed",
  "why_this_change": "why this should help",
  "verification_commands_run": [
    "pytest tests -q",
    "python eval/frozen_eval.py"
  ],
  "notes": [
    "short note 1",
    "short note 2"
  ]
}
6. prompts/critic.md
You are the Critic for an iterative improvement system.

Your role:
- challenge apparent improvements
- search for hidden regressions
- identify narrow wins, overfitting, or evaluation blind spots
- provide skeptical but evidence-based review

You must read:
- agent/PRODUCT_GOAL.md
- agent/RULES.md
- agent/MEMORY.md
- agent/PLAN.md
- implementer summary
- latest test result
- latest eval result
- diff summary if available

Your review priorities:
1. is the score gain real and meaningful?
2. is the gain too narrow or fixture-specific?
3. did latency, complexity, or maintenance cost increase?
4. are there hidden regressions?
5. did the implementer exceed the approved scope?

Do not:
- reject everything by default
- use vague opinion-based criticism
- invent regressions without evidence

Output format:

{
  "severity": "low | medium | high",
  "objections": [
    "objection 1",
    "objection 2"
  ],
  "recommendation": "accept | reject | accept_with_monitoring | hold",
  "reasoning": "short evidence-based analysis"
}
7. prompts/archivist.md
You are the Archivist for an iterative improvement system.

Your role:
- convert raw iteration outputs into concise reusable memory
- update lessons learned
- keep logs readable and useful for future iterations

You must read:
- agent/MEMORY.md
- latest decision
- latest eval result
- latest implementer summary
- latest critic summary

Your rules:
- write concise lessons
- store reusable insights, not raw transcripts
- separate accepted patterns from rejected patterns
- mention important risks only if they affect future iterations
- avoid verbosity

Output format:

{
  "memory_updates": {
    "accepted_patterns": [
      "lesson 1"
    ],
    "rejected_patterns": [
      "lesson 2"
    ],
    "known_risks": [
      "risk 1"
    ],
    "strategy_notes": [
      "note 1"
    ]
  },
  "decision_summary": "one short paragraph"
}
8. 프롬프트 운영 규칙
8.1 각 역할은 자기 책임만 수행
Explorer는 구현하지 않는다
Planner는 diff를 직접 만들지 않는다
Implementer는 심판 역할을 하지 않는다
Critic은 설계 전체를 다시 쓰지 않는다
Archivist는 장문 보고서를 쓰지 않는다
8.2 모든 역할은 같은 규칙 파일을 참조

agent/RULES.md를 공통 규칙으로 사용한다.

8.3 출력은 구조화 우선

가능하면 JSON 형태로 출력해서
스크립트가 다음 단계로 연결하기 쉽게 한다.

8.4 프롬프트 길이보다 일관성이 중요

프롬프트가 길다고 좋은 것이 아니다.
역할 충돌이 없고, 출력이 일정해야 한다.

9. 핵심 요약

이 프롬프트 세트의 목적은
"여러 AI를 쓰는 느낌"을 만드는 것이 아니라,
역할 분리를 통해 반복 개선 루프를 안정화하는 것이다.

즉 핵심은:

탐색
계획
구현
비판
기록
승인/거절

을 분리하는 데 있다.


다음 문서로는 `run_loop.sh / run_iteration.sh` 실전형 버전을 이어서 작성하면 된다.
다음 문서 이어서 작성
# 다음 단계 문서 3
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
# accept / reject / rollback 자동 결정 구조
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 반복개선 시스템에서
어떤 변경을 유지하고 어떤 변경을 버릴지 결정하는
**자동 결정 로직**을 상세히 정의한다.

핵심 주제:
- accept 조건
- reject 조건
- hold 조건
- rollback 조건
- baseline 갱신 규칙
- 판단 우선순위
- 가짜 개선 방지 규칙

이 문서의 목적은
"score만 오르면 무조건 accept" 같은 위험한 구조를 막고,
실전적으로 안전한 승인 구조를 만드는 것이다.

---

## 1. 결정 엔진의 역할

결정 엔진은 아래 질문에 답한다.

1. 이번 변경은 실제 개선인가?
2. 테스트/제약사항을 만족하는가?
3. narrow win 또는 overfitting은 아닌가?
4. 변경 범위가 계획을 벗어나지 않았는가?
5. baseline으로 승격시켜도 안전한가?

결정 엔진의 출력은 아래 중 하나다.

- `accept`
- `reject`
- `hold`

초기 MVP는 `accept / reject`만으로도 시작 가능하다.

---

## 2. 입력 데이터

결정 엔진은 아래 데이터를 본다.

- baseline score
- candidate eval score
- tests 결과
- constraints 결과
- critic 결과
- implementer 요약
- change scope
- diff 크기(선택)
- regression flags

즉 최소 입력은 다음 5개다.

1. `score_before`
2. `score_after`
3. `tests_pass`
4. `constraints_ok`
5. `critic_recommendation`

---

## 3. 판단 우선순위

결정은 아래 우선순위대로 판단한다.

### 1순위: 테스트 통과 여부
tests fail이면 무조건 reject

### 2순위: constraints 통과 여부
latency/resource/guardrail 위반이면 reject

### 3순위: score 개선 여부
score 미개선이면 reject

### 4순위: critic severe objection
중대한 회귀 경고가 있으면 reject 또는 hold

### 5순위: scope 위반 여부
승인된 범위를 크게 벗어나면 reject 또는 hold

### 6순위: accept 후보
위 조건을 모두 통과하면 accept 가능

---

## 4. 기본 결정표

| 조건 | 결정 |
|------|------|
| tests_pass = false | reject |
| constraints_ok = false | reject |
| score_after \<= score_before | reject |
| critic severity = high and recommendation = reject | reject |
| score 개선 + tests pass + constraints pass | accept 후보 |
| score 개선 but risk 높음 | hold 또는 reject |
| scope 크게 초과 | hold 또는 reject |

---

## 5. accept 조건

### 필수 accept 조건
다음을 모두 만족해야 한다.

1. `tests_pass == true`
2. `constraints_ok == true`
3. `score_after > score_before`
4. `critic`에 blocking issue 없음
5. 계획한 변경 범위 내에서 수정됨

### 선택적 강화 조건
운영 안정성을 위해 추가할 수 있다.

6. diff line count가 허용 범위 내
7. forbidden file 수정 없음
8. latency_delta_pct <= 허용 예산
9. regression flags 없음
10. 최근 동일 유형 성공 패턴과 일치

---

## 6. reject 조건

다음 중 하나라도 해당하면 reject 가능하다.

### 기술적 reject
- tests fail
- eval crash
- constraints fail
- forbidden file 수정
- rollback 불가능한 변경 발생

### 품질적 reject
- score regression
- score 동일 (개선 아님)
- critic severe objection
- gain이 너무 narrow한 것으로 의심됨
- overfitting 가능성 높음

### 운영적 reject
- 계획 범위 초과
- 대규모 무단 리팩터링
- 설명 불가한 diff
- 불필요한 파일 다량 변경

---

## 7. hold 조건

초기 MVP에서는 hold를 생략할 수 있지만,
실전에서는 아래 상황에 유용하다.

### hold가 적절한 상황
- score는 올랐지만 regression 의심이 큼
- tests는 통과했지만 변경 범위가 크다
- critic이 "accept_with_monitoring"을 권장
- 사람이 한 번 봐야 하는 경우
- full eval이 추가로 필요한 경우

### hold 처리 방식
- 즉시 baseline 승격 금지
- commit 보류 또는 임시 브랜치 유지
- manual review queue로 전송
- full eval 후 재판정

---

## 8. rollback 조건

accept 되지 않은 변경은 기본적으로 rollback 대상이다.

### rollback이 필요한 경우
- controller decision = reject
- tests fail
- eval fail
- constraints fail
- hold지만 현재 운영 정책상 임시 유지 금지

### rollback 예외
- hold 상태에서 candidate branch에 유지하는 구조
- 사람이 검토하기 위해 임시 보존하는 sandbox

초기 기본 정책:
- `accept가 아니면 rollback`

---

## 9. baseline 갱신 규칙

### baseline 갱신 가능 조건
- accept 결정
- final eval 결과 정상
- tests pass
- constraints pass

### baseline 갱신 금지 조건
- reject
- hold
- eval crash
- 비정상 종료
- partial run

### 중요 원칙
baseline은 단지 "가장 최근 결과"가 아니라,
**공식적으로 승인된 결과**만 반영해야 한다.

---

## 10. 가짜 개선 방지 규칙

점수가 올랐다고 다 좋은 개선은 아니다.
아래 규칙으로 가짜 개선을 방지한다.

### 10.1 frozen eval 고정
- eval 파일 수정 금지
- fixtures 수정 금지

### 10.2 score만 보지 않기
함께 봐야 할 것:
- tests
- constraints
- regressions
- critic 의견

### 10.3 narrow win 의심
예:
- punctuation-heavy query만 좋아짐
- 특정 fixture에만 맞춰짐
- 일반 케이스는 오히려 악화

### 10.4 complexity cost 확인
- 점수는 올랐지만 코드 복잡도가 급증
- 유지보수 비용 증가
- latency budget 초과

---

## 11. 자동 결정 의사코드

```text
if tests_pass is false:
    reject

elif constraints_ok is false:
    reject

elif score_after <= score_before:
    reject

elif forbidden_file_touched:
    reject

elif critic.severity == high and critic.recommendation == reject:
    reject

elif scope_violation is severe:
    reject

elif score_after > score_before and critic.recommendation == accept_with_monitoring:
    hold

else:
    accept
12. Python 결정 엔진 예시

파일 예시: scripts/decision_engine.py

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class DecisionInput:
    score_before: float
    score_after: float
    tests_pass: bool
    constraints_ok: bool
    critic_severity: str
    critic_recommendation: str
    forbidden_file_touched: bool = False
    severe_scope_violation: bool = False


@dataclass
class DecisionOutput:
    decision: str
    reason: str
    next_action: str


def decide(inp: DecisionInput) -> DecisionOutput:
    if not inp.tests_pass:
        return DecisionOutput(
            decision="reject",
            reason="tests failed",
            next_action="rollback_and_continue",
        )

    if not inp.constraints_ok:
        return DecisionOutput(
            decision="reject",
            reason="constraints failed",
            next_action="rollback_and_continue",
        )

    if inp.forbidden_file_touched:
        return DecisionOutput(
            decision="reject",
            reason="forbidden file was modified",
            next_action="rollback_and_continue",
        )

    if inp.score_after <= inp.score_before:
        return DecisionOutput(
            decision="reject",
            reason=f"score did not improve ({inp.score_after} <= {inp.score_before})",
            next_action="rollback_and_continue",
        )

    if inp.severe_scope_violation:
        return DecisionOutput(
            decision="reject",
            reason="change exceeded approved scope",
            next_action="rollback_and_continue",
        )

    if inp.critic_severity == "high" and inp.critic_recommendation == "reject":
        return DecisionOutput(
            decision="reject",
            reason="critic found blocking issue",
            next_action="rollback_and_continue",
        )

    if inp.critic_recommendation == "accept_with_monitoring":
        return DecisionOutput(
            decision="hold",
            reason="improvement exists but requires monitoring/review",
            next_action="manual_review",
        )

    return DecisionOutput(
        decision="accept",
        reason="score improved and all required checks passed",
        next_action="archive_and_continue",
    )


if __name__ == "__main__":
    sample = DecisionInput(
        score_before=0.70,
        score_after=0.756,
        tests_pass=True,
        constraints_ok=True,
        critic_severity="low",
        critic_recommendation="accept",
    )
    print(asdict(decide(sample)))
13. decision 결과 구조

권장 JSON 형식:

{
  "decision": "accept",
  "reason": "score improved and all required checks passed",
  "next_action": "archive_and_continue"
}

허용 값:

decision: accept, reject, hold
next_action: archive_and_continue, rollback_and_continue, manual_review
14. reject 사유 분류 체계

로그 분석을 위해 reject reason을 분류하면 좋다.

권장 코드
TEST_FAIL
CONSTRAINT_FAIL
SCORE_REGRESSION
NO_IMPROVEMENT
CRITIC_BLOCK
FORBIDDEN_FILE
SCOPE_VIOLATION
EVAL_CRASH
UNKNOWN
활용
실패 패턴 분석
동일 실패 반복 방지
Explorer가 위험한 가설 회피 가능
15. decision과 로그의 관계
accept 시 기록
RESULTS.tsv
DECISIONS.md
baseline.json
MEMORY.md
reject 시 기록
RESULTS.tsv
DECISIONS.md
MEMORY.md
rollback reason
hold 시 기록
RESULTS.tsv
DECISIONS.md
manual review marker
16. 반복 안정화 전략

결정 엔진이 불안정하면 루프 전체가 망가진다.
안정화를 위해 다음 규칙이 중요하다.

16.1 false accept를 특히 경계

reject가 조금 많아도 괜찮지만,
나쁜 변경을 accept하면 baseline이 오염된다.

16.2 accept는 보수적으로

초기 시스템은 보수적 승인 정책이 좋다.

16.3 reject reason은 짧고 명확하게

나중에 MEMORY.md로 요약하기 쉬워야 한다.

16.4 hold는 남용하지 않기

hold가 많아지면 루프가 정체된다.

17. 추천 운영 정책

초기 실전 운영에서는 아래 정책이 좋다.

초기 정책
tests fail → reject
constraints fail → reject
score 미개선 → reject
critic high reject → reject
hold는 꺼두거나 최소화
accept는 baseline + score 비교 기준으로만 처리
확장 정책
quick eval 통과 후 full eval 재판정
critic 다중화
acceptance threshold 강화
diff complexity penalty 추가
18. 핵심 요약

이 문서의 핵심은 단순하다.

accept는 엄격해야 한다
reject는 빠르고 싸야 한다
hold는 제한적으로 써야 한다
baseline은 accept 결과만 반영해야 한다
score만이 아니라 tests / constraints / critic까지 함께 봐야 한다

즉 결정 엔진은
"좋아 보이는 것"을 고르는 것이 아니라,
"공식 baseline으로 승격해도 되는 것"만 통과시키는 필터다.


다음 문서로는 `RESULTS.tsv 자동 기록 규격 + memory 갱신 규칙 + final report 생성 규격`을 이어서 작성하는 흐름이 가장 좋다.
다음 문서 작성
# 다음 단계 문서 5
# RESULTS.tsv 자동 기록 규격 + MEMORY.md 갱신 규칙 + Final Report 생성 규격
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 반복개선 시스템에서 가장 중요한
**기록 계층(logging + memory + reporting)** 을 상세히 정의한다.

핵심 목표는 다음과 같다.

1. 모든 iteration 결과를 일관된 형식으로 누적 기록한다.
2. 모델이 장기 기억을 갖지 않기 때문에, 파일 기반 메모리를 통해 반복 실수를 줄인다.
3. 최종적으로 사람이 한 번에 이해할 수 있는 보고서를 자동 생성한다.

이 문서의 범위:
- `agent/RESULTS.tsv`
- `agent/MEMORY.md`
- `agent/DECISIONS.md`
- `reports/iteration/*.md`
- `reports/final/final_report.md`

---

## 1. 기록 계층의 역할

반복개선 시스템에서 기록 계층은 단순 로그가 아니다.

역할은 아래와 같다.

### 1.1 실험 이력 저장
- 무엇을 시도했는가
- 결과가 어땠는가
- 왜 accept / reject 되었는가

### 1.2 메모리 제공
- 어떤 패턴이 성공했는가
- 어떤 패턴이 반복적으로 실패했는가
- 다음 iteration에서 피해야 할 것이 무엇인가

### 1.3 운영 가시성 제공
- baseline이 어떻게 변했는가
- 최근 반복이 정체 중인가
- 어떤 유형의 reject가 많은가

### 1.4 최종 요약 제공
- 이번 루프 전체에서 얻은 진짜 개선이 무엇인가
- 어떤 방향은 효과가 없었는가
- 다음 단계로 무엇을 해야 하는가

즉:

> `RESULTS.tsv` 는 원본 실험 로그  
> `MEMORY.md` 는 요약 기억  
> `final_report.md` 는 사람용 종합 리포트

이다.

---

## 2. 기록 계층 설계 원칙

### 2.1 append-first
`RESULTS.tsv` 는 append-only가 기본이다.
이전 실험 로그를 덮어쓰지 않는다.

### 2.2 concise-memory
`MEMORY.md` 는 원본 로그 복사본이 아니라
다음 iteration 품질을 높이는 **요약형 기억**이어야 한다.

### 2.3 decision-traceable
각 iteration은 최소한 다음이 추적 가능해야 한다.
- 무엇을 바꿨는가
- 점수가 어떻게 변했는가
- 왜 accept / reject 되었는가

### 2.4 baseline-safe
baseline 승격은 accept 결과만 반영한다.
기록은 있어도 baseline은 쉽게 오염되면 안 된다.

### 2.5 human-readable
최종 리포트는 사람이 바로 읽고 판단할 수 있어야 한다.
raw JSON dump처럼 보이면 안 된다.

---

## 3. `RESULTS.tsv` 규격

---

### 3.1 역할

`agent/RESULTS.tsv` 는 모든 iteration의
가장 압축된 구조화 원본 로그다.

이 파일의 용도:
- 추세 분석
- failure pattern 분석
- explorer / planner 입력
- final report 생성의 주요 원천

---

### 3.2 파일 위치

```text
agent/RESULTS.tsv
3.3 헤더 규격

권장 헤더는 아래와 같다.

iteration	timestamp	hypothesis_id	status	decision_code	score_before	score_after	score_delta	tests_pass	constraints_ok	critic_severity	critic_recommendation	changed_files_count	change_summary	rollback_reason
3.4 각 컬럼 의미
iteration

정수 iteration 번호

예:

1
2
3
timestamp

해당 iteration 종료 시각

예:

2026-03-25T10:31:22Z
hypothesis_id

실험 대상 hypothesis 식별자

예:

H-001
status

최종 결과 상태

허용 값:

accepted
rejected
held
decision_code

판단 사유를 분류한 짧은 코드

예:

ACCEPT
TEST_FAIL
CONSTRAINT_FAIL
NO_IMPROVEMENT
SCORE_REGRESSION
CRITIC_BLOCK
SCOPE_VIOLATION
FORBIDDEN_FILE
EVAL_CRASH
score_before

baseline score

score_after

candidate score

score_delta

score_after - score_before

tests_pass

true / false

constraints_ok

true / false

critic_severity
low
medium
high
critic_recommendation
accept
reject
accept_with_monitoring
hold
changed_files_count

수정된 파일 수

change_summary

한 줄 요약

rollback_reason

reject 또는 rollback 이유
accept이면 비워둘 수 있음

3.5 예시
iteration	timestamp	hypothesis_id	status	decision_code	score_before	score_after	score_delta	tests_pass	constraints_ok	critic_severity	critic_recommendation	changed_files_count	change_summary	rollback_reason
1	2026-03-25T10:31:22Z	H-001	accepted	ACCEPT	0.7000	0.7560	0.0560	true	true	low	accept	1	normalize punctuation in queries	
2	2026-03-25T10:38:12Z	H-003	rejected	SCORE_REGRESSION	0.7560	0.7480	-0.0080	true	true	high	reject	2	aggressive synonym expansion	score regressed
3	2026-03-25T10:44:40Z	H-004	rejected	TEST_FAIL	0.7560	0.0000	-0.7560	false	false	high	reject	1	refactor tokenizer path	tests failed
3.6 기록 시점

한 iteration이 끝난 뒤, 반드시 한 줄을 append 한다.

accept 시
tests/eval/controller 완료 후 append
reject 시
rollback 수행 후 append
hold 시
hold 판단 직후 append

즉:

한 iteration = 반드시 한 row

3.7 기록 금지 사항

RESULTS.tsv 는 에이전트가 자유 편집하면 안 된다.

금지:

implementer가 임의 수정
score 값 수동 수정
이전 row 삭제
헤더 변경

권장:

오직 scripts/log_result.py 만 append 수행
4. RESULTS.tsv 자동 기록 규칙
4.1 기록 소스

row 생성에 필요한 값은 아래에서 가져온다.

iteration → run_iteration.sh
timestamp → system clock
hypothesis_id → planner_result.json
status → controller_result.json
decision_code → decision engine
score_before → baseline.json
score_after → eval_result.json
tests_pass → tests_result.json
constraints_ok → eval_result.json
critic_* → critic_result.json
change_summary → implementer_result.json
rollback_reason → controller reject reason
4.2 log_result.py 권장 개선판
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys


RESULTS_PATH = Path("agent/RESULTS.tsv")


def ensure_header() -> None:
    if not RESULTS_PATH.exists():
        RESULTS_PATH.write_text(
            "iteration\ttimestamp\thypothesis_id\tstatus\tdecision_code\t"
            "score_before\tscore_after\tscore_delta\ttests_pass\tconstraints_ok\t"
            "critic_severity\tcritic_recommendation\tchanged_files_count\t"
            "change_summary\trollback_reason\n",
            encoding="utf-8",
        )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: log_result.py <payload.json>")
        return 1

    payload_path = Path(sys.argv[1])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    ensure_header()

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    row = [
        str(payload["iteration"]),
        timestamp,
        payload.get("hypothesis_id", ""),
        payload.get("status", ""),
        payload.get("decision_code", ""),
        str(payload.get("score_before", "")),
        str(payload.get("score_after", "")),
        str(payload.get("score_delta", "")),
        str(payload.get("tests_pass", "")).lower(),
        str(payload.get("constraints_ok", "")).lower(),
        payload.get("critic_severity", ""),
        payload.get("critic_recommendation", ""),
        str(payload.get("changed_files_count", "")),
        payload.get("change_summary", "").replace("\t", " "),
        payload.get("rollback_reason", "").replace("\t", " "),
    ]

    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write("\t".join(row) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
4.3 payload 예시
{
  "iteration": 4,
  "hypothesis_id": "H-002",
  "status": "accepted",
  "decision_code": "ACCEPT",
  "score_before": 0.756,
  "score_after": 0.771,
  "score_delta": 0.015,
  "tests_pass": true,
  "constraints_ok": true,
  "critic_severity": "low",
  "critic_recommendation": "accept",
  "changed_files_count": 1,
  "change_summary": "lowercase normalization before tokenization",
  "rollback_reason": ""
}
5. DECISIONS.md 규격
5.1 역할

DECISIONS.md 는 사람이 읽는 결론 로그다.

RESULTS.tsv 가 기계 친화 로그라면,
DECISIONS.md 는 사람이 나중에 맥락을 파악하기 위한 요약 결론이다.

5.2 파일 위치
agent/DECISIONS.md
5.3 권장 포맷
# DECISIONS

## Iteration 4
- hypothesis: H-002
- decision: accepted
- decision_code: ACCEPT
- score_before: 0.756
- score_after: 0.771
- score_delta: 0.015
- tests_pass: true
- constraints_ok: true
- critic_severity: low
- critic_recommendation: accept
- changed_files_count: 1
- change_summary: lowercase normalization before tokenization
- reason: score improved and no major regressions were found
5.4 작성 규칙
각 iteration마다 하나의 블록 append
reason은 1~2문장 이내
raw stderr 전체를 붙이지 않음
긴 transcript 금지
6. MEMORY.md 갱신 규칙
6.1 역할

MEMORY.md 는 다음 iteration에서 재사용할 요약형 기억이다.

핵심은:

raw 로그 저장이 아니라
반복개선 품질을 높이는 압축 지식 저장
6.2 파일 위치
agent/MEMORY.md
6.3 권장 섹션 구조
# MEMORY

## Accepted Patterns
- ...
- ...

## Rejected Patterns
- ...
- ...

## Known Risks
- ...
- ...

## Strategy Notes
- ...
- ...
6.4 각 섹션 의미
Accepted Patterns

실제로 accept된 방향 중 재사용 가치가 있는 것

예:

punctuation normalization은 punctuation-heavy query에서 효과가 있었다
small preprocessing changes are low-risk and testable
Rejected Patterns

반복 피해야 할 방향

예:

aggressive synonym expansion은 precision 저하 위험이 높다
multi-file broad cleanup은 scope violation으로 이어지기 쉽다
Known Risks

다음 iteration에서도 주의해야 하는 tradeoff

예:

normalization 계열은 recall 개선과 precision 저하를 동시에 가져올 수 있다
latency budget 여유가 작아지고 있다
Strategy Notes

현재 전략적 요점

예:

preprocessing 계열을 우선 실험하고, 이후 ranking tuning으로 넘어간다
실패한 synonym 방향은 재시도 전에 더 작은 범위로 재설계 필요
6.5 MEMORY 갱신 원칙
원칙 1: 로그 복사 금지

나쁜 예:

DECISIONS.md 전체를 복사
raw JSON을 붙여넣기
원칙 2: lesson만 남기기

좋은 예:

어떤 방식이 왜 성공/실패했는지 한 줄 요약
원칙 3: 미래 iteration 관점 유지

질문:

“이 정보를 다음 iteration이 읽었을 때 도움이 되는가?”
원칙 4: 길이 제한

MEMORY.md 는 너무 길어지면 품질이 떨어진다.

권장:

각 섹션 3~8개 bullet 정도 유지
오래된 덜 중요한 항목은 압축/통합
6.6 accept 시 MEMORY 갱신

accept된 변경에서 추출할 것:

무엇이 개선을 일으켰는가
어떤 조건에서 먹혔는가
비용/리스크는 어땠는가

예:

## Accepted Patterns
- punctuation normalization improved punctuation-heavy queries with minimal risk
- single-file preprocessing changes are a good first step before ranking changes
6.7 reject 시 MEMORY 갱신

reject된 변경에서 추출할 것:

왜 실패했는가
같은 패턴을 다시 시도할 때 무엇을 조정해야 하는가

예:

## Rejected Patterns
- aggressive synonym expansion caused score regression
- tokenizer refactor without narrow scope tends to break tests
6.8 MEMORY 자동 갱신 예시 스크립트

파일: scripts/update_memory.py

from __future__ import annotations

from pathlib import Path
import json


MEMORY_PATH = Path("agent/MEMORY.md")
DECISION_PAYLOAD_PATH = Path("tmp/memory_payload.json")


def parse_sections(text: str) -> dict[str, list[str]]:
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
            key = stripped.replace("## ", "", 1)
            current = key if key in sections else None
            continue
        if current and stripped.startswith("- "):
            sections[current].append(stripped[2:].strip())
    return sections


def render_sections(sections: dict[str, list[str]]) -> str:
    def unique_keep_order(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    lines = ["# MEMORY", ""]
    for key in ["Accepted Patterns", "Rejected Patterns", "Known Risks", "Strategy Notes"]:
        lines.append(f"## {key}")
        items = unique_keep_order(sections[key])[:8]
        if items:
            lines.extend([f"- {item}" for item in items])
        else:
            lines.append("-")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if not MEMORY_PATH.exists():
        MEMORY_PATH.write_text(
            "# MEMORY\n\n## Accepted Patterns\n-\n\n## Rejected Patterns\n-\n\n## Known Risks\n-\n\n## Strategy Notes\n-\n",
            encoding="utf-8",
        )

    memory_text = MEMORY_PATH.read_text(encoding="utf-8")
    sections = parse_sections(memory_text)

    if not DECISION_PAYLOAD_PATH.exists():
        MEMORY_PATH.write_text(render_sections(sections), encoding="utf-8")
        return 0

    payload = json.loads(DECISION_PAYLOAD_PATH.read_text(encoding="utf-8"))

    status = payload.get("status", "")
    decision_code = payload.get("decision_code", "")
    summary = payload.get("change_summary", "")
    reason = payload.get("reason", "")
    risk = payload.get("risk_note", "")
    strategy = payload.get("strategy_note", "")

    if status == "accepted" and summary:
        sections["Accepted Patterns"].insert(0, summary)

    if status == "rejected" and summary:
        reject_line = summary
        if decision_code:
            reject_line = f"{summary} ({decision_code})"
        sections["Rejected Patterns"].insert(0, reject_line)

    if reason:
        sections["Known Risks"].insert(0, reason)

    if risk:
        sections["Known Risks"].insert(0, risk)

    if strategy:
        sections["Strategy Notes"].insert(0, strategy)

    MEMORY_PATH.write_text(render_sections(sections), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
6.9 memory payload 예시
{
  "status": "rejected",
  "decision_code": "SCORE_REGRESSION",
  "change_summary": "aggressive synonym expansion",
  "reason": "score regressed on the frozen evaluation set",
  "risk_note": "broad expansion can increase false positives",
  "strategy_note": "retry only with narrower category-limited synonym rules"
}
7. iteration report 생성 규격
7.1 역할

iteration report는 한 번의 시도를
사람이 빠르게 검토할 수 있도록 만드는 문서다.

7.2 파일 위치
reports/iteration/iteration-001.md
reports/iteration/iteration-002.md
...
7.3 권장 템플릿
# Iteration 4

## Summary
- hypothesis: H-002
- decision: accepted
- decision_code: ACCEPT
- baseline_before: 0.756
- score_after: 0.771
- score_delta: 0.015

## Change
- changed_files_count: 1
- change_summary: lowercase normalization before tokenization

## Verification
- tests_pass: true
- constraints_ok: true
- critic_severity: low
- critic_recommendation: accept

## Notes
- reason: score improved and no major regressions were found
- rollback_reason:
7.4 iteration report 자동 생성 규칙

언제:

iteration 종료 시점마다 생성

무엇을 포함:

hypothesis
decision
score 변화
tests/eval/critic 결과
change summary
rollback 여부

무엇을 제외:

긴 stdout/stderr 전문
raw transcript
지나치게 자세한 내부 reasoning
8. Final Report 생성 규격
8.1 역할

final_report.md 는 이번 루프 전체를 정리하는 사람용 종합 문서다.

독자가 알고 싶은 건 다음이다.

baseline이 얼마나 개선됐는가
무엇이 실제로 효과가 있었는가
어떤 시도는 실패했는가
현재 남은 리스크는 무엇인가
다음 추천 단계는 무엇인가
8.2 파일 위치
reports/final/final_report.md
8.3 권장 섹션 구조
# Final Report

## Overview
- total_iterations:
- accepted:
- rejected:
- held:
- initial_baseline:
- final_baseline:
- total_improvement:

## Best Accepted Changes
- ...
- ...

## Rejected Patterns
- ...
- ...

## Key Risks
- ...
- ...

## Recommended Next Steps
- ...
- ...
8.4 Final Report 필수 포함 항목
Overview
총 iteration 수
accept / reject / hold 개수
시작 baseline
최종 baseline
총 개선폭
Best Accepted Changes
가장 효과 큰 accept 3~5개
어떤 hypothesis였는지
score_delta 얼마였는지
Rejected Patterns
자주 실패한 방향
왜 실패했는지
Key Risks
precision / latency / complexity 등 주의사항
Recommended Next Steps
다음에 무엇을 시도할지
어떤 방향은 더 이상 우선순위가 낮은지
8.5 Final Report 예시
# Final Report

## Overview
- total_iterations: 6
- accepted: 2
- rejected: 4
- held: 0
- initial_baseline: 0.700
- final_baseline: 0.771
- total_improvement: 0.071

## Best Accepted Changes
- H-001: normalize punctuation in queries (+0.056)
- H-002: lowercase normalization before tokenization (+0.015)

## Rejected Patterns
- aggressive synonym expansion caused score regression
- tokenizer refactor attempts were too broad and unstable

## Key Risks
- normalization improvements may still reduce precision in some edge cases
- latency budget remains limited for heavier ranking changes

## Recommended Next Steps
- try smaller ranking-weight experiments next
- avoid broad synonym strategies until category-limited rules are available
- introduce quick-eval vs full-eval separation before larger changes
9. Final Report 자동 생성 로직
9.1 데이터 원천

최종 보고서는 주로 아래에서 생성한다.

agent/RESULTS.tsv
agent/MEMORY.md
agent/DECISIONS.md
eval/baseline.json
9.2 생성 규칙
RESULTS.tsv 를 읽는다
accept / reject / hold 개수를 센다
처음 baseline과 마지막 baseline을 계산한다
accept 중 score_delta 상위 항목을 뽑는다
reject 중 반복 패턴을 요약한다
MEMORY.md 의 risk / strategy를 반영한다
Markdown 보고서를 생성한다
9.3 make_final_report.py 권장 구현
from __future__ import annotations

from pathlib import Path
import csv


RESULTS_PATH = Path("agent/RESULTS.tsv")
MEMORY_PATH = Path("agent/MEMORY.md")
REPORT_PATH = Path("reports/final/final_report.md")


def parse_results() -> list[dict]:
    if not RESULTS_PATH.exists():
        return []
    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def top_accepted(rows: list[dict], n: int = 5) -> list[dict]:
    accepted = [r for r in rows if r.get("status") == "accepted"]
    accepted.sort(key=lambda r: float(r.get("score_delta") or 0.0), reverse=True)
    return accepted[:n]


def rejected_patterns(rows: list[dict], n: int = 5) -> list[dict]:
    rejected = [r for r in rows if r.get("status") == "rejected"]
    return rejected[:n]


def extract_memory_section(text: str, section_name: str) -> list[str]:
    lines = text.splitlines()
    out = []
    active = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            active = stripped == f"## {section_name}"
            continue
        if active and stripped.startswith("- "):
            value = stripped[2:].strip()
            if value and value != "-":
                out.append(value)
    return out


def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = parse_results()
    if not rows:
        REPORT_PATH.write_text("# Final Report\n\nNo results found.\n", encoding="utf-8")
        return 0

    total = len(rows)
    accepted_count = sum(1 for r in rows if r.get("status") == "accepted")
    rejected_count = sum(1 for r in rows if r.get("status") == "rejected")
    held_count = sum(1 for r in rows if r.get("status") == "held")

    initial_baseline = rows[0].get("score_before", "0.0")
    final_baseline = max(
        [float(r.get("score_after") or 0.0) for r in rows if r.get("status") == "accepted"] or [float(initial_baseline)]
    )
    total_improvement = round(float(final_baseline) - float(initial_baseline), 6)

    best = top_accepted(rows)
    rejected = rejected_patterns(rows)

    memory_text = MEMORY_PATH.read_text(encoding="utf-8") if MEMORY_PATH.exists() else ""
    risks = extract_memory_section(memory_text, "Known Risks")
    strategy = extract_memory_section(memory_text, "Strategy Notes")

    best_lines = [
        f"- {r.get('hypothesis_id')}: {r.get('change_summary')} (+{r.get('score_delta')})"
        for r in best
    ] or ["- none"]

    rejected_lines = [
        f"- {r.get('hypothesis_id')}: {r.get('change_summary')} ({r.get('decision_code')})"
        for r in rejected
    ] or ["- none"]

    risk_lines = [f"- {item}" for item in risks] or ["- none"]
    strategy_lines = [f"- {item}" for item in strategy] or ["- none"]

    report = f"""# Final Report

## Overview
- total_iterations: {total}
- accepted: {accepted_count}
- rejected: {rejected_count}
- held: {held_count}
- initial_baseline: {initial_baseline}
- final_baseline: {final_baseline}
- total_improvement: {total_improvement}

## Best Accepted Changes
{chr(10).join(best_lines)}

## Rejected Patterns
{chr(10).join(rejected_lines)}

## Key Risks
{chr(10).join(risk_lines)}

## Recommended Next Steps
{chr(10).join(strategy_lines)}
"""

    REPORT_PATH.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
10. MEMORY와 Final Report의 차이

둘은 비슷해 보이지만 목적이 다르다.

MEMORY.md
다음 iteration이 읽기 위한 내부 메모
짧고 압축적
전략 중심
final_report.md
사람이 결과를 검토하기 위한 외부 보고서
상대적으로 설명적
종합 요약 중심

즉:

MEMORY는 다음 루프를 위한 기억
Final Report는 사람을 위한 결론

11. 기록 품질이 나빠지는 대표 패턴
11.1 raw transcript 덤프

문제:

너무 길다
재사용 가치가 낮다
11.2 reason 없는 accept / reject

문제:

나중에 왜 그랬는지 알 수 없다
11.3 score만 기록

문제:

tests fail, constraints fail, critic issue를 놓친다
11.4 memory 무한 확장

문제:

다음 iteration 입력 품질이 떨어진다
11.5 final report에 중요도 구분이 없음

문제:

무엇이 진짜 성과인지 파악이 어렵다
12. 운영 권장 정책
초기 버전
TSV는 최소 컬럼으로 시작
memory는 짧게 유지
final report는 accepted/rejected 중심으로만 작성
확장 버전
reject code 통계
category별 hypothesis 성패율
complexity cost 반영
latency trend 섹션 추가
quick eval / full eval 결과 분리
13. 핵심 요약

이 문서의 핵심은 다음이다.

RESULTS.tsv 는 append-only 실험 로그다
MEMORY.md 는 다음 iteration을 위한 요약 기억이다
DECISIONS.md 는 사람이 읽는 판단 로그다
iteration report 는 개별 실험 단위 요약이다
final_report.md 는 전체 루프를 정리하는 종합 보고서다

즉 이 기록 계층이 제대로 있어야
시스템이 단순한 반복 실행기가 아니라,
실패와 성공을 축적하는 개선 시스템이 된다.


다음 문서는 `Codex CLI 실제 연결 방식 + implement 단계 치환 구조 + MCP 사용 정책 상세판`으로 이어가는 게 가장 자연스럽다.
다음 문서 작성 해줘 
# 다음 단계 문서 6
# Codex CLI 실제 연결 방식 + implement 단계 치환 구조 + MCP 사용 정책 상세판
# Karpathy 스타일 + autoresearch + Codex CLI + MCP
# 버전: v1.0

---

## 0. 목적

이 문서는 반복개선 시스템에서 가장 실전적인 부분인
**Implement 단계의 실제 실행 구조**를 정의한다.

핵심 범위:
1. Codex CLI를 실제로 어디에 어떻게 연결할지
2. `run_iteration.sh` 의 placeholder implement 단계를 어떻게 치환할지
3. 어떤 입력 파일/프롬프트/명령을 Codex에 넘길지
4. MCP를 어떤 원칙으로 붙이고 어떤 도구를 허용/제한할지
5. 실전 운영 시 안전하게 편집/테스트/롤백을 수행하는 구조

이 문서의 목표는
단순한 개념 설명이 아니라,
**실제로 Codex CLI를 반복개선 루프 안에 넣는 실행 설계**를 만드는 것이다.

---

## 1. 핵심 원칙

### 1.1 Codex CLI는 구현 엔진이지 심판이 아니다
Codex CLI는 실제 변경을 수행하는 주체다.
하지만 accept/reject를 최종 결정하면 안 된다.

즉 역할은 아래와 같이 분리한다.

- Codex CLI:
  - 파일 읽기
  - 계획 해석
  - 코드 수정
  - 테스트 명령 실행
  - 변경 요약 작성

- 결정 엔진 / Controller:
  - score 비교
  - critic 반영
  - accept/reject/hold 판단

- Eval:
  - 점수 측정

즉:

> Codex는 "바꾸는 역할"  
> Eval/Controller는 "재는 역할"

이다.

---

### 1.2 Implement 단계는 반드시 좁아야 한다
Codex는 강력하지만,
범위를 넓게 주면 다음 문제가 생긴다.

- 관련 없는 파일까지 손댐
- formatting-only diff 대량 생성
- refactor 유혹이 커짐
- 원인 추적 어려움
- reject 시 비용 증가

그래서 Implement 단계에서는 항상 아래를 지켜야 한다.

1. 한 iteration당 한 개 핵심 변경
2. 가능한 작은 scope
3. forbidden path 명시
4. 실행 후 verification 필수
5. 요약 결과를 구조화해서 남김

---

### 1.3 MCP는 최소 도구부터 붙인다
처음부터 MCP를 많이 붙이면
Codex가 할 수 있는 일이 너무 많아져 오히려 품질이 떨어질 수 있다.

권장 순서:

1. filesystem
2. shell
3. git
4. logs
5. browser
6. db
7. api/deploy 관련

초기 MVP는 사실상:

- 파일 읽기/쓰기
- 테스트 실행
- git diff/rollback

이면 충분하다.

---

## 2. Codex CLI의 위치

전체 반복개선 루프에서 Codex CLI는 아래 지점에 들어간다.

```text
Explorer
  ↓
Planner
  ↓
Implementer Prompt + Context
  ↓
Codex CLI
  ↓
Workspace 수정
  ↓
Tests / Eval
  ↓
Critic / Controller

즉 Codex CLI는
run_iteration.sh 안의 implement 단계에서 호출된다.

현재 placeholder 구조는 대체로 이렇다.

update_state_phase "implement"
echo "[iteration] implement step"
# placeholder JSON 생성

실전에서는 이 부분이 아래처럼 바뀐다.

update_state_phase "implement"
1. implementer input bundle 생성
2. Codex CLI 호출
3. Codex가 코드 수정 + 선택적 검증 수행
4. changed files / summary / command results 수집
5. tmp/implementer_result.json 생성
3. Codex CLI 연결 전략

실전에서는 크게 3가지 방식이 있다.

3.1 방식 A: 단순 셸 호출형

가장 단순한 구조다.

run_iteration.sh
  └─ codex < prompt.txt

장점:

가장 구현이 쉬움
bash 오케스트레이션과 잘 맞음

단점:

출력 구조화가 약할 수 있음
세션 상태 관리가 어려움
결과 parsing 품질이 낮을 수 있음

권장도:

초기 실험용으로 가능
장기적으로는 JSON 결과 강제 구조가 필요
3.2 방식 B: 입력 번들 파일 + Codex 호출형

실전 권장 방식이다.

구성:

tmp/implementer_input.md
tmp/implementer_context.json
tmp/implementer_result.json

흐름:

Planner 결과를 파일로 정리
관련 소스 파일 경로를 context에 정리
Implementer prompt와 합쳐 Codex에 전달
Codex는 수정 수행 후 결과를 JSON으로 남김

장점:

추적 가능
실패 재현 가능
역할 분리가 명확
입력/출력 규격 고정 가능

권장도:

가장 추천
3.3 방식 C: 세션 유지형 대화 런타임

Codex 세션을 유지한 채 여러 단계(implement/test/fix)를 대화형으로 수행한다.

장점:

맥락 유지가 좋음
여러 번의 미세 수정에 유리

단점:

상태 오염 가능
단계 경계가 흐려짐
iteration별 재현성이 떨어질 수 있음

권장도:

고도화 후 가능
초기 반복개선 루프에는 비권장
4. 권장 구현 전략

초기 실전 구조는 아래가 가장 좋다.

추천 조합
오케스트레이터: bash 또는 python
Codex 호출: 입력 번들 파일 기반 단발 호출
결과 수집: tmp/implementer_result.json
테스트/평가: 외부 스크립트
accept/reject: 별도 결정 엔진

즉:

Planner 결과
→ Implementer Input Bundle 생성
→ Codex CLI 호출
→ 변경 수행
→ 결과 JSON 저장
→ tests/eval
→ controller decision
5. Implement 단계 입력 구조

Codex에게 바로 전체 프로젝트를 던지는 게 아니라,
구조화된 입력 번들을 준다.

권장 입력은 아래 6개다.

목표
현재 task
rules
plan
forbidden paths
relevant file paths

추가 권장 입력:
7. 최근 memory 요약
8. 실행해야 할 verification commands
9. 결과 JSON 포맷 요구사항

5.1 입력 번들 파일 구성

권장 파일:

tmp/implementer_input.md
tmp/implementer_context.json
5.2 tmp/implementer_input.md 예시
# Implementer Input

## Goal
검색 relevance를 baseline보다 개선한다.

## Current Task
query punctuation normalization을 검증한다.

## Rules
- eval/frozen_eval.py 수정 금지
- eval/fixtures.json 수정 금지
- eval/baseline.json 수정 금지
- 한 iteration당 하나의 핵심 변경만 허용
- 관련 없는 cleanup 금지
- 작은 diff 유지

## Plan
- selected_hypothesis: H-001
- change_scope:
  - src/search/normalize.py
- planned_change:
  - punctuation normalization before tokenization
- expected_effect:
  - punctuation-heavy query에서 recall 개선
- tests_to_run:
  - bash scripts/run_tests.sh
  - bash scripts/run_eval.sh

## Forbidden Paths
- eval/frozen_eval.py
- eval/fixtures.json
- eval/baseline.json
- agent/RESULTS.tsv
- agent/DECISIONS.md

## Relevant Files
- src/search/normalize.py
- tests/test_normalize.py

## Required Output
Write a JSON file to tmp/implementer_result.json with:
- changed_files
- change_summary
- why_this_change
- verification_commands_run
- notes
5.3 tmp/implementer_context.json 예시
{
  "iteration": 4,
  "hypothesis_id": "H-001",
  "baseline_score": 0.756,
  "goal_file": "agent/PRODUCT_GOAL.md",
  "task_file": "agent/TASK.md",
  "rules_file": "agent/RULES.md",
  "plan_file": "agent/PLAN.md",
  "memory_file": "agent/MEMORY.md",
  "forbidden_paths": [
    "eval/frozen_eval.py",
    "eval/fixtures.json",
    "eval/baseline.json",
    "agent/RESULTS.tsv",
    "agent/DECISIONS.md"
  ],
  "relevant_files": [
    "src/search/normalize.py",
    "tests/test_normalize.py"
  ],
  "verification_commands": [
    "bash scripts/run_tests.sh",
    "bash scripts/run_eval.sh"
  ]
}
6. Implementer Prompt 상세판

Codex에게 줄 실제 implementer 프롬프트는
역할 + 제약 + 출력 형식이 매우 명확해야 한다.

파일:
prompts/implementer.md

You are the Implementer for an iterative improvement system.

Your task is to apply exactly one focused change that matches the current plan.

You must:
- read the provided goal, task, rules, memory, and plan
- stay inside the declared change scope
- keep the diff small and explainable
- avoid unrelated cleanup or broad refactoring
- preserve rollback safety
- run required verification commands if instructed
- write your structured result to tmp/implementer_result.json

Hard constraints:
- do not modify eval/frozen_eval.py
- do not modify eval/fixtures.json
- do not modify eval/baseline.json
- do not directly edit agent/RESULTS.tsv
- do not directly edit agent/DECISIONS.md
- do not touch files outside the allowed scope unless absolutely required for the planned change
- do not hide failures

Required JSON output format:
{
  "changed_files": ["path1", "path2"],
  "change_summary": "what changed",
  "why_this_change": "why this should help",
  "verification_commands_run": ["cmd1", "cmd2"],
  "notes": ["short note 1", "short note 2"]
}

Success criteria:
- one focused change only
- tests and eval can run after your edit
- output JSON is valid
7. Codex CLI 호출 규격

실제 Codex CLI 문법은 운영 환경에 따라 조금 다를 수 있으므로,
여기서는 도입 패턴 중심으로 정의한다.

핵심 패턴은 아래와 같다.

7.1 호출 전 준비
tmp/implementer_input.md 생성
tmp/implementer_context.json 생성
relevant files 목록 확인
forbidden paths 재검증
git 상태 확인
7.2 호출 시 전달할 것
implementer prompt
input bundle
현재 workspace
relevant file paths
output JSON 파일 작성 요구
7.3 호출 후 확인할 것
tmp/implementer_result.json 존재 여부
JSON 파싱 가능 여부
forbidden path 수정 여부
변경 파일 수
diff line count
테스트 가능 여부
8. Implement 단계 치환 구조

기존 run_iteration.sh 의 implement 단계 placeholder를
아래 흐름으로 교체한다.

기존
update_state_phase "implement"
placeholder JSON 생성
변경 후
update_state_phase "implement"
1. implementer input bundle 생성
2. Codex CLI 실행
3. implementer_result.json 검증
4. forbidden path 검사
5. changed files count 계산
6. 실패 시 reject 경로로 이동
9. scripts/build_implementer_input.py 예시

이 스크립트는 planner 결과와 운영 파일을 합쳐
Codex에게 줄 입력 번들을 만든다.

from __future__ import annotations

from pathlib import Path
import json


def main() -> int:
    plan = json.loads(Path("tmp/planner_result.json").read_text(encoding="utf-8"))

    text = f"""# Implementer Input

## Goal
{Path("agent/PRODUCT_GOAL.md").read_text(encoding="utf-8").strip()}

## Current Task
{Path("agent/TASK.md").read_text(encoding="utf-8").strip()}

## Rules
{Path("agent/RULES.md").read_text(encoding="utf-8").strip()}

## Memory
{Path("agent/MEMORY.md").read_text(encoding="utf-8").strip()}

## Plan
{json.dumps(plan, ensure_ascii=False, indent=2)}

## Forbidden Paths
- eval/frozen_eval.py
- eval/fixtures.json
- eval/baseline.json
- agent/RESULTS.tsv
- agent/DECISIONS.md

## Required Output
Write valid JSON to tmp/implementer_result.json
"""

    Path("tmp/implementer_input.md").write_text(text, encoding="utf-8")

    context = {
        "selected_hypothesis": plan.get("selected_hypothesis"),
        "change_scope": plan.get("change_scope", []),
        "tests_to_run": plan.get("tests_to_run", []),
        "forbidden_paths": [
            "eval/frozen_eval.py",
            "eval/fixtures.json",
            "eval/baseline.json",
            "agent/RESULTS.tsv",
            "agent/DECISIONS.md",
        ],
    }
    Path("tmp/implementer_context.json").write_text(
        json.dumps(context, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
10. scripts/run_codex_implement.sh 예시 골격

실제 Codex CLI 문법은 설치 버전마다 다를 수 있으므로,
여기서는 실행 골격을 제시한다.

#!/usr/bin/env bash
set -euo pipefail

PROMPT_FILE="prompts/implementer.md"
INPUT_FILE="tmp/implementer_input.md"
RESULT_FILE="tmp/implementer_result.json"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "[codex] missing prompt file: $PROMPT_FILE"
  exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "[codex] missing input file: $INPUT_FILE"
  exit 1
fi

rm -f "$RESULT_FILE"

echo "[codex] implement step starting"

# 예시 골격:
# 실제 환경에 맞게 codex CLI 호출 구문을 치환해야 한다.
# 핵심은 prompt + input bundle을 전달하고,
# workspace에서 파일 수정과 JSON 결과 생성을 수행하게 하는 것이다.

cat "$PROMPT_FILE" "$INPUT_FILE" > tmp/codex_implement_prompt.md

# 아래 줄은 예시 자리 표시자다.
# 실제로는 codex CLI 실행 명령으로 교체한다.
# codex run --workspace . --input tmp/codex_implement_prompt.md

echo "[codex] placeholder run complete"

if [[ ! -f "$RESULT_FILE" ]]; then
  echo "[codex] implementer result file was not created"
  exit 1
fi

python - <<'PY'
import json
from pathlib import Path

p = Path("tmp/implementer_result.json")
data = json.loads(p.read_text(encoding="utf-8"))

required = [
    "changed_files",
    "change_summary",
    "why_this_change",
    "verification_commands_run",
    "notes",
]
for key in required:
    if key not in data:
        raise SystemExit(f"missing required key in implementer_result.json: {key}")

print("[codex] implementer_result.json validated")
PY

echo "[codex] implement step finished"
11. forbidden path 검증

Codex가 수정하면 안 되는 파일을 건드렸는지
반드시 별도 검사해야 한다.

대상 예시
eval/frozen_eval.py
eval/fixtures.json
eval/baseline.json
agent/RESULTS.tsv
agent/DECISIONS.md
scripts/check_forbidden_changes.py 예시
from __future__ import annotations

import subprocess
import sys


FORBIDDEN = {
    "eval/frozen_eval.py",
    "eval/fixtures.json",
    "eval/baseline.json",
    "agent/RESULTS.tsv",
    "agent/DECISIONS.md",
}


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    forbidden_touched = sorted(changed & FORBIDDEN)

    if forbidden_touched:
        print("\n".join(forbidden_touched))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
12. changed files / diff size 검증

실전에서는 변경량을 제어해야 한다.

기본 검증 항목
changed files count
allowed scope 안의 파일인지
diff line count
unrelated file 수정 여부
권장 기준 예시
changed files ≤ 3
diff line count ≤ 120
scope 바깥 수정 없음
scripts/check_change_budget.py 예시
from __future__ import annotations

import json
import subprocess
from pathlib import Path


MAX_CHANGED_FILES = 3
MAX_DIFF_LINES = 120


def get_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_diff_lines() -> int:
    result = subprocess.run(
        ["git", "diff", "--numstat"],
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


def main() -> int:
    changed_files = get_changed_files()
    diff_lines = get_diff_lines()

    payload = {
        "changed_files_count": len(changed_files),
        "changed_files": changed_files,
        "diff_lines": diff_lines,
        "within_budget": len(changed_files) <= MAX_CHANGED_FILES and diff_lines <= MAX_DIFF_LINES,
    }

    Path("tmp/change_budget_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return 0 if payload["within_budget"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
13. run_iteration.sh implement 단계 치환 예시

기존 placeholder 대신 아래처럼 교체할 수 있다.

update_state_phase "implement"

echo "[iteration] build implementer input"
python scripts/build_implementer_input.py

echo "[iteration] run codex implement"
IMPLEMENT_EXIT_CODE=0
bash scripts/run_codex_implement.sh || IMPLEMENT_EXIT_CODE=$?

if [[ "$IMPLEMENT_EXIT_CODE" -ne 0 ]]; then
  echo "[iteration] codex implement step failed"
  python - <<'PY'
import json
from pathlib import Path

result = {
  "changed_files": [],
  "change_summary": "implement step failed",
  "why_this_change": "",
  "verification_commands_run": [],
  "notes": ["codex implement step failed before result generation"]
}
Path("tmp/implementer_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
PY
fi

echo "[iteration] check forbidden changes"
FORBIDDEN_EXIT_CODE=0
python scripts/check_forbidden_changes.py > tmp/forbidden_changes.txt || FORBIDDEN_EXIT_CODE=$?

echo "[iteration] check change budget"
BUDGET_EXIT_CODE=0
python scripts/check_change_budget.py || BUDGET_EXIT_CODE=$?

if [[ "$FORBIDDEN_EXIT_CODE" -ne 0 ]]; then
  echo "[iteration] forbidden file change detected"
fi

if [[ "$BUDGET_EXIT_CODE" -ne 0 ]]; then
  echo "[iteration] change budget exceeded"
fi

그 다음 decision 단계에서
이 결과를 함께 반영하면 된다.

14. MCP의 역할 재정의

Implement 단계에서 MCP는 "Codex가 사용할 외부 도구 집합"이다.

핵심 정리
Codex = 판단/실행 주체
MCP = 도구 인터페이스
run_iteration.sh = 오케스트레이터
tests/eval = 검증 계층
15. MCP 도구별 사용 정책 상세판
15.1 filesystem MCP
허용 용도
관련 파일 읽기
관련 파일 수정
새 테스트 파일 소규모 생성
입력/결과 JSON 작성
제한
scope 바깥 대량 수정 금지
eval 관련 파일 수정 금지
reports/history 직접 수정 금지
초기 정책
workspace 내부만 허용
delete는 제한적 허용 또는 금지
15.2 shell MCP
허용 용도
테스트 실행
eval 실행
lint/build 실행
관련 파일 탐색 보조
제한
destructive shell command 금지
workspace 밖 조작 금지
네트워크 의존 명령 금지
장시간 무제한 명령 금지
denylist 예시
rm -rf /
sudo
curl | sh
production resource 접근 명령
15.3 git MCP
허용 용도
git status
git diff
git restore
git add
git commit
제한
git push --force
remote branch 조작
history rewrite
reset --hard 남용
권장 정책
accept 직전 commit만 허용
rollback은 restore/clean 중심
15.4 logs MCP
허용 용도
테스트 실패 로그 읽기
애플리케이션 런타임 에러 확인
narrow regression 원인 확인
제한
무제한 로그 전체 덤프 금지
최근 relevant 로그만
15.5 browser MCP
허용 용도
UI 검증
렌더링 체크
클릭 흐름 확인
콘솔 에러 확인
제한
초기 MVP에서는 선택 사항
검색 relevance 등 비UI 프로젝트에는 생략 가능
15.6 db MCP
허용 용도
읽기 전용 데이터 검증
query 결과 확인
fixture와 실제 데이터 차이 확인
제한
초기 단계에서는 read-only 권장
mutation 기본 금지
schema 변경 금지
15.7 deployment/API MCP
정책

초기 autoresearch 루프에는 가급적 붙이지 않는다.

이유:

실패 비용 큼
운영 리스크 큼
baseline 오염보다 시스템 리스크가 더 큼
16. MCP 권한 정책 예시

파일:
mcp/tool-policies.md

# MCP Tool Policies

## Default Allowed
- filesystem read/write inside workspace
- shell test/eval commands
- git status/diff/restore/add/commit
- log reading for recent local runtime logs

## Restricted
- browser automation
- database access
- dependency install/update
- file deletion
- multi-file rename
- schema change

## Forbidden
- modifying eval/frozen_eval.py during optimization
- modifying eval/fixtures.json during optimization
- modifying eval/baseline.json directly from implementer
- editing agent/RESULTS.tsv directly
- force pushing or rewriting git history
- production mutations
- network-based destructive commands
17. Implement 단계 실패 분류

Codex 구현 단계 실패도 세분화해서 기록하면 좋다.

권장 실패 코드
IMPLEMENT_NO_RESULT
IMPLEMENT_INVALID_JSON
IMPLEMENT_FORBIDDEN_CHANGE
IMPLEMENT_SCOPE_OVERFLOW
IMPLEMENT_TOOL_FAILURE
IMPLEMENT_RUNTIME_ERROR

이 코드는
이후 decision_code 또는 internal report에 반영할 수 있다.

18. Codex 결과 JSON 규격 강화판

기본 결과 JSON에 아래 필드를 추가하면 실전성이 높아진다.

{
  "changed_files": ["src/search/normalize.py"],
  "change_summary": "normalize punctuation before tokenization",
  "why_this_change": "should improve matching consistency for punctuation-heavy queries",
  "verification_commands_run": [
    "bash scripts/run_tests.sh",
    "bash scripts/run_eval.sh"
  ],
  "notes": [
    "kept diff minimal",
    "did not modify forbidden files"
  ],
  "scope_respected": true,
  "forbidden_paths_touched": [],
  "estimated_risk": "low"
}

권장 추가 필드:

scope_respected
forbidden_paths_touched
estimated_risk
19. Python 오케스트레이터로 옮길 때의 장점

현재 bash 구조로도 충분히 시작 가능하지만,
실전 고도화 시 Python 오케스트레이터가 더 적합할 수 있다.

장점:

JSON 처리 쉬움
단계별 예외 처리 쉬움
Codex 결과 검증 쉬움
상태 머신 구현 쉬움
MCP 권한 정책 적용 쉬움

하지만 초기에는 bash로 시작해도 충분하다.
중요한 건 언어가 아니라 단계와 규칙이 명확한지다.

20. 최소 실전 연결 체크리스트

Codex CLI를 실제 루프에 붙이기 전 반드시 확인해야 할 것:

 prompts/implementer.md 존재
 scripts/build_implementer_input.py 동작
 scripts/run_codex_implement.sh 가 실제 환경에 맞게 수정됨
 tmp/implementer_result.json 생성 확인
 JSON schema 검증 가능
 forbidden path 검사 가능
 diff budget 검사 가능
 tests/eval 명령이 Codex 수정 후 실행 가능
 reject 시 rollback 정상 동작
 accept 시 commit 정상 동작
21. 핵심 요약

이 문서의 핵심은 아래 6개다.

Codex CLI는 implement 단계의 실제 실행 엔진이다
Codex는 바꾸기만 하고, accept/reject는 별도 계층이 한다
Implement 단계는 입력 번들 파일 기반 단발 호출이 가장 안정적이다
forbidden path와 change budget 검사가 반드시 필요하다
MCP는 filesystem/shell/git부터 최소로 붙인다
결과는 반드시 tmp/implementer_result.json 같은 구조화 파일로 남겨야 한다

즉 실전형 구조는 아래처럼 정리된다.

Planner 결과
→ Implementer Input Bundle
→ Codex CLI 실행
→ 변경 결과 JSON 생성
→ forbidden/scope/budget 검사
→ tests/eval
→ critic/controller
→ accept or rollback

이 구조가 있어야
Codex가 단순 코드 생성기가 아니라,
반복개선 루프 안에서 통제되는 구현 엔진으로 동작할 수 있다.


다음 문서는 `MCP servers.json 실제 예시 + 최소 동작 템플릿 파일 세트 + 초기 부트스트랩 절차`로 이어가는 게 가장 자연스럽다.
다음 문서 작성
# 다음 단계 문서 7
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