import subprocess
from pathlib import Path
from .config import OrchestratorConfig, load_baseline
from .runner import IterationRunner


def _get_last_iteration(config: OrchestratorConfig) -> int:
    """Read the last iteration number from RESULTS.tsv. Returns 0 if empty."""
    if not config.results_path.exists():
        return 0
    lines = config.results_path.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) <= 1:  # header only
        return 0
    try:
        return int(lines[-1].split("\t")[0])
    except (ValueError, IndexError):
        return 0


class LoopOrchestrator:
    def __init__(self, config=None):
        self.config = config or OrchestratorConfig()
        self.runner = IterationRunner(self.config)

    def run(self, max_iterations=None, target_score=None):
        max_iter = max_iterations or self.config.max_iterations
        target = target_score or self.config.target_score
        self.config.tmp_path.mkdir(parents=True, exist_ok=True)
        (self.config.reports_path / "final").mkdir(parents=True, exist_ok=True)
        print(f"[loop] mode={self.config.mode} max_iterations={max_iter}")
        if not self.config.allow_dirty:
            r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=Path.cwd())
            if r.stdout.strip():
                print("[loop] Working tree is dirty. Commit or stash first.")
                return {"status": "aborted", "reason": "dirty_tree"}
        current = load_baseline(self.config)["score"]
        start_iter = _get_last_iteration(self.config) + 1
        print(f"[loop] baseline={current} start_iteration={start_iter}")
        streak = 0
        iterations_run = 0
        for i in range(start_iter, start_iter + max_iter):
            iterations_run = i - start_iter + 1
            print("\n" + "=" * 50 + f"\n[loop] Iteration {i}/{max_iter}\n" + "=" * 50)
            try:
                ctrl = self.runner.run(iteration=i, baseline_score=current)
            except StopIteration:
                print("[loop] All hypotheses exhausted. Stopping.")
                break
            except Exception as e:
                print(f"[loop] Failed: {e}")
                break
            new = load_baseline(self.config)["score"]
            print(f"[loop] decision={ctrl.decision} baseline_now={new}")
            if new > current:
                streak = 0
            else:
                streak += 1
                print(f"[loop] No improvement (streak: {streak}/{self.config.max_no_improvement_streak})")
            current = new
            if target is not None and current >= target:
                print(f"[loop] Target reached: {current} >= {target}")
                break
            if streak >= self.config.max_no_improvement_streak:
                print(f"[loop] No improvement for {self.config.max_no_improvement_streak} iterations. Stopping.")
                break
        print(f"[loop] Final baseline: {current}")
        return {"status": "completed", "final_score": current, "iterations_run": iterations_run}
