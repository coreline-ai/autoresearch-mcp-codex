# AutoResearch Agent System

자율 프로젝트 개선 시스템 - 목표를 정의하면 시스템이 스스로 반복 실험을 통해 결과를 개선합니다.

## 핵심 개념

1. **목표 정의** - PRODUCT_GOAL.md에 최상위 목표 설정
2. **작은 변경** - 한 iteration당 하나의 핵심 변경만 수행
3. **Frozen Eval** - 고정된 평가 기준으로 일관되게 측정
4. **자동 판단** - 좋아지면 유지, 나빠지면 롤백
5. **기계학습** - MEMORY.md에 패턴을 축적

## 주요 디렉토리

| 디렉토리 | 설명 |
|---------|------|
| `agent/` | 목표, 규칙, 메모리, 계획, 결과 로그 |
| `eval/` | frozen eval 및 평가 기준 |
| `prompts/` | 역할별 프롬프트 (Controller, Explorer, Planner, etc.) |
| `scripts/` | Shell 실행 스크립트 |
| `orchestrator/` | Python 오케스트레이터 (권장) |
| `mcp/` | MCP 연결 및 정책 |
| `reports/` | iteration / final 결과 리포트 |

## 실행 방법

### Python 오케스트레이터 (권장)

```bash
# 단일 iteration 실행
python3 orchestrator/cli.py single --iteration 1 --baseline 0.5

# 여러 iteration 실행 (최대 10회)
python3 orchestrator/cli.py --allow-dirty loop --max-iterations 10

# 목표 점수 도달 시 중단
python3 orchestrator/cli.py --allow-dirty loop --max-iterations 100 --target-score 0.95

# 멀티 에이전트 모드 (준비 중)
python3 orchestrator/cli.py --mode multi-agent loop --max-iterations 10
```

### Shell 스크립트 (호환용)

```bash
# 단일 iteration 실행
bash scripts/run_iteration.sh --iteration 1 --mode single-agent --baseline 0.0

# 여러 iteration 실행
bash scripts/run_loop.sh --max-iterations 10 --allow-dirty true
```

## CLI 옵션

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--mode` | `single-agent` 또는 `multi-agent` | `single-agent` |
| `--allow-dirty` | Git dirty 상태 허용 | `false` |
| `--max-iterations` | 최대 iteration 수 | `10` |
| `--target-score` | 목표 점수 (도달 시 종료) | 없음 |

## 중요 원칙

### 절대 규칙
- `eval/frozen_eval.py` 수정 금지
- `eval/fixtures.json` 수정 금지
- 한 iteration 당 하나의 핵심 변경만 허용

### 판단 기준
- Tests 실패 시 → **REJECT**
- Score 미개선 시 → **REJECT**
- Score 개선 시 → **ACCEPT**

### 종료 조건
- 목표 점수 도달
- N회 연속 미개선 (기본 3회)
- 최대 iteration 도달

## 결과 확인

```bash
# iteration 결과
cat agent/RESULTS.tsv

# 결정 로그
cat agent/DECISIONS.md

# 현재 상태
cat agent/ITERATION_STATE.json

# 누적 학습
cat agent/MEMORY.md
```

## 예제

### 검색 relevance 개선 예제

```bash
# 1. 초기 baseline 설정
echo '{"score": 0.5, "measured_at": "2026-03-25T00:00:00Z", "iteration": 0}' > eval/baseline.json

# 2. 10회 iteration 실행
python3 orchestrator/cli.py --allow-dirty loop --max-iterations 10

# 3. 결과 확인
echo "Final score:"
python3 -c "import json; print(json.load(open('eval/baseline.json'))['score'])"
```

## 개발

### 테스트 실행

```bash
# 단위 테스트
pytest tests/ -v

# 커버리지
pytest tests/ --cov=eval --cov=orchestrator --cov-report=term-missing
```

### 구조

```
autoresearch-agent/
├── orchestrator/
│   ├── __init__.py
│   ├── state.py        # IterationState, Phase enum
│   ├── config.py       # OrchestratorConfig
│   ├── agents.py       # Agent execution phases
│   ├── logging.py      # Results logging
│   ├── runner.py       # IterationRunner
│   ├── loop.py         # LoopOrchestrator
│   └── cli.py          # CLI entry point
├── agent/              # State files
├── eval/               # Frozen evaluation
├── prompts/            # Agent prompts
├── scripts/            # Shell scripts
├── tests/              # Unit tests
└── mcp/                # MCP configuration
```

## 라이선스

MIT License
