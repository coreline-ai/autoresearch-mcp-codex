# PLAN

## Selected Hypothesis
H-001: normalize punctuation in queries

## Change Scope
- src/query_processor.py
- tests/test_query_processor.py

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
