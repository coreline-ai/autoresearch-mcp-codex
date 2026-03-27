#!/usr/bin/env python3
"""CLI entry point for AutoResearch Orchestrator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.config import OrchestratorConfig
from orchestrator.loop import LoopOrchestrator
from orchestrator.runner import IterationRunner


def _make_config(args) -> OrchestratorConfig:
    """Build OrchestratorConfig from parsed CLI arguments."""
    kwargs = dict(
        mode=args.mode,
        allow_dirty=args.allow_dirty,
        llm_provider=args.provider,
    )
    if hasattr(args, "max_iterations"):
        kwargs["max_iterations"] = args.max_iterations
    if hasattr(args, "target_score") and args.target_score is not None:
        kwargs["target_score"] = args.target_score
    return OrchestratorConfig(**kwargs)


def cmd_single(args) -> int:
    c = _make_config(args)
    r = IterationRunner(c).run(
        iteration=args.iteration,
        baseline_score=args.baseline,
        hypothesis=args.hypothesis,
    )
    print(f"\nResult: {r.decision} ({r.decision_code}) score: {r.score_before} -> {r.score_after}")
    return 0


def cmd_loop(args) -> int:
    c = _make_config(args)
    s = LoopOrchestrator(c).run()
    print(f"\nFinal: {s['status']}, score: {s.get('final_score')}, iterations: {s.get('iterations_run')}")
    return 0


def cmd_auth(args) -> int:
    """Check authentication status for the configured LLM provider."""
    from orchestrator.agents import check_llm_auth
    result = check_llm_auth(args.provider)
    status = "OK" if result["authenticated"] else "FAIL"
    print(f"[{result['provider']}] {status}: {result['message']}")
    return 0 if result["authenticated"] else 1


def main() -> int:
    p = argparse.ArgumentParser(description="AutoResearch Orchestrator")
    p.add_argument("--mode", choices=["single-agent", "multi-agent"], default="single-agent")
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--provider", choices=["claude", "codex"], default="claude",
                    help="LLM provider: claude (Claude Code CLI) or codex (OpenAI Codex CLI)")
    sp = p.add_subparsers(dest="command")

    s = sp.add_parser("single", help="Run a single iteration")
    s.add_argument("--iteration", type=int, default=1)
    s.add_argument("--baseline", type=float, default=0.0)
    s.add_argument("--hypothesis", type=str, default="H-001")

    lp = sp.add_parser("loop", help="Run iterative loop")
    lp.add_argument("--max-iterations", type=int, default=10)
    lp.add_argument("--target-score", type=float)

    sp.add_parser("auth", help="Check LLM provider authentication status")

    a = p.parse_args()
    if a.command == "single":
        return cmd_single(a)
    elif a.command == "loop":
        return cmd_loop(a)
    elif a.command == "auth":
        return cmd_auth(a)
    else:
        p.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
