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
