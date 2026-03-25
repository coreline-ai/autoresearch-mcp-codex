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
