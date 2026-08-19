from __future__ import annotations

from typing import Protocol

from virtual_lab.models import Scenario
from virtual_lab.simulator import Policy, RunResult


class BackendNotAvailable(RuntimeError):
    """Raised when Gazebo/ROS 2 or Isaac Sim is not installed on this machine."""


class SimulatorBackend(Protocol):
    name: str

    def available(self) -> bool: ...

    def simulate(self, scenario: Scenario, policy: Policy | None = None) -> RunResult: ...
