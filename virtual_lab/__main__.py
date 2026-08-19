from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from virtual_lab.knowledge_graph import twin_graph
from virtual_lab.models import Scenario
from virtual_lab.simulator import simulate, write_run
from virtual_lab.visualize import to_svg


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_run(args: argparse.Namespace) -> int:
    scenario = Scenario.load(args.scenario)
    result = simulate(scenario)
    out = Path(args.out)
    write_run(result, out)
    svg = out.with_suffix(".svg")
    to_svg(scenario, result, svg)
    graph_path = out.with_name(out.stem + "_twin.json")
    graph_path.write_text(json.dumps(twin_graph(scenario), indent=2), encoding="utf-8")
    print(json.dumps(result.summary(), indent=2))
    print(f"log: {out}")
    print(f"map: {svg}")
    print(f"twin: {graph_path}")
    return 0 if result.success or args.allow_failure else 1


def cmd_compare(args: argparse.Namespace) -> int:
    rows = []
    for path in args.scenarios:
        scenario = Scenario.load(path)
        result = simulate(scenario)
        rows.append(result.summary())
    print(json.dumps(rows, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Virtual Robotics Testing lab (Month 1–2 MVP): 2D twin, navigation, logs."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Simulate one scenario and write logs")
    run.add_argument("--scenario", required=True)
    run.add_argument("--out", default=str(_repo_root() / "runs" / "last.json"))
    run.add_argument("--allow-failure", action="store_true")
    run.set_defaults(func=cmd_run)

    cmp_ = sub.add_parser("compare", help="Run several scenarios and print summaries")
    cmp_.add_argument("scenarios", nargs="+")
    cmp_.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
