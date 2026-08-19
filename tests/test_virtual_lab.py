from __future__ import annotations

from pathlib import Path

import pytest

from virtual_lab.models import AABB, Pose, Robot, Scenario, Warehouse
from virtual_lab.safety import collision
from virtual_lab.simulator import simulate

ROOT = Path(__file__).resolve().parent.parent


def test_open_aisle_reaches_goal():
    result = simulate(Scenario.load(ROOT / "scenarios" / "open_aisle.json"))
    assert result.success
    assert result.outcome == "goal"
    assert result.path_length > 10
    assert result.min_clearance >= 0.35


def test_blocked_aisle_does_not_reach_goal():
    result = simulate(Scenario.load(ROOT / "scenarios" / "blocked_aisle.json"))
    assert not result.success
    assert result.outcome in {"timeout", "obstacle_2"} or result.outcome.startswith("obstacle")


def test_collision_detects_shelf():
    scenario = Scenario(
        name="hit",
        warehouse=Warehouse(10, 10, (AABB(4, 4, 6, 6),)),
        start=Pose(1, 5),
        goal=Pose(9, 5),
        robot=Robot(radius=0.4),
    )
    assert collision(Pose(5, 5), scenario) == "obstacle_0"
    assert collision(Pose(1, 5), scenario) is None


def test_out_of_bounds():
    scenario = Scenario(
        name="wall",
        warehouse=Warehouse(8, 8, ()),
        start=Pose(4, 4),
        goal=Pose(7, 4),
        robot=Robot(radius=0.4),
    )
    assert collision(Pose(-0.1, 4), scenario) == "out_of_bounds"
