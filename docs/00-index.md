# AutoResearch Agent System - Documentation Index

**Source:** `ref.md` (split into sections for better navigation)

---

## Overview

This documentation describes a comprehensive multi-agent system that combines:

- **Karpathy-style exploration**: Open-ended hypothesis generation and research
- **autoresearch methodology**: Iterative improvement with frozen evaluation
- **Codex CLI**: Actual code/document/configuration modification execution
- **MCP (Model Context Protocol)**: External tool integration layer

The system is designed to automatically improve project quality through iterative experimentation, hypothesis testing, and rollback mechanisms.

---

## Document Sections

### [01. Single Agent Design](./01-single-agent-design.md)
**Lines 1-380 | ~8.8KB**

A pragmatic approach to building a single autonomous agent system. Covers:
- Goal definition and agent roles
- Codex CLI as the primary execution engine
- MCP as tool connection layer (not an agent)
- autoresearch as an operational loop
- Minimal folder structure
- File-by-file role definitions (TASK.md, RULES.md, MEMORY.md, RESULTS.tsv)
- Practical iteration loop with evaluation and rollback
- Safety mechanisms and failure patterns

**Best for:** Understanding the foundational single-agent architecture before scaling to multi-agent.

---

### [02. Multi-Agent Architecture](./02-multi-agent-architecture.md)
**Lines 382-1316 | ~20.9KB**

Complete production-ready multi-agent system design. Covers:
- Why combine Karpathy-style exploration with autoresearch optimization
- System objectives and suitable task types
- Full architecture overview with 6 specialized agents:
  - **Controller Agent**: Orchestrates the entire loop
  - **Explorer Agent**: Generates hypotheses (Karpathy-style)
  - **Planner Agent**: Breaks down experiments into testable units
  - **Implementer Agent**: Applies actual changes via Codex CLI
  - **Evaluator Agent**: Runs frozen eval and tests
  - **Critic Agent**: Analyzes failures and prevents fake improvements
  - **Archivist Agent**: Maintains memory and logs
- Codex CLI positioning (runtime vs agents)
- MCP integration strategy
- Directory structure and file descriptions
- Execution loop and iteration design principles
- Evaluation system and rollback strategies
- Memory structure and operational modes
- Common failure patterns and recommended balances

**Best for:** Understanding the complete multi-agent system architecture.

---

### [03. PRD (Product Requirements Document)](./03-PRD.md)
**Lines 1317-1897 | ~14.3KB**

Product requirements from a business/user perspective. Covers:
- Product vision and objectives
- Problem definition (why existing AI coding tools fall short)
- Target users (primary and secondary)
- Product scope (in-scope and out-of-scope)
- Core usage scenarios (search relevance, test pass rate, RAG quality)
- User flows (initialization, iterative improvement, termination)
- Product principles (frozen eval first, small changes, fail cheap)
- Functional requirements (11 major features)
- Non-functional requirements (reliability, reproducibility, traceability)
- Success metrics and MVP definition
- Release phases and constraints
- Risks and open issues

**Best for:** Understanding what problem this system solves and how success is measured.

---

### [04. TRD (Technical Requirements Document)](./04-TRD.md)
**Lines 1898-2883 | ~19.0KB**

Technical requirements and system design. Covers:
- System overview and architecture
- State machine design
- Component responsibilities
- Data models (state, hypotheses, decisions, eval results)
- Tool policies (MCP usage rules)
- Accepted/rejected patterns
- Constraints and reminders

**Best for:** Understanding the technical specification and design decisions.

---

### [05. Folder Structure Templates](./05-folder-structure-templates.md)
**Lines 2884-3637 | ~18.5KB**

Actual file templates for the project structure. Includes:
- Recommended folder structure
- README.md template
- PRODUCT_GOAL.md template
- CURRENT_TASK.md template
- OPERATING_RULES.md template
- MEMORY.md template
- HYPOTHESES.md template
- PLAN.md template
- DECISIONS.md template
- EVAL_RUBRIC.md template
- TOOL_POLICIES.md template

**Best for:** Getting started with actual file creation and project setup.

---

### [06. Prompts Detail](./06-prompts-detail.md)
**Lines 3638-3983 | ~8.1KB**

Detailed prompt specifications for each agent. Covers:
- Purpose of prompt design
- `prompts/controller.md` - Iteration control and accept/reject decisions
- `prompts/explorer.md` - Hypothesis generation
- `prompts/planner.md` - Experiment planning and task breakdown
- `prompts/implementer.md` - Actual modification execution
- `prompts/evaluator.md` - Frozen eval and testing
- `prompts/critic.md` - Failure analysis and regression prevention
- `prompts/archivist.md` - Memory and log management

**Best for:** Understanding how to prompt each agent effectively.

---

### [07. Shell Scripts](./07-shell-scripts.md)
**Lines 3984-4556 | ~12.2KB**

Shell script implementations for the orchestration layer. Includes:
- `run_loop.sh` - Main loop controller
- `run_iteration.sh` - Single iteration execution
- `run_eval.sh` - Evaluation runner
- `accept_change.sh` - Accept and commit improvements
- `rollback_change.sh` - Rollback failed experiments
- `update_memory.py` - Memory file updates
- `summarize_results.py` - Results aggregation

