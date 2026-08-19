#!/usr/bin/env python3
"""Run one warehouse episode in NVIDIA Isaac Sim (headless-capable)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from virtual_lab.backends.isaac import scenario_to_isaac_prims
from virtual_lab.controller import apply_cbf, command, step
from virtual_lab.models import Pose, Scenario
from virtual_lab.safety import barrier_value, collision, min_clearance
from virtual_lab.simulator import RunResult, Sample, write_run


def _run_with_twin_kinematics(scenario: Scenario) -> RunResult:
    """Kinematic fallback used only for --dry-run (CI / no GPU)."""
    from virtual_lab.simulator import simulate

    return simulate(scenario)


def _run_with_isaac(scenario: Scenario, headless: bool) -> RunResult:
    from isaacsim import SimulationApp

    sim = SimulationApp({"headless": headless})
    try:
        import numpy as np
        from omni.isaac.core import World
        from omni.isaac.core.objects import DynamicCuboid, FixedCuboid
        from omni.isaac.core.robots import Robot

        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        for i, box in enumerate(scenario.warehouse.obstacles):
            world.scene.add(
                FixedCuboid(
                    prim_path=f"/World/Shelf_{i}",
                    name=f"shelf_{i}",
                    position=np.array(
                        [(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2, 0.7]
                    ),
                    scale=np.array([box.x1 - box.x0, box.y1 - box.y0, 1.4]),
                )
            )
        world.reset()
        pose = scenario.start
        samples: list[Sample] = []
        path = 0.0
        t = 0.0
        worst_c, worst_h, viol = 1e9, 1e9, 0
        outcome = "timeout"
        while t <= scenario.max_time:
            world.step(render=not headless)
            speed, yaw = command(pose, scenario)
            speed, yaw = apply_cbf(pose, speed, yaw, scenario)
            nxt = step(pose, speed, yaw, scenario.dt, scenario.friction)
            event = collision(nxt, scenario)
            c = min_clearance(nxt, scenario.warehouse)
            h = barrier_value(nxt, scenario)
            worst_c, worst_h = min(worst_c, c), min(worst_h, h)
            if h < 0:
                viol += 1
            path += pose.distance_to(nxt)
            t += scenario.dt
            samples.append(Sample(t, nxt.x, nxt.y, nxt.theta, speed, yaw, c, h, event))
            pose = nxt
            if event:
                outcome = event
                break
            if pose.distance_to(scenario.goal) <= scenario.goal_tolerance:
                outcome = "goal"
                break
        return RunResult(
            scenario=scenario.name,
            success=outcome == "goal",
            outcome=outcome,
            duration=t,
            path_length=path,
            min_clearance=worst_c,
            min_barrier=worst_h,
            samples=samples,
            violations=viol,
        )
    finally:
        sim.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Isaac Sim episode for VRTOP")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dry-export", action="store_true", help="Write prim JSON only")
    parser.add_argument("--dry-run", action="store_true", help="Use 2D kinematics (no GPU)")
    args = parser.parse_args()
    scenario = Scenario.load(args.scenario)
    if args.dry_export:
        Path(args.out).write_text(
            json.dumps(scenario_to_isaac_prims(scenario), indent=2), encoding="utf-8"
        )
        return 0
    if args.dry_run:
        result = _run_with_twin_kinematics(scenario)
        write_run(result, args.out)
        return 0 if result.success else 1
    try:
        result = _run_with_isaac(scenario, headless=args.headless)
    except ImportError:
        print(
            "isaacsim is not importable. Install Isaac Sim or pass --dry-run / --dry-export.",
            file=sys.stderr,
        )
        return 2
    write_run(result, args.out)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
