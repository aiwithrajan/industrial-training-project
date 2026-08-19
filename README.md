# Virtual Robotics Testing & Optimization Platform

Industrial training project: a virtual test lab that finds robot failures in simulation before hardware is at risk.

The **six-month algorithms run on a 2D twin by default**. Plug in **Gazebo + ROS 2** or **Isaac Sim** with `--backend` when those engines are installed. See [docs/SIMULATORS.md](docs/SIMULATORS.md).

```bash
python3 -m virtual_lab doctor
python3 -m virtual_lab run --backend twin --scenario scenarios/open_aisle.json
```

## Documents

| File | Purpose |
| --- | --- |
| [Executive Summary.pdf](Executive%20Summary.pdf) | Company brief |
| [docs/One-Page Pitch.pdf](docs/One-Page%20Pitch.pdf) | One-page ask |
| [docs/Evaluation Report.pdf](docs/Evaluation%20Report.pdf) | Experiment results |
| [docs/SIMULATORS.md](docs/SIMULATORS.md) | How to add Gazebo/ROS 2 and Isaac Sim |

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