**Best for:** Understanding the bash-based orchestration implementation.

---

### [08. Decision Engine](./08-decision-engine.md)
**Lines 4557-5195 | ~14.7KB**

Accept/reject/rollback decision logic specification. Covers:
- Decision engine role and responsibilities
- Input data (test results, scores, constraints)
- Decision priority (tests > constraints > score > critic > scope)
- Decision matrix
- Accept conditions (mandatory and optional)
- Reject conditions (technical, quality, operational)
- Hold conditions and handling
- Rollback conditions and exceptions
- Baseline update rules
- Fake improvement prevention
- Pseudocode for automated decision-making

**Best for:** Understanding how the system decides whether to keep or discard changes.

---

### [09. Results & Memory Specifications](./09-results-memory-specs.md)
**Lines 5196-5665 | ~10.9KB**

Recording layer specifications. Covers:
- Role of recording (history, memory, visibility, summary)
- Design principles (append-first, concise-memory, decision-traceable)
- `RESULTS.tsv` format specification
- `MEMORY.md` update rules
- `DECISIONS.md` format
- Final report generation format

**Best for:** Understanding how experimental results are tracked and summarized.

---

### [10. Codex CLI & MCP Integration](./10-codex-mcp-integration.md)
**Lines 5666-7537 | ~46.2KB**

Detailed integration guide for Codex CLI and MCP. Covers:
- Core principles (Codex as implementation engine, not judge)
- Implement phase scope constraints
- MCP minimal tool approach
- Codex CLI positioning in the architecture
- Implementer input/output format
- Implementer prompt template
- MCP tool policies (default allowed, restricted, forbidden)
- Example configurations

**Best for:** Understanding how to integrate Codex CLI and MCP tools practically.

---

### [11. Python Orchestrator](./11-python-orchestrator.md)
**Lines 7538-12399 | ~134KB**

Complete Python-based orchestration design. Covers:
- Why move from bash to Python (JSON handling, state machine, testability)
- Service separation design:
  - `IterationService` - Main iteration orchestration
  - `ReportingService` - Report generation
  - `MemoryService` - Memory management
  - `ChangeGuardService` - Change validation
  - `PlannerService` - Experiment planning
  - `CriticService` - Failure analysis
  - `BaselineService` - Baseline management
- State machine implementation
- End-to-end Python code skeleton
- Service class drafts

**Best for:** Understanding the production Python implementation.

---

## Reading Path Recommendations

### For Quick Understanding
1. Start with **[01. Single Agent Design](./01-single-agent-design.md)** for the basics
2. Read **[02. Multi-Agent Architecture](./02-multi-agent-architecture.md)** for the full picture
3. Review **[03. PRD](./03-PRD.md)** for product context

### For Implementation
1. **[05. Folder Structure Templates](./05-folder-structure-templates.md)** - Set up files
2. **[06. Prompts Detail](./06-prompts-detail.md)** - Configure agents
3. **[07. Shell Scripts](./07-shell-scripts.md)** or **[11. Python Orchestrator](./11-python-orchestrator.md)** - Choose implementation approach
4. **[08. Decision Engine](./08-decision-engine.md)** - Implement decision logic
5. **[09. Results & Memory Specs](./09-results-memory-specs.md)** - Set up tracking
6. **[10. Codex CLI & MCP Integration](./10-codex-mcp-integration.md)** - Connect tools

### For Architecture Understanding
1. **[02. Multi-Agent Architecture](./02-multi-agent-architecture.md)** - Full architecture
2. **[04. TRD](./04-TRD.md)** - Technical specification
3. **[11. Python Orchestrator](./11-python-orchestrator.md)** - Service design

---

## File Statistics

| File | Lines | Size | Description |
|------|-------|------|-------------|
| 01-single-agent-design.md | 380 | 8.8KB | Single agent foundations |
| 02-multi-agent-architecture.md | 935 | 20.9KB | Complete multi-agent design |
| 03-PRD.md | 581 | 14.3KB | Product requirements |
| 04-TRD.md | 986 | 19.0KB | Technical requirements |
| 05-folder-structure-templates.md | 754 | 18.5KB | File templates |
| 06-prompts-detail.md | 346 | 8.1KB | Prompt specifications |
| 07-shell-scripts.md | 573 | 12.2KB | Shell implementation |
| 08-decision-engine.md | 639 | 14.7KB | Decision logic |
| 09-results-memory-specs.md | 470 | 10.9KB | Recording specs |
| 10-codex-mcp-integration.md | 1,872 | 46.2KB | Codex & MCP guide |
| 11-python-orchestrator.md | 4,862 | 134KB | Python implementation |
| **Total** | **11,398** | **307.6KB** | Complete documentation |

---

## Original Document

The original unified document is available at:
- **[ref.md](./ref.md)** - Complete unified reference (12,399 lines, ~300KB)

---

*This index was automatically generated from the ref.md document split.*
