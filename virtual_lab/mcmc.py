from __future__ import annotations

import math
import random

from virtual_lab.adversarial import FailureCase, _perturbation, _with_block
from virtual_lab.models import Scenario
from virtual_lab.simulator import simulate


def mcmc_search(
    base: Scenario,
    n: int = 40,
    temperature: float = 0.35,
    rng: random.Random | None = None,
) -> list[FailureCase]:
    """Metropolis-Hastings over blocker (x, y). Energy is high when the robot still succeeds."""
    rng = rng or random.Random(7)
    x = (base.start.x + base.goal.x) / 2
    y = base.start.y + 1.5
    cases: list[FailureCase] = []
    result = simulate(_with_block(base, x, y), rng=random.Random(1))
    energy = (1.0 if result.success else 0.0) + 0.05 * _perturbation(base, x, y)

    for _ in range(n):
        nx = min(max(x + rng.gauss(0, 0.7), 3.0), base.warehouse.width - 3.0)
        ny = min(max(y + rng.gauss(0, 0.8), 1.4), base.warehouse.height - 1.4)
        trial = simulate(_with_block(base, nx, ny), rng=random.Random(1))
        n_energy = (1.0 if trial.success else 0.0) + 0.05 * _perturbation(base, nx, ny)
        accept = n_energy <= energy or rng.random() < math.exp((energy - n_energy) / temperature)
        if accept:
            x, y, energy, result = nx, ny, n_energy, trial
        cases.append(
            FailureCase("mcmc", x, y, result.outcome, result.success, _perturbation(base, x, y))
        )
    return cases
