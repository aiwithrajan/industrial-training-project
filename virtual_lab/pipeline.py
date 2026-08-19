from __future__ import annotations

import json
from pathlib import Path

from virtual_lab.experiments import run_all
from virtual_lab.report import write_dashboard, write_json


def complete(out_dir: str | Path, quick: bool = False) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = run_all(quick=quick)
    write_json(payload, out_dir / "evaluation.json")
    write_dashboard(payload, out_dir / "dashboard.html")
    return payload


def main_complete(out: str, quick: bool) -> int:
    payload = complete(out, quick=quick)
    print(json.dumps(payload.get("kpis", {}), indent=2))
    print(f"json: {Path(out) / 'evaluation.json'}")
    print(f"dash: {Path(out) / 'dashboard.html'}")
    return 0
