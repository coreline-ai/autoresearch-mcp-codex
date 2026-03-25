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
