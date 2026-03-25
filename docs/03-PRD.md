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
