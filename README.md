<p align="center">
  <h1 align="center">🔬 AutoResearch MCP</h1>
  <p align="center">
    <strong>Frozen Evaluation 기반 자율 반복 개선 에이전트 시스템</strong>
  </p>
  <p align="center">
    <a href="#quickstart">Quickstart</a> · <a href="#architecture">Architecture</a> · <a href="#how-it-works">How it Works</a> · <a href="#cli-reference">CLI Reference</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/tests-81%20passed-brightgreen?logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/E2E-34%20passed-brightgreen" alt="E2E">
  <img src="https://img.shields.io/badge/Claude%20CLI-OAuth-blueviolet?logo=anthropic" alt="Claude CLI">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

---

## 📌 What is this?

목표를 정의하면 **LLM이 스스로 코드를 수정하고**, frozen evaluation으로 측정하고, 좋아지면 유지/나빠지면 롤백하는 **자율 개선 루프**입니다.

```
┌─────────────────────────────────────────────────────┐
│  🎯 Goal: "검색 relevance 개선"                      │
│                                                     │
│  Iteration 1: H-002 선택 → Claude가 코드 수정       │
│               → 테스트 통과 → score 0.5→1.0         │
│               → ✅ ACCEPT → baseline 갱신            │
│                                                     │
│  Iteration 2: H-003 선택 → Claude가 코드 수정       │
│               → 테스트 실패 → ❌ REJECT → rollback   │
│                                                     │
│  ... 목표 달성 또는 가설 소진까지 반복               │
└─────────────────────────────────────────────────────┘
```

> **API key 불필요** — Claude Code CLI 또는 OpenAI Codex CLI의 OAuth 로그인으로 동작합니다.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **LLM 코드 수정** | Claude Code CLI가 실제로 파일을 수정 (`--dangerously-skip-permissions`) |
| 🧊 **Frozen Eval** | 평가 기준이 iteration 중 절대 변하지 않음 — 공정한 측정 보장 |
| 🔄 **자동 Accept/Reject** | 10단계 Decision Engine이 점수/테스트/제약 위반을 종합 판단 |
| ⏪ **자동 Rollback** | reject 시 `git restore`로 원상복구 (agent 상태는 보존) |
| 🧬 **가설 생명주기** | selected → tried → accepted/rejected — 같은 가설 무한 반복 방지 |
| 📊 **완전한 관측성** | RESULTS.tsv, DECISIONS.md, MEMORY.md, ITERATION_STATE.json |
| 🔒 **안전성 검사** | forbidden path, scope violation, change budget 자동 차단 |
| 🏗️ **제약 조건 파이프라인** | latency budget, regression detection, score sanity check |

---

## 🚀 Quickstart

### 1. Prerequisites

```bash
# Python 3.11+
uv venv .venv --python 3.12
uv pip install pytest

# Claude Code CLI (OAuth — API key 불필요)
npm install -g @anthropic-ai/claude-code
claude auth login    # 브라우저에서 Claude 계정 로그인

# 또는 OpenAI Codex CLI
npm install -g @openai/codex
codex login          # 브라우저에서 ChatGPT 계정 로그인
```

### 2. Authentication Check

```bash
python orchestrator/cli.py --provider claude auth
# [claude] OK: Claude OAuth credentials found

python orchestrator/cli.py --provider codex auth
# [codex] OK: Codex OAuth credentials found
```

### 3. Run

```bash
# 단일 iteration
python orchestrator/cli.py single --iteration 1 --baseline 0.5

# 반복 루프 (최대 10회, stagnation 시 조기 종료)
python orchestrator/cli.py --allow-dirty loop --max-iterations 10

# 목표 점수 도달 시 중단
python orchestrator/cli.py --allow-dirty loop --max-iterations 50 --target-score 0.95

# Codex CLI 사용
python orchestrator/cli.py --provider codex --allow-dirty loop --max-iterations 5
```

---

## 🏗️ Architecture

