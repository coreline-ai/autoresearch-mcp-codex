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
