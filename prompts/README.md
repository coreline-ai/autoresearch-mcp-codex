# Prompts Directory

This directory contains role-specific prompts for the AutoResearch Agent System.

## Prompt Files

| File | Role | Purpose |
|------|------|---------|
| controller.md | Controller | Iteration governance and accept/reject decisions |
| explorer.md | Explorer | Hypothesis generation and exploration |
| planner.md | Planner | Experiment planning and task breakdown |
| implementer.md | Implementer | Actual code/document modification |
| critic.md | Critic | Failure analysis and regression prevention |
| archivist.md | Archivist | Memory and log management |

## Usage

Each prompt is used by the corresponding agent role during the iteration loop.

## Key Design Principles

1. **Single Responsibility**: Each prompt defines one clear role
2. **Structured Output**: All prompts specify JSON output format
3. **Constraint Awareness**: All prompts reference RULES.md
4. **Evidence-Based**: Decisions must be based on tests and eval results
