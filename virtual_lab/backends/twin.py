from __future__ import annotations

from virtual_lab.models import Scenario
from virtual_lab.simulator import Policy, RunResult, simulate as twin_simulate


class TwinBackend:
    """In-repo 2D digital twin (default). No extra installs."""

    name = "twin"

    def available(self) -> bool:
        return True

    def simulate(self, scenario: Scenario, policy: Policy | None = None) -> RunResult:
        return twin_simulate(scenario, policy=policy)