```
autoresearch-mcp/
├── 🧠 orchestrator/          # Python 오케스트레이터 (정본 실행 경로)
│   ├── cli.py                # CLI 진입점 (single / loop / auth)
│   ├── runner.py             # 12-Phase IterationRunner
│   ├── loop.py               # LoopOrchestrator (stagnation, target)
│   ├── agents.py             # 7개 Agent 함수 + Claude/Codex CLI 연동
│   ├── state.py              # 16 Phase, 11 DecisionCode, IterationState
│   ├── config.py             # OrchestratorConfig (provider, paths, limits)
│   └── logging.py            # RESULTS.tsv, DECISIONS.md, MEMORY.md
│
├── 📦 src/                    # 제품 코드 (LLM이 수정하는 대상)
│   └── query_processor.py    # normalize_query() — 개선 타겟
│
├── 🧊 eval/                   # Frozen Evaluation (절대 수정 금지)
│   ├── frozen_eval.py        # 고정 평가 스크립트
│   ├── fixtures.json         # 고정 테스트 입력 (3개 쿼리)
│   ├── baseline.json         # 현재 baseline 점수
│   ├── constraints.py        # latency/regression 제약 체크
│   └── rubric.md             # 점수 기준 설명
│
├── 📋 agent/                  # 에이전트 상태 파일
│   ├── PRODUCT_GOAL.md       # 최상위 목표
│   ├── TASK.md               # 현재 cycle 목표
│   ├── RULES.md              # 운영 규칙
│   ├── HYPOTHESES.md         # 가설 레지스트리 (생명주기 관리)
│   ├── PLAN.md               # 현재 실행 계획
│   ├── MEMORY.md             # 누적 학습 (accepted/rejected 패턴)
│   ├── ITERATION_STATE.json  # 현재 phase 상태
│   ├── RESULTS.tsv           # 전체 iteration 결과 로그
│   └── DECISIONS.md          # 결정 히스토리
│
├── 📝 prompts/                # 에이전트 프롬프트
│   ├── implementer.md        # ✅ Claude CLI에 전달됨
│   ├── explorer.md           # 📌 향후 LLM 연결 예정
│   ├── planner.md            # 📌 향후 LLM 연결 예정
│   ├── critic.md             # 📌 향후 LLM 연결 예정
│   ├── controller.md         # 규칙 기반으로 충분
│   └── archivist.md          # 규칙 기반으로 충분
│
├── 🧪 tests/                  # 테스트 (81개)
│   ├── test_frozen_eval.py   # Frozen eval 검증
│   ├── test_orchestrator.py  # 오케스트레이터 전체 검증
│   └── test_query_processor.py # 제품 코드 엣지케이스
│
├── 🔧 scripts/                # Shell 스크립트 (비정본, 호환용)
├── 📊 demo_test/              # E2E 검증 스크립트 (34 checks)
├── 📖 docs/                   # 설계 문서 (11개, 307KB)
└── ⚙️ mcp/                    # MCP 서버 설정
```

---

## ⚙️ How it Works

### 12-Phase Iteration Pipeline

```
INIT → READ_CONTEXT → EXPLORE → PLAN → IMPLEMENT → RUN_TESTS
  → RUN_EVAL → CRITIQUE → DECIDE → ACCEPT/REJECT → ARCHIVE → DONE
```

