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
- tests와 constraints를 함께 만족해야 최종 accept 가능.
