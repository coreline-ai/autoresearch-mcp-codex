# MCP Tool Policies

## Default Allowed
- filesystem read/write inside workspace
- shell commands for tests, eval, lint, build
- git status, diff, restore, add, commit

## Restricted
- file deletion
- multi-file rename
- dependency install/update
- schema change
- browser automation
- database access

## Forbidden
- editing eval/frozen_eval.py during optimization
- editing eval/fixtures.json during optimization
- editing eval/baseline.json from implementer
- directly editing agent/RESULTS.tsv
- directly editing agent/DECISIONS.md
- destructive shell commands
- force push
- history rewrite
- production mutations
