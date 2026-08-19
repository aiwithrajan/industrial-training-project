from __future__ import annotations

import json
import shutil
from pathlib import Path

from virtual_lab.backends.base import BackendNotAvailable
from virtual_lab.models import Scenario
from virtual_lab.simulator import Policy, RunResult, Sample

INSTALL = """NVIDIA Isaac Sim is not installed on this machine.

Isaac Sim 4.5+ (Linux, NVIDIA GPU, Ubuntu 22.04 recommended):
  1. Install the NVIDIA driver + CUDA-compatible GPU.
  2. Download Isaac Sim from NVIDIA Omniverse / Isaac Sim docs:
     https://docs.isaacsim.omniverse.nvidia.com/
  3. Create the Python env Isaac ships (or pip install isaacsim if using the pip preview).
  4. Run:
       ./python.sh /path/to/this/repo/simulators/isaac/run_episode.py \\
           --scenario scenarios/open_aisle.json --out /tmp/isaac_result.json

Docker (NGC, GPU required):
  docker compose --profile isaac build
  docker compose --profile isaac run --rm isaac \\
      python3 -m virtual_lab run --backend isaac --scenario scenarios/open_aisle.json

Isaac is the high-fidelity / vision / parallel-RL backend. The 2D twin and Gazebo
remain valid for control and failure search. Use all three for sim-to-sim gap checks.

Docs: docs/SIMULATORS.md
"""


class IsaacBackend:
    name = "isaac"

    def available(self) -> bool:
        if shutil.which("isaacsim") or shutil.which("isaac-sim"):
            return True
        try:
            import isaacsim  # noqa: F401

            return True
        except ImportError:
            return False

    def simulate(self, scenario: Scenario, policy: Policy | None = None) -> RunResult:
        if policy is not None:
            raise BackendNotAvailable("Isaac backend uses its own controller loop. Pass policy=None.")
        if not self.available():
            raise BackendNotAvailable(INSTALL)
        script = Path(__file__).resolve().parents[2] / "simulators" / "isaac" / "run_episode.py"
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory(prefix="vrtop-isaac-") as tmp:
            scenario_path = Path(tmp) / "scenario.json"
            result_path = Path(tmp) / "result.json"
            scenario_path.write_text(json.dumps(scenario.to_dict()), encoding="utf-8")
            proc = subprocess.run(
                [
                    "python3",
                    str(script),
                    "--scenario",
                    str(scenario_path),
                    "--out",
                    str(result_path),
                    "--headless",
                ],
                capture_output=True,
                text=True,
                timeout=scenario.max_time + 90,
                check=False,
            )
            if proc.returncode != 0 or not result_path.exists():
                raise BackendNotAvailable(
                    "Isaac episode failed.\n"
                    f"stdout:\n{proc.stdout[-2000:]}\nstderr:\n{proc.stderr[-2000:]}\n"
                    + INSTALL
                )
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        samples = [Sample(**row) for row in payload.get("samples", [])]
        summary = payload.get("summary", payload)
        return RunResult(
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


def scenario_to_isaac_prims(scenario: Scenario) -> dict:
    """Stage description Isaac's run_episode.py (or Omniverse) can load."""
    prims = [
        {
            "path": "/World/Ground",
            "type": "Cube",
            "size": [scenario.warehouse.width, scenario.warehouse.height, 0.05],
            "pose": [scenario.warehouse.width / 2, scenario.warehouse.height / 2, -0.025],
            "static": True,
        }
    ]
    for i, box in enumerate(scenario.warehouse.obstacles):
        prims.append(
            {
                "path": f"/World/Shelf_{i}",
                "type": "Cube",
                "size": [box.x1 - box.x0, box.y1 - box.y0, 1.4],
                "pose": [(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2, 0.7],
                "static": True,
            }
        )
    prims.append(
        {
            "path": "/World/Robot",
            "type": "DiffDrive",
            "radius": scenario.robot.radius,
            "pose": [scenario.start.x, scenario.start.y, scenario.robot.radius],
            "yaw": scenario.start.theta,
        }
    )
    return {"world": scenario.name, "prims": prims, "goal": [scenario.goal.x, scenario.goal.y]}
