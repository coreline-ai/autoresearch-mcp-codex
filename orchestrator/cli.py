#!/usr/bin/env python3
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestrator.config import OrchestratorConfig
from orchestrator.loop import LoopOrchestrator
from orchestrator.runner import IterationRunner

def cmd_single(args):
    c = OrchestratorConfig(mode=args.mode, allow_dirty=args.allow_dirty)
    r = IterationRunner(c).run(iteration=args.iteration, baseline_score=args.baseline, hypothesis=args.hypothesis)
    print(f"\nResult: {r.decision} (score: {r.score_before} → {r.score_after})")
    return 0

def cmd_loop(args):
    c = OrchestratorConfig(max_iterations=args.max_iterations, target_score=args.target_score, mode=args.mode, allow_dirty=args.allow_dirty)
    s = LoopOrchestrator(c).run()
    print(f"\nFinal: {s['status']}, score: {s.get('final_score')}, iterations: {s.get('iterations_run')}")
    return 0

def main():
    p = argparse.ArgumentParser(description="AutoResearch Orchestrator")
    p.add_argument("--mode", choices=["single-agent", "multi-agent"], default="single-agent")
    p.add_argument("--allow-dirty", action="store_true")
    sp = p.add_subparsers(dest="command")
    s = sp.add_parser("single")
    s.add_argument("--iteration", type=int, default=1)
    s.add_argument("--baseline", type=float, default=0.0)
    s.add_argument("--hypothesis", type=str, default="H-001")
    l = sp.add_parser("loop")
    l.add_argument("--max-iterations", type=int, default=10)
    l.add_argument("--target-score", type=float)
    a = p.parse_args()
    if a.command == "single": return cmd_single(a)
    elif a.command == "loop": return cmd_loop(a)
    else: p.print_help(); return 1

if __name__ == "__main__": sys.exit(main())
