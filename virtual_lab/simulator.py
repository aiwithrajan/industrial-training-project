from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from virtual_lab.controller import command, step, would_collide
from virtual_lab.models import Pose, Scenario
from virtual_lab.safety import collision, min_clearance


@dataclass
class Sample:
    t: float
    x: float
    y: float
    theta: float
    speed: float
    yaw: float
    clearance: float
    event: str | None = None


@dataclass
class RunResult:
    scenario: str
    success: bool
    outcome: str
    duration: float
    path_length: float
    min_clearance: float
    samples: list[Sample]

    def summary(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "success": self.success,
            "outcome": self.outcome,
            "duration_s": round(self.duration, 3),
            "path_length_m": round(self.path_length, 3),
            "min_clearance_m": round(self.min_clearance, 3),
            "steps": len(self.samples),
        }


def simulate(scenario: Scenario) -> RunResult:
    pose = scenario.start
    samples: list[Sample] = []
    path_length = 0.0
    t = 0.0
    worst_clear = float("inf")
    outcome = "timeout"

    while t <= scenario.max_time:
        speed, yaw = command(pose, scenario)
        if would_collide(pose, speed, yaw, scenario.dt, scenario):
            speed, yaw = 0.0, yaw * 0.35
            if would_collide(pose, speed, yaw, scenario.dt, scenario):
                speed, yaw = 0.0, 0.0
        nxt = step(pose, speed, yaw, scenario.dt)
        event = collision(nxt, scenario)
        clearance = min_clearance(nxt, scenario.warehouse)
        worst_clear = min(worst_clear, clearance)
        path_length += pose.distance_to(nxt)
        t += scenario.dt
        samples.append(
            Sample(t, nxt.x, nxt.y, nxt.theta, speed, yaw, clearance, event)
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
        samples=samples,
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
