# Changelog

All notable changes to the AutoResearch Agent System will be documented in this file.

## [0.1.0] - 2026-03-25

### Added
- **Phase 0-8**: MVP 기능 완성
  - 프로젝트 구조 및 Git 저장소
  - Agent 템플릿 (PRODUCT_GOAL, TASK, RULES, MEMORY, etc.)
  - Frozen eval 시스템 (eval/frozen_eval.py)
  - Agent 역할별 프롬프트 (7개 역할)
  - Shell 스크립트 오케스트레이션
  - 단일/다중 iteration 실행
  - Rollback 기능
  - 결과 로깅 (RESULTS.tsv, DECISIONS.md)

- **Phase 9**: Python 오케스트레이터
  - `orchestrator/state.py` - IterationState, Phase enum
  - `orchestrator/config.py` - OrchestratorConfig dataclass
  - `orchestrator/agents.py` - Agent execution phases
  - `orchestrator/logging.py` - Results logging
  - `orchestrator/runner.py` - IterationRunner
  - `orchestrator/loop.py` - LoopOrchestrator
  - `orchestrator/cli.py` - CLI entry point

### Features
- Single iteration execution
- Multi-iteration loop with stopping conditions
- Automatic rollback on rejected changes
- Frozen evaluation (immutable criteria)
- Memory accumulation (accepted/rejected patterns)
- Stagnation detection (stops after N no-improvement iterations)
- Target score early termination

### Usage
```bash
# Run single iteration
python3 orchestrator/cli.py single --iteration 1 --baseline 0.5

# Run multi-iteration loop
python3 orchestrator/cli.py --allow-dirty loop --max-iterations 10

# Run with target score
python3 orchestrator/cli.py --allow-dirty loop --max-iterations 100 --target-score 0.95
```

### Testing
- 7 unit tests (frozen_eval)
- E2E test passed (10 iterations)
- Rollback test passed

### Documentation
- README.md with usage guide
- IMPLEMENTATION_PLAN.md with 76 tasks
- Agent prompts for 6 roles

## [Unreleased]

### Planned
- Multi-agent parallel execution
- Codex CLI integration
- Coverage > 80%
- API documentation
