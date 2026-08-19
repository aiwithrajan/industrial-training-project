from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from virtual_lab.adversarial import adversarial_search, random_search, summarize_search
from virtual_lab.bayesopt import bayesian_optimize
from virtual_lab.grammar import generate_layout
from virtual_lab.knowledge_graph import twin_graph
from virtual_lab.mcmc import mcmc_search
from virtual_lab.models import Scenario
from virtual_lab.pipeline import main_complete
from virtual_lab.simulator import simulate, write_run
from virtual_lab.visualize import to_svg


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_run(args: argparse.Namespace) -> int:
    scenario = Scenario.load(args.scenario)
    if args.cbf:
        scenario = scenario.evolved(use_cbf=True)
    result = simulate(scenario)
    out = Path(args.out)
    write_run(result, out)
    to_svg(scenario, result, out.with_suffix(".svg"))
    graph_path = out.with_name(out.stem + "_twin.json")
    graph_path.write_text(json.dumps(twin_graph(scenario), indent=2), encoding="utf-8")
    print(json.dumps(result.summary(), indent=2))
    print(f"log: {out}")
    return 0 if result.success or args.allow_failure else 1


def cmd_compare(args: argparse.Namespace) -> int:
    rows = []
    for path in args.scenarios:
        scenario = Scenario.load(path)
        result = simulate(scenario)
        rows.append(result.summary())
    print(json.dumps(rows, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    base = Scenario.load(args.scenario)
    rnd = summarize_search(random_search(base, n=args.trials))
    adv = summarize_search(adversarial_search(base, n=args.trials))
    mc = summarize_search(mcmc_search(base, n=args.trials))
    print(json.dumps({"random": rnd, "adversarial": adv, "mcmc": mc}, indent=2))
    return 0


def cmd_tune(args: argparse.Namespace) -> int:
    base = Scenario.load(args.scenario).evolved(use_cbf=True)
    result = bayesian_optimize(base)
    print(json.dumps(result.__dict__, indent=2, default=str))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(args.count):
        sc = generate_layout(seed=args.seed + i)
        path = out / f"{sc.name}.json"
        path.write_text(json.dumps(sc.to_dict(), indent=2), encoding="utf-8")
        result = simulate(sc.evolved(use_cbf=True))
        rows.append({"file": str(path), **result.summary()})
    print(json.dumps(rows, indent=2))
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    return main_complete(args.out, quick=args.quick)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Virtual Robotics Testing & Optimization Platform (6-month 2D twin)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Simulate one scenario")
    run.add_argument("--scenario", required=True)
    run.add_argument("--out", default=str(_repo_root() / "runs" / "last.json"))
    run.add_argument("--allow-failure", action="store_true")
    run.add_argument("--cbf", action="store_true")
    run.set_defaults(func=cmd_run)

    cmp_ = sub.add_parser("compare", help="Run several scenarios")
    cmp_.add_argument("scenarios", nargs="+")
    cmp_.set_defaults(func=cmd_compare)

    search = sub.add_parser("search", help="Random vs adversarial vs MCMC failure search")
    search.add_argument("--scenario", default=str(_repo_root() / "scenarios" / "open_aisle.json"))
    search.add_argument("--trials", type=int, default=16)
    search.set_defaults(func=cmd_search)

    tune = sub.add_parser("tune", help="Bayesian speed optimization")
    tune.add_argument("--scenario", default=str(_repo_root() / "scenarios" / "open_aisle.json"))
    tune.set_defaults(func=cmd_tune)

    gen = sub.add_parser("generate", help="Grammar-based warehouse layouts")
    gen.add_argument("--count", type=int, default=5)
    gen.add_argument("--seed", type=int, default=10)
    gen.add_argument("--out", default=str(_repo_root() / "scenarios" / "generated"))
    gen.set_defaults(func=cmd_generate)

    done = sub.add_parser("complete", help="Run the full 6-month evaluation suite")
    done.add_argument("--out", default=str(_repo_root() / "docs" / "evaluation"))
    done.add_argument("--quick", action="store_true")
    done.set_defaults(func=cmd_complete)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
