from virtual_lab.ui import api


def test_list_scenarios():
    names = {s["id"] for s in api.list_scenarios()}
    assert "open_aisle" in names
    assert "blocked_aisle" in names


def test_run_open_aisle_for_ui():
    packed = api.run_scenario("open_aisle", use_cbf=True, speed=1.0)
    assert packed["summary"]["success"] is True
    assert packed["path"]
    assert packed["world"]["width"] == 20


def test_run_blocked_aisle_for_ui():
    packed = api.run_scenario("blocked_aisle")
    assert packed["summary"]["success"] is False
