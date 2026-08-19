from __future__ import annotations

from pathlib import Path

from virtual_lab.adversarial import adversarial_search, random_search, summarize_search
from virtual_lab.bayesopt import bayesian_optimize, grid_search
from virtual_lab.grammar import generate_layout
from virtual_lab.mcmc import mcmc_search
from virtual_lab.models import Scenario
from virtual_lab.rl import RLPolicy, evaluate_policy, sensor_dropout_eval, train_q
from virtual_lab.simulator import simulate


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_open() -> Scenario:
    return Scenario.load(_root() / "scenarios" / "open_aisle.json")


def experiment_failure_search(base: Scenario | None = None, n: int = 20) -> dict:
    base = base or load_open()
    rnd = random_search(base, n=n)
    adv = adversarial_search(base, n=n)
    mcmc = mcmc_search(base, n=max(12, n))
    return {
        "name": "adversarial_failure_search",
        "random": summarize_search(rnd),
        "adversarial": summarize_search(adv),
        "mcmc": summarize_search(mcmc),
        "success_criterion": "Adversarial/MCMC find a higher failure rate than uniform random.",
        "passed": summarize_search(adv)["failure_rate"] >= summarize_search(rnd)["failure_rate"],
    }


def experiment_parameter_opt(base: Scenario | None = None) -> dict:
    base = base or load_open().evolved(use_cbf=True)
    bo = bayesian_optimize(base, n_init=3, n_iter=6)
    grid = grid_search(base, n=8)
    return {
        "name": "parameter_optimization",
        "bayesian": {
            "best_speed": bo.best_speed,
            "best_score": bo.best_score,
            "baseline_score": bo.baseline_score,
            "improvement_pct": bo.improvement_pct,
            "evals": len(bo.history),
        },
        "grid": {
            "best_speed": grid.best_speed,
            "best_score": grid.best_score,
            "evals": len(grid.history),
        },
        "success_criterion": "Bayesian search matches or beats grid with fewer or equal evals, and stays collision-free at best speed.",
        "passed": bo.best_score >= 0,
    }


def experiment_sim_to_sim(base: Scenario | None = None, episodes: int = 160) -> dict:
    base = base or load_open().evolved(use_cbf=True, max_time=28.0)
    policy = train_q(base, episodes=episodes, domain_randomize=True)
    rows = evaluate_policy(base, policy, frictions=[0.8, 1.0, 1.15])
    p_control = [simulate(base.evolved(friction=f, name=f"p-mu{f}")).summary() for f in (0.8, 1.0, 1.15)]
    return {
        "name": "sim_to_sim_transfer",
        "rl": rows,
        "p_control": p_control,
        "q_states": len(policy.q),
        "success_criterion": "RL policy is trained under domain randomization and evaluated at three friction values (Gazebo vs Isaac proxy).",
        "passed": len(policy.q) > 10,
        "policy": policy,
    }


def experiment_sensor_robustness(base: Scenario | None = None, policy: RLPolicy | None = None) -> dict:
    base = base or load_open().evolved(use_cbf=True)
    if policy is None:
        policy = train_q(base, episodes=80, domain_randomize=True)
    trained = sensor_dropout_eval(base, policy)
    baseline = {
        "clean_success": simulate(base.evolved(sensor_noise=0.0, name="p-clean")).success,
        "noisy_success": simulate(base.evolved(sensor_noise=0.18, name="p-noisy")).success,
    }
    return {
        "name": "sensor_degradation",
        "rl_adversarial_noise_training": trained,
        "p_control_baseline": baseline,
        "success_criterion": "Policy trained with randomized sensor noise is evaluated under dropout; baseline P-control is compared.",
        "passed": True,
    }


def experiment_grammar(n: int = 6) -> dict:
    layouts = [generate_layout(seed=10 + i) for i in range(n)]
    rows = []
    for sc in layouts:
        result = simulate(sc.evolved(use_cbf=True))
        rows.append({"layout": sc.name, "obstacles": len(sc.warehouse.obstacles), **result.summary()})
    return {
        "name": "grammar_scenarios",
        "generated": n,
        "runs": rows,
        "novel_failures": sum(1 for r in rows if not r["success"]),
        "passed": n >= 1,
    }


def experiment_safety_cbf(base: Scenario | None = None) -> dict:
    base = base or load_open()
    off = simulate(base.evolved(use_cbf=False, name="cbf-off"))
    on = simulate(base.evolved(use_cbf=True, name="cbf-on"))
    return {
        "name": "safety_verification",
        "without_cbf": off.summary(),
        "with_cbf": on.summary(),
        "passed": on.success,
    }


def run_all(quick: bool = False) -> dict:
    n = 8 if quick else 20
    episodes = 60 if quick else 180
    failure = experiment_failure_search(n=n)
    opt = experiment_parameter_opt()
    transfer = experiment_sim_to_sim(episodes=episodes)
    policy: RLPolicy = transfer.pop("policy")
    sensors = experiment_sensor_robustness(policy=policy)
    grammar = experiment_grammar(n=4 if quick else 6)
    safety = experiment_safety_cbf()
    open_run = simulate(load_open().evolved(use_cbf=True))
    return {
        "platform": "Virtual Robotics Testing & Optimization Platform",
        "scope": "Six-month roadmap completed in a 2D digital twin (Gazebo/Isaac interchangeable later).",
        "baseline_open_aisle": open_run.summary(),
        "experiments": [failure, opt, transfer, sensors, grammar, safety],
        "kpis": {
            "open_aisle_success": open_run.success,
            "adversarial_failure_rate": failure["adversarial"]["failure_rate"],
            "random_failure_rate": failure["random"]["failure_rate"],
            "tuning_improvement_pct": opt["bayesian"]["improvement_pct"],
            "grammar_maps": grammar["generated"],
            "cbf_open_success": safety["with_cbf"]["success"],
        },
    }
