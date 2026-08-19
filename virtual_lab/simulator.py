from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from virtual_lab.controller import apply_cbf, command, step, would_collide
from virtual_lab.models import Pose, Scenario
from virtual_lab.safety import barrier_value, collision, min_clearance

Policy = Callable[[Pose, Scenario], tuple[float, float]]


@dataclass
class Sample:
    t: float
    x: float
    y: float
    theta: float
    speed: float
    yaw: float
    clearance: float
    barrier: float
    event: str | None = None


@dataclass
class RunResult:
    scenario: str
    success: bool
    outcome: str
    duration: float
    path_length: float
    min_clearance: float
    min_barrier: float
    samples: list[Sample]
    violations: int = 0

    def summary(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "success": self.success,
            "outcome": self.outcome,
            "duration_s": round(self.duration, 3),
            "path_length_m": round(self.path_length, 3),
            "min_clearance_m": round(self.min_clearance, 3),
            "min_barrier": round(self.min_barrier, 3),
            "violations": self.violations,
            "steps": len(self.samples),
            "throughput_items_per_hr": round(
                (3600.0 / self.duration) if self.success and self.duration > 0 else 0.0, 2
            ),
        }


def simulate(scenario: Scenario, policy: Policy | None = None, rng: random.Random | None = None) -> RunResult:
    policy = policy or command
    rng = rng or random.Random(scenario.seed)
    pose = scenario.start
    samples: list[Sample] = []
    path_length = 0.0
    t = 0.0
    worst_clear = float("inf")
    worst_h = float("inf")
    violations = 0
    outcome = "timeout"

    while t <= scenario.max_time:
        observed = pose.jitter(rng, scenario.sensor_noise)
        speed, yaw = policy(observed, scenario)
        speed, yaw = apply_cbf(pose, speed, yaw, scenario)
        if would_collide(pose, speed, yaw, scenario.dt, scenario):
            speed, yaw = 0.0, yaw * 0.35
            if would_collide(pose, speed, yaw, scenario.dt, scenario):
                speed, yaw = 0.0, 0.0
        nxt = step(pose, speed, yaw, scenario.dt, scenario.friction)
        event = collision(nxt, scenario)
        clearance = min_clearance(nxt, scenario.warehouse)
        h = barrier_value(nxt, scenario)
        worst_clear = min(worst_clear, clearance)
        worst_h = min(worst_h, h)
        if h < 0:
            violations += 1
        path_length += pose.distance_to(nxt)
        t += scenario.dt
        samples.append(
            Sample(t, nxt.x, nxt.y, nxt.theta, speed, yaw, clearance, h, event)
        )
        pose = nxt
        if event:
            outcome = event
            break
        if pose.distance_to(scenario.goal) <= scenario.goal_tolerance:
            outcome = "goal"
            break

    success = outcome == "goal"
    return RunResult(
        scenario=scenario.name,
        success=success,
        outcome=outcome,
        duration=t,
        path_length=path_length,
        min_clearance=0.0 if worst_clear == float("inf") else worst_clear,
        min_barrier=0.0 if worst_h == float("inf") else worst_h,
        samples=samples,
        violations=violations,
    )


def write_run(result: RunResult, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": result.summary(),
        "samples": [asdict(s) for s in result.samples],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
