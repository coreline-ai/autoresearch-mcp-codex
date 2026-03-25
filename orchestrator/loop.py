import subprocess
from pathlib import Path
from .config import OrchestratorConfig, load_baseline
from .runner import IterationRunner

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
        print(f"[loop] baseline={current}")
        streak = 0
        for i in range(1, max_iter + 1):
            print("\n" + "=" * 50 + f"\n[loop] Iteration {i}/{max_iter}\n" + "=" * 50)
            try:
                ctrl = self.runner.run(iteration=i, baseline_score=current)
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
            if target and current >= target:
                print(f"[loop] Target reached: {current} >= {target}")
                break
            if streak >= self.config.max_no_improvement_streak:
                print(f"[loop] No improvement for {self.config.max_no_improvement_streak} iterations. Stopping.")
                break
        print(f"[loop] Final baseline: {current}")
        return {"status": "completed", "final_score": current, "iterations_run": i}
