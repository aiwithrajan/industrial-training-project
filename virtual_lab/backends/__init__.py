from __future__ import annotations

from virtual_lab.backends.base import BackendNotAvailable, SimulatorBackend
from virtual_lab.backends.gazebo import GazeboBackend
from virtual_lab.backends.isaac import IsaacBackend
from virtual_lab.backends.twin import TwinBackend

BACKENDS = {
    "twin": TwinBackend,
    "gazebo": GazeboBackend,
    "isaac": IsaacBackend,
}


def get_backend(name: str) -> SimulatorBackend:
    key = name.strip().lower()
    if key not in BACKENDS:
        raise BackendNotAvailable(
            f"Unknown backend '{name}'. Choose: {', '.join(sorted(BACKENDS))}."
        )
    return BACKENDS[key]()


def status() -> dict[str, bool]:
    return {name: cls().available() for name, cls in BACKENDS.items()}
