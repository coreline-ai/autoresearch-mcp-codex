from .agents import run_implementer, run_tests, run_eval, run_controller, rollback_change
from .config import OrchestratorConfig, save_baseline
from .logging import log_result, log_decision, update_memory
from .state import Phase, update_phase

class IterationRunner:
    def __init__(self, config=None):
        self.config = config or OrchestratorConfig()

    def run(self, iteration, baseline_score, hypothesis="H-001"):
        print(f"[iteration {iteration}] Starting...")
        update_phase(Phase.IMPLEMENT)
        impl = run_implementer(self.config, hypothesis)
        update_phase(Phase.RUN_TESTS)
        test = run_tests(self.config)
        update_phase(Phase.RUN_EVAL)
        eval_result = run_eval(self.config)
        update_phase(Phase.DECIDE)
        ctrl = run_controller(self.config, baseline_score, eval_result.score, test.passed)
        print(f"[iteration {iteration}] Decision: {ctrl.decision} (score: {baseline_score} → {eval_result.score})")
        if ctrl.decision == "accept":
            update_phase(Phase.ACCEPT)
            save_baseline(self.config, eval_result.score, iteration)
        else:
            update_phase(Phase.REJECT)
            rollback_change(self.config)
        update_phase(Phase.ARCHIVE)
        log_result(self.config, iteration, hypothesis, ctrl.decision, ctrl.decision_code, baseline_score, eval_result.score,
                  test.passed, impl.change_summary, "" if ctrl.decision == "accept" else "placeholder")
        log_decision(self.config, iteration, ctrl.decision, ctrl.decision_code, baseline_score, eval_result.score,
                    test.passed, impl.change_summary, "" if ctrl.decision == "accept" else "placeholder")
        update_memory(self.config, ctrl.decision_code, impl.change_summary, "" if ctrl.decision == "accept" else "placeholder")
        update_phase(Phase.DONE)
        print(f"[iteration {iteration}] Completed")
        return ctrl
