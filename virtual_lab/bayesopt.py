from __future__ import annotations

import math
from dataclasses import dataclass

from virtual_lab.models import Scenario
from virtual_lab.simulator import simulate


def _solve(K: list[list[float]], y: list[float]) -> list[float]:
    n = len(y)
    a = [row[:] + [y[i]] for i, row in enumerate(K)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(a[r][i]))
        a[i], a[pivot] = a[pivot], a[i]
        diag = a[i][i] or 1e-9
        for j in range(i, n + 1):
            a[i][j] /= diag
        for r in range(n):
            if r == i:
                continue
            factor = a[r][i]
            for j in range(i, n + 1):
                a[r][j] -= factor * a[i][j]
    return [a[i][n] for i in range(n)]


def _rbf(a: float, b: float, length: float = 0.18) -> float:
    return math.exp(-((a - b) ** 2) / (2 * length**2))


def _mu_sigma(xs: list[float], ys: list[float], x: float) -> tuple[float, float]:
    n = len(xs)
    k = [_rbf(x, xi) for xi in xs]
    K = [[_rbf(xs[i], xs[j]) + (1e-5 if i == j else 0.0) for j in range(n)] for i in range(n)]
    alpha = _solve(K, ys)
    mu = sum(ki * ai for ki, ai in zip(k, alpha))
    k_alpha = _solve(K, k)
    var = max(1e-6, 1.0 - sum(ki * ai for ki, ai in zip(k, k_alpha)))
    return mu, math.sqrt(var)


def _ei(mu: float, sigma: float, best: float) -> float:
    if sigma < 1e-8:
        return 0.0
    z = (mu - best) / sigma
    cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2)))
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return (mu - best) * cdf + sigma * pdf


def _objective(scenario: Scenario, speed: float) -> float:
    run = simulate(scenario.evolved(speed=speed, name=f"{scenario.name}@v{speed:.2f}"))
    if not run.success:
        return -1.0
    return run.summary()["throughput_items_per_hr"]


@dataclass
class TuneResult:
    best_speed: float
    best_score: float
    history: list[dict]
    baseline_score: float
    improvement_pct: float


def bayesian_optimize(
    scenario: Scenario,
    n_init: int = 3,
    n_iter: int = 7,
    lo: float = 0.45,
    hi: float = 1.2,
) -> TuneResult:
    grid_init = [lo, (lo + hi) / 2, hi][:n_init]
    xs: list[float] = []
    ys: list[float] = []
    history: list[dict] = []
    for x in grid_init:
        y = _objective(scenario, x)
        xs.append(x)
        ys.append(y)
        history.append({"speed": round(x, 3), "score": round(y, 3), "kind": "init"})

    for _ in range(n_iter):
        best = max(ys)
        candidates = [lo + i * (hi - lo) / 24 for i in range(25)]
        x_next = max(candidates, key=lambda x: _ei(*_mu_sigma(xs, ys, x), best))
        y = _objective(scenario, x_next)
        xs.append(x_next)
        ys.append(y)
        history.append({"speed": round(x_next, 3), "score": round(y, 3), "kind": "ei"})

    best_i = max(range(len(ys)), key=lambda i: ys[i])
    baseline = _objective(scenario, scenario.speed)
    best_score = ys[best_i]
    improvement = 0.0 if baseline <= 0 else 100.0 * (best_score - baseline) / abs(baseline)
    return TuneResult(
        best_speed=round(xs[best_i], 3),
        best_score=round(best_score, 3),
        history=history,
        baseline_score=round(baseline, 3),
        improvement_pct=round(improvement, 2),
    )


def grid_search(scenario: Scenario, n: int = 10, lo: float = 0.45, hi: float = 1.2) -> TuneResult:
    history = []
    best_s, best_y = scenario.speed, -1e9
    for i in range(n):
        x = lo + i * (hi - lo) / max(n - 1, 1)
        y = _objective(scenario, x)
        history.append({"speed": round(x, 3), "score": round(y, 3), "kind": "grid"})
        if y > best_y:
            best_s, best_y = x, y
    baseline = _objective(scenario, scenario.speed)
    improvement = 0.0 if baseline <= 0 else 100.0 * (best_y - baseline) / abs(baseline)
    return TuneResult(
        best_speed=round(best_s, 3),
        best_score=round(best_y, 3),
        history=history,
        baseline_score=round(baseline, 3),
        improvement_pct=round(improvement, 2),
    )