| Phase | Agent | Action |
|-------|-------|--------|
| `INIT` | — | IterationState 초기화 |
| `READ_CONTEXT` | — | agent/*.md 파일 로딩 |
| `EXPLORE` | Explorer | HYPOTHESES.md에서 actionable 가설 선택 |
| `PLAN` | Planner | PLAN.md에서 change scope/tests 파싱 |
| `IMPLEMENT` | Implementer | **Claude CLI로 실제 코드 수정** |
| `RUN_TESTS` | — | `pytest tests/ -v` 실행 |
| `RUN_EVAL` | — | `frozen_eval.py` + `constraints.py` 실행 |
| `CRITIQUE` | Critic | 8가지 규칙 기반 검토 (narrow win, scope, latency 등) |
| `DECIDE` | Controller | **10단계 Decision Engine** |
| `ACCEPT/REJECT` | — | baseline 갱신 or git rollback |
| `ARCHIVE` | Archivist | RESULTS.tsv, DECISIONS.md, MEMORY.md 기록 |
| `DONE` | — | 가설 상태 갱신 (accepted/rejected/tried) |

### 10-Level Decision Engine

```
Level 0: NO_CODE_CHANGE    → 실제 파일 변경 없음 (placeholder)
Level 1: TEST_FAIL         → 테스트 실패
Level 2: CONSTRAINT_FAIL   → latency/regression 제약 위반
Level 3: FORBIDDEN_FILE    → eval/frozen_eval.py 등 수정 시도
Level 4: SCOPE_VIOLATION   → plan scope 밖 파일 수정
Level 5: CRITIC_BLOCK      → critic severity=high
Level 6: SCORE_REGRESSION  → 점수 하락
Level 7: NO_IMPROVEMENT    → 점수 동일
Level 8: ACCEPT            → 모든 검증 통과 + 점수 개선
```

### Hypothesis Lifecycle

```
proposed → selected → (iteration) → accepted ✅
                                   → rejected ❌
                                   → tried (NO_CODE_CHANGE 2회 연속)
parked → (수동 활성화 필요)
```

---

## 📋 CLI Reference

```bash
python orchestrator/cli.py [OPTIONS] COMMAND [ARGS]
```

### Global Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--provider` | `claude`, `codex` | `claude` | LLM provider (OAuth 기반) |
| `--mode` | `single-agent` | `single-agent` | 실행 모드 |
| `--allow-dirty` | flag | `false` | git dirty 상태 허용 |

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `single` | 단일 iteration 실행 | `cli.py single --iteration 1 --baseline 0.5` |
| `loop` | 반복 루프 실행 | `cli.py loop --max-iterations 10 --target-score 0.9` |
| `auth` | LLM 인증 상태 확인 | `cli.py --provider claude auth` |

### Single Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--iteration` | int | `1` | Iteration 번호 |
| `--baseline` | float | `0.0` | Baseline 점수 |
| `--hypothesis` | str | `H-001` | 시작 가설 |

### Loop Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max-iterations` | int | `10` | 최대 반복 횟수 |
| `--target-score` | float | — | 목표 점수 (도달 시 조기 종료) |

---

## 🔐 LLM Authentication

API key가 **필요 없습니다**. OAuth 로그인으로 동작합니다.

### Claude Code CLI

```bash
# 설치
npm install -g @anthropic-ai/claude-code

# OAuth 로그인 (브라우저에서 Claude 계정)
claude auth login

# 인증 확인
python orchestrator/cli.py --provider claude auth
```

> 토큰은 `~/.claude/.credentials.json`에 저장됩니다 (1년 유효).

### OpenAI Codex CLI

```bash
# 설치
npm install -g @openai/codex

# OAuth 로그인 (브라우저에서 ChatGPT 계정)
codex login

# 인증 확인
python orchestrator/cli.py --provider codex auth
```

> 토큰은 `~/.codex/auth.json`에 저장됩니다 (자동 갱신).

---

## 🧪 Testing

```bash
# Unit tests (81개)
uv run pytest tests/ -v

# E2E pipeline test (34 checks)
uv run python demo_test/run_e2e_test.py

# 실제 Claude CLI accept 경로 검증 (OAuth 필요)
# → src/query_processor.py를 Claude가 수정 → score 0.5→1.0 → ACCEPT
python orchestrator/cli.py --allow-dirty single --iteration 1 --baseline 0.5
```

### Test Coverage

| Test Suite | Count | Covers |
|-----------|-------|--------|
| `test_frozen_eval.py` | 9 | frozen eval scoring, fixture correctness |
| `test_query_processor.py` | 13 | normalize_query edge cases |
| `test_orchestrator.py` | 52 | state, decision engine, critic, explorer, planner, logging, runner, loop |
| `demo_test/run_e2e_test.py` | 34 | full pipeline (reject + stagnation + constraints) |

---

## 📊 Observability

### Iteration Results

```bash
# 전체 결과 로그 (TSV, 15 columns)
cat agent/RESULTS.tsv

# 결정 히스토리
cat agent/DECISIONS.md

# 현재 상태
cat agent/ITERATION_STATE.json

# 누적 학습
cat agent/MEMORY.md

# 가설 상태
cat agent/HYPOTHESES.md

# Final report 생성
python scripts/make_final_report.py
```

### ITERATION_STATE.json Example

```json
{
  "iteration": 1,
  "phase": "done",
  "selected_hypothesis": "H-002",
  "tests_pass": true,
  "candidate_score": 1.0,
  "decision": "accept"
}
```

---

## 📐 Rules & Safety

### Absolute Rules

| Rule | Enforced by |
|------|-------------|
| 🚫 `eval/frozen_eval.py` 수정 금지 | FORBIDDEN_FILE (Level 3) |
| 🚫 `eval/fixtures.json` 수정 금지 | FORBIDDEN_FILE (Level 3) |
| 🚫 `eval/baseline.json` 직접 수정 금지 | FORBIDDEN_FILE (Level 3) |
| 📏 1 iteration = 1 core change | Critic + change budget |
| ⏱️ Latency 증가 5% 이하 | CONSTRAINT_FAIL (Level 2) |

### Termination Conditions

| Condition | Default |
|-----------|---------|
| 목표 점수 도달 | `--target-score` |
| N회 연속 미개선 | 3회 |
| 최대 iteration 도달 | `--max-iterations` |
| 모든 가설 소진 | 자동 감지 |

---

## 🗺️ Roadmap

- [x] Single-agent pipeline
- [x] Claude Code CLI integration (OAuth)
- [x] Codex CLI support
- [x] 10-level Decision Engine
- [x] Hypothesis lifecycle management
- [x] Constraints pipeline (latency, regressions)
- [x] Windows compatibility (cp949 fix)
- [ ] Explorer LLM 연결 (동적 가설 생성)
- [ ] Planner LLM 연결 (가설별 동적 계획)
- [ ] Critic LLM 연결 (LLM 기반 회귀 분석)
- [ ] Multi-agent parallel execution

---

## 📄 License

MIT License

---

<p align="center">
  Built with 🔬 <a href="https://github.com/coreline-ai/autoresearch-mcp-codex">AutoResearch MCP</a>
</p>
