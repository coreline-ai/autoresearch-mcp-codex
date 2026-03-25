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
