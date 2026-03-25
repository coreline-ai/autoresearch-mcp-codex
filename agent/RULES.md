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
