# Virtual Robotics Testing & Optimization Platform

Industrial training project: a virtual test lab that finds robot failures in simulation before hardware is at risk.

The **six-month roadmap is implemented on a 2D digital twin** in this repo (no GPU or Gazebo required). Gazebo / Isaac Sim can replace the physics engine later; search, tuning, RL, and safety stay the same.

## Documents

| File | Purpose |
| --- | --- |
| [Executive Summary.pdf](Executive%20Summary.pdf) | Company brief |
| [docs/One-Page Pitch.pdf](docs/One-Page%20Pitch.pdf) | One-page ask |
| [docs/Evaluation Report.pdf](docs/Evaluation%20Report.pdf) | Experiment results |
| [docs/evaluation/dashboard.html](docs/evaluation/dashboard.html) | Interactive KPI dashboard |

## Roadmap coverage

| Months | Capability | Command |
| --- | --- | --- |
| 1–2 | Twin, A→B nav, logs, collisions | `python3 -m virtual_lab run --scenario scenarios/open_aisle.json` |
| 3–4 | Adversarial + MCMC failure search, Bayesian speed tuning | `python3 -m virtual_lab search` · `python3 -m virtual_lab tune` |
| 5 | Domain-randomized Q-learning, sim-to-sim friction, CBF shield | included in `complete` |
| 6 | Grammar layouts, full evaluation suite, dashboard + report | `python3 -m virtual_lab complete` |

## Run the full suite

```bash
python3 -m pytest -q
python3 -m virtual_lab complete --out docs/evaluation
python3 scripts/generate_evaluation_report.py
```

Open aisle should reach the goal. Blocked aisle and adversarial crates demonstrate “what if this aisle is closed?”. Bayesian tuning searches a faster safe speed. Grammar maps mint new warehouses automatically.

## Tests

```bash
pip install pytest
python3 -m pytest -q
```
