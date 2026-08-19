from __future__ import annotations

from pathlib import Path

import pytest

from virtual_lab.backends import get_backend, status
from virtual_lab.backends.base import BackendNotAvailable
from virtual_lab.backends.gazebo_sdf import scenario_to_sdf
from virtual_lab.backends.isaac import scenario_to_isaac_prims
from virtual_lab.models import Scenario

ROOT = Path(__file__).resolve().parent.parent


def test_twin_backend_runs_open_aisle():
    sc = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    result = get_backend("twin").simulate(sc)
    assert result.success


def test_doctor_reports_twin_only_here():
    info = status()
    assert info["twin"] is True
    assert info["gazebo"] is False
    assert info["isaac"] is False


def test_gazebo_unavailable_explains_install():
    sc = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    with pytest.raises(BackendNotAvailable) as err:
        get_backend("gazebo").simulate(sc)
    assert "ros-humble" in str(err.value) or "colcon" in str(err.value)


def test_isaac_unavailable_explains_install():
    sc = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    with pytest.raises(BackendNotAvailable) as err:
        get_backend("isaac").simulate(sc)
    assert "Isaac" in str(err.value)


def test_sdf_export_contains_robot_and_shelves():
    sc = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    sdf = scenario_to_sdf(sc)
    assert "<sdf version=" in sdf
    assert 'model name="robot"' in sdf
    assert "gz-sim-diff-drive-system" in sdf
    assert "shelf_0" in sdf
    assert sc.warehouse.obstacles


def test_isaac_prim_export():
    sc = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    prims = scenario_to_isaac_prims(sc)
    assert prims["world"] == "open_aisle"
    assert any(p["path"] == "/World/Robot" for p in prims["prims"])
    assert any(p["path"].startswith("/World/Shelf_") for p in prims["prims"])


def test_unknown_backend():
    with pytest.raises(BackendNotAvailable):
        get_backend("unreal")
