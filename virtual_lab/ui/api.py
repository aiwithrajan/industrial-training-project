from __future__ import annotations

from pathlib import Path

from virtual_lab.adversarial import adversarial_search, random_search, summarize_search
from virtual_lab.backends import status
from virtual_lab.bayesopt import bayesian_optimize
from virtual_lab.mcmc import mcmc_search
from virtual_lab.models import Scenario
from virtual_lab.simulator import simulate


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def scenario_dir() -> Path:
    return repo_root() / "scenarios"


def list_scenarios() -> list[dict]:
    rows = []
    for path in sorted(scenario_dir().glob("*.json")):
        sc = Scenario.load(path)
        rows.append(
            {
                "id": path.stem,
                "file": str(path.relative_to(repo_root())),
                "name": sc.name,
                "notes": sc.notes,
                "speed": sc.speed,
            }
        )
    return rows


def load_named(name: str) -> Scenario:
    safe = Path(name).name.replace("..", "")
    path = scenario_dir() / safe
    if path.suffix != ".json":
        path = scenario_dir() / f"{safe}.json"
    root = scenario_dir().resolve()
    resolved = path.resolve()
    if not str(resolved).startswith(str(root)) or not path.exists():
        raise FileNotFoundError(f"Unknown scenario '{name}'")
    return Scenario.load(path)


def pack_run(scenario: Scenario, result) -> dict:
    step = max(1, len(result.samples) // 200)
    samples = result.samples[::step]
    if result.samples and samples[-1] is not result.samples[-1]:
        samples.append(result.samples[-1])
    return {
        "summary": result.summary(),
        "world": {
            "width": scenario.warehouse.width,
            "height": scenario.warehouse.height,
            "radius": scenario.robot.radius,
            "start": [scenario.start.x, scenario.start.y, scenario.start.theta],
            "goal": [scenario.goal.x, scenario.goal.y],
            "obstacles": [b.as_list() for b in scenario.warehouse.obstacles],
            "use_cbf": scenario.use_cbf,
            "speed": scenario.speed,
            "friction": scenario.friction,
            "sensor_noise": scenario.sensor_noise,
        },
        "path": [
            {
                "x": s.x,
                "y": s.y,
                "theta": s.theta,
                "clearance": s.clearance,
                "t": s.t,
            }
            for s in samples
        ],
    }


def run_scenario(name: str, *, use_cbf: bool = False, speed: float | None = None,
                 friction: float = 1.0, sensor_noise: float = 0.0) -> dict:
    sc = load_named(name)
    updates = {"use_cbf": use_cbf, "friction": friction, "sensor_noise": sensor_noise}
    if speed is not None:
        updates["speed"] = float(speed)
    sc = sc.evolved(**updates)
    return pack_run(sc, simulate(sc))


def run_search(name: str, trials: int = 8) -> dict:
    base = load_named(name)
    trials = max(4, min(int(trials), 16))
    return {
        "random": summarize_search(random_search(base, n=trials)),
        "adversarial": summarize_search(adversarial_search(base, n=trials)),
        "mcmc": summarize_search(mcmc_search(base, n=trials)),
        "trials": trials,
    }


def run_tune(name: str) -> dict:
    base = load_named(name).evolved(use_cbf=True)
    result = bayesian_optimize(base, n_init=3, n_iter=4)
    return {
        "best_speed": result.best_speed,
        "best_score": result.best_score,
        "baseline_score": result.baseline_score,
        "improvement_pct": result.improvement_pct,
        "history": result.history,
    }


def snapshot() -> dict:
    return {"backends": status(), "scenarios": list_scenarios()}
