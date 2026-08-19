from __future__ import annotations

import random

from virtual_lab.models import AABB, Pose, Robot, Scenario, Warehouse


def generate_layout(seed: int, n_aisles: int | None = None) -> Scenario:
    """Grammar: WAREHOUSE ? n AISLE shelves with a traversable mid-lane."""
    rng = random.Random(seed)
    n_aisles = n_aisles or rng.randint(2, 4)
    width, height = 20.0, 12.0
    obstacles: list[AABB] = []
    gap = 2.6
    for i in range(n_aisles):
        x0 = 3.5 + i * 4.0
        shelf_w = 1.1
        cut = height / 2
        lower_top = cut - gap / 2 + rng.uniform(-0.2, 0.2)
        upper_bot = cut + gap / 2 + rng.uniform(-0.2, 0.2)
        obstacles.append(AABB(x0, 0.3, x0 + shelf_w, max(2.0, lower_top)))
        obstacles.append(AABB(x0, min(height - 2.0, upper_bot), x0 + shelf_w, height - 0.3))
        if rng.random() < 0.25:
            # optional crate in the lane (unsafe placement)
            cy = cut + rng.uniform(-0.4, 0.4)
            obstacles.append(AABB(x0 + 1.3, cy - 0.5, x0 + 2.1, cy + 0.5))
    start = Pose(1.2, height / 2, 0.0)
    goal = Pose(width - 1.5, height / 2, 0.0)
    return Scenario(
        name=f"grammar_{seed}",
        warehouse=Warehouse(width, height, tuple(obstacles)),
        start=start,
        goal=goal,
        robot=Robot(),
        speed=1.0,
        max_time=40.0,
        notes="Ontology-style warehouse grammar (aisles + optional lane crate).",
        seed=seed,
    )
