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
