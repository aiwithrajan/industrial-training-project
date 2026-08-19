from __future__ import annotations

import random
from dataclasses import dataclass

from virtual_lab.models import AABB, Scenario, Warehouse
from virtual_lab.simulator import simulate


@dataclass
class FailureCase:
    method: str
    x: float
    y: float
    outcome: str
    success: bool
    perturbation: float


def _with_block(base: Scenario, x: float, y: float, w: float = 1.2, h: float = 2.4) -> Scenario:
    block = AABB(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    obstacles = tuple(base.warehouse.obstacles) + (block,)
    warehouse = Warehouse(base.warehouse.width, base.warehouse.height, obstacles)
    return base.evolved(
        name=f"{base.name}+block@{x:.1f},{y:.1f}",
        warehouse=warehouse,
    )


def _perturbation(base: Scenario, x: float, y: float) -> float:
    mid_x = (base.start.x + base.goal.x) / 2
    mid_y = (base.start.y + base.goal.y) / 2
    return ((x - mid_x) ** 2 + (y - mid_y) ** 2) ** 0.5


def random_search(base: Scenario, n: int = 24, rng: random.Random | None = None) -> list[FailureCase]:
    rng = rng or random.Random(0)
    found: list[FailureCase] = []
    for _ in range(n):
        x = rng.uniform(3.0, base.warehouse.width - 3.0)
        y = rng.uniform(1.5, base.warehouse.height - 1.5)
        result = simulate(_with_block(base, x, y), rng=random.Random(1))
        found.append(
            FailureCase("random", x, y, result.outcome, result.success, _perturbation(base, x, y))
        )
    return found


def adversarial_search(
    base: Scenario, n: int = 24, rng: random.Random | None = None
) -> list[FailureCase]:
    """Hill-climb a blocking crate onto the start-goal line to maximize failure."""
    rng = rng or random.Random(1)
    mid_x = (base.start.x + base.goal.x) / 2
    y = rng.uniform(2.0, base.warehouse.height - 2.0)
    x = mid_x
    found: list[FailureCase] = []
    step = 0.7
    for i in range(n):
        result = simulate(_with_block(base, x, y), rng=random.Random(1))
        found.append(
            FailureCase("adversarial", x, y, result.outcome, result.success, _perturbation(base, x, y))
        )
        if not result.success:
            y += rng.choice([-1, 1]) * step * 0.3
        else:
            # move toward the lane center
            y += (base.start.y - y) * 0.45 + rng.uniform(-0.15, 0.15)
        y = min(max(y, 1.4), base.warehouse.height - 1.4)
        x = mid_x + (0.4 if i % 2 else -0.4)
    return found


def summarize_search(cases: list[FailureCase]) -> dict:
    fails = [c for c in cases if not c.success]
    return {
        "trials": len(cases),
        "failures": len(fails),
        "failure_rate": round(len(fails) / len(cases), 3) if cases else 0.0,
        "min_perturbation": round(min((c.perturbation for c in fails), default=0.0), 3),
        "modes": sorted({c.outcome for c in fails}),
    }
