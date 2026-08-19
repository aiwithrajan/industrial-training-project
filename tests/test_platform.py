from __future__ import annotations

from pathlib import Path

from virtual_lab.adversarial import adversarial_search, random_search, summarize_search
from virtual_lab.bayesopt import bayesian_optimize
from virtual_lab.experiments import experiment_grammar, experiment_safety_cbf
from virtual_lab.grammar import generate_layout
from virtual_lab.mcmc import mcmc_search
from virtual_lab.models import Scenario
from virtual_lab.rl import train_q
from virtual_lab.simulator import simulate

ROOT = Path(__file__).resolve().parent.parent


def test_cbf_keeps_open_aisle_safe():
    sc = Scenario.load(ROOT / "scenarios" / "open_aisle.json").evolved(use_cbf=True)
    result = simulate(sc)
    assert result.success
    assert result.violations == 0


def test_adversarial_finds_at_least_as_many_failures_as_random():
    base = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    rnd = summarize_search(random_search(base, n=8))
    adv = summarize_search(adversarial_search(base, n=8))
    assert adv["failures"] >= rnd["failures"]


def test_mcmc_runs_and_records_cases():
    base = Scenario.load(ROOT / "scenarios" / "open_aisle.json")
    cases = mcmc_search(base, n=6)
    assert len(cases) == 6


def test_bayesopt_finds_nonnegative_score():
    base = Scenario.load(ROOT / "scenarios" / "open_aisle.json").evolved(use_cbf=True)
    result = bayesian_optimize(base, n_init=3, n_iter=3)
    assert result.best_score >= 0
    assert 0.45 <= result.best_speed <= 1.2


def test_grammar_layout_is_simulatable():
    sc = generate_layout(21)
    result = simulate(sc.evolved(use_cbf=True, max_time=30))
    assert result.outcome in {"goal", "timeout"} or result.outcome.startswith("obstacle")
    pack = experiment_grammar(n=2)
    assert pack["generated"] == 2


def test_rl_trains_a_q_table():
    base = Scenario.load(ROOT / "scenarios" / "open_aisle.json").evolved(use_cbf=True, max_time=16)
    policy = train_q(base, episodes=25, domain_randomize=True)
    assert len(policy.q) > 5


def test_safety_experiment_passes():
    assert experiment_safety_cbf()["passed"]
