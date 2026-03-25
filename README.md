# AutoResearch Agent System

반복 개선형 에이전트 시스템

## 핵심 개념
- 목표를 정의한다
- 작은 변경을 수행한다
- frozen eval로 측정한다
- 좋아지면 유지한다
- 나빠지면 롤백한다
- 결과를 기억으로 축적한다

## 주요 디렉토리
- `agent/` : 목표, 규칙, 메모리, 계획, 결과 로그
- `eval/` : frozen eval 및 평가 기준
- `prompts/` : 역할별 프롬프트
- `scripts/` : 실행 스크립트
- `mcp/` : MCP 연결 및 정책
- `reports/` : iteration / final 결과 리포트

## 실행 방법
```bash
# 단일 iteration 실행
bash scripts/run_iteration.sh --iteration 1 --mode single-agent --baseline 0.0

# 여러 iteration 실행
bash scripts/run_loop.sh --max-iterations 10 --mode single-agent
```

## 중요 원칙
- `eval/frozen_eval.py` 수정 금지
- `eval/fixtures.json` 수정 금지
- 한 iteration 당 하나의 핵심 변경만 허용
- tests 실패 시 reject
- score 미개선 시 reject
