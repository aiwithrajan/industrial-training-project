from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from virtual_lab.backends.base import BackendNotAvailable
from virtual_lab.backends.gazebo_sdf import scenario_to_sdf
from virtual_lab.models import Scenario
from virtual_lab.simulator import Policy, RunResult

INSTALL = """Gazebo + ROS 2 is not installed on this machine.

Ubuntu 22.04 (Humble + Gazebo Fortress):
  sudo apt update
  sudo apt install -y ros-humble-desktop ros-humble-ros-gz ros-humble-ros-gz-sim \\
      ros-humble-ros-gz-bridge python3-colcon-common-extensions
  source /opt/ros/humble/setup.bash

Ubuntu 24.04 (Jazzy + Gazebo Harmonic):
  sudo apt install -y ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-ros-gz-sim

Then build the workspace in this repo:
  cd simulators/ros2_ws
  source /opt/ros/$ROS_DISTRO/setup.bash
  colcon build --symlink-install
  source install/setup.bash

Or use Docker:
  docker compose --profile gazebo build
  docker compose --profile gazebo run --rm gazebo \\
      python3 -m virtual_lab run --backend gazebo --scenario scenarios/open_aisle.json --allow-failure

Docs: docs/SIMULATORS.md
"""


class GazeboBackend:
    name = "gazebo"

    def available(self) -> bool:
        return bool(shutil.which("ros2") and (shutil.which("gz") or shutil.which("ign")))

    def simulate(self, scenario: Scenario, policy: Policy | None = None) -> RunResult:
        if policy is not None:
            raise BackendNotAvailable(
                "Gazebo backend uses the onboard ROS 2 controller. Pass policy=None."
            )
        if not self.available():
            raise BackendNotAvailable(INSTALL)
        world = scenario_to_sdf(scenario)
        with tempfile.TemporaryDirectory(prefix="vrtop-gz-") as tmp:
            tmp_path = Path(tmp)
            world_path = tmp_path / "world.sdf"
            scenario_path = tmp_path / "scenario.json"
            result_path = tmp_path / "result.json"
            world_path.write_text(world, encoding="utf-8")
            scenario_path.write_text(json.dumps(scenario.to_dict()), encoding="utf-8")
            env = os.environ.copy()
            cmd = [
                "ros2",
                "launch",
                "vrtop_gazebo",
                "warehouse.launch.py",
                f"world:={world_path}",
                f"scenario:={scenario_path}",
                f"result:={result_path}",
            ]
            proc = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=scenario.max_time + 45,
                check=False,
            )
            if proc.returncode != 0 or not result_path.exists():
                raise BackendNotAvailable(
                    "Gazebo launch failed.\n"
                    f"stdout:\n{proc.stdout[-2000:]}\nstderr:\n{proc.stderr[-2000:]}\n"
                    + INSTALL
                )
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        from virtual_lab.simulator import RunResult as RR
        from virtual_lab.simulator import Sample

        samples = [Sample(**row) for row in payload.get("samples", [])]
        summary = payload.get("summary", payload)
        return RR(
            scenario=scenario.name,
            success=bool(summary.get("success")),
            outcome=str(summary.get("outcome", "timeout")),
            duration=float(summary.get("duration_s", 0.0)),
            path_length=float(summary.get("path_length_m", 0.0)),
            min_clearance=float(summary.get("min_clearance_m", 0.0)),
            min_barrier=float(summary.get("min_barrier", 0.0)),
            samples=samples,
            violations=int(summary.get("violations", 0)),
        )
