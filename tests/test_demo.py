from pathlib import Path
from xml.etree import ElementTree as ET

from virtual_lab.demo import build_demo, export_worlds


def test_demo_writes_html_and_worlds(tmp_path):
    html = build_demo(tmp_path / "demo")
    assert html.exists()
    text = html.read_text(encoding="utf-8")
    assert "Play both runs" in text
    assert "open_aisle" in text
    worlds = export_worlds(tmp_path / "worlds")
    sdf = Path(worlds["open_aisle"])
    ET.fromstring(sdf.read_text(encoding="utf-8"))
    assert (tmp_path / "worlds" / "open_aisle.isaac.json").exists()
