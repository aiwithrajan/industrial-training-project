# Virtual Robotics Testing & Optimization Platform

Industrial training project: a virtual test lab that finds robot failures in simulation before hardware is at risk.

The **six-month algorithms run on a 2D twin by default**. Plug in **Gazebo + ROS 2** or **Isaac Sim** with `--backend` when those engines are installed. See [docs/SIMULATORS.md](docs/SIMULATORS.md).

## Show it working (UI)

```bash
python3 -m virtual_lab ui
```

Open **http://127.0.0.1:8765**

1. Choose `open_aisle` → **Run scenario** (robot reaches the gold goal).
2. Choose `blocked_aisle` → **Run scenario** (gets stuck — the what-if).
3. Optional: **Find failures** and **Tune speed** on the same screen.


## Documents

| File | Purpose |
| --- | --- |
| [Executive Summary.pdf](Executive%20Summary.pdf) | Company brief |
| [docs/One-Page Pitch.pdf](docs/One-Page%20Pitch.pdf) | One-page ask |
| [docs/Evaluation Report.pdf](docs/Evaluation%20Report.pdf) | Experiment results |
| [docs/Demo Slides.pdf](docs/Demo%20Slides.pdf) | 8-slide company presentation |
| [docs/demo/index.html](docs/demo/index.html) | Interactive path playback |

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

Open aisle should reach the goal. Blocked aisle and adversarial crates demonstrate “what if the center aisle is closed?”.

## Live demo (slides + playback)

```bash
python3 -m virtual_lab demo
python3 scripts/generate_slides.py
```

Open `docs/demo/index.html` and click **Play both runs**. Pre-exported Gazebo worlds land in `simulators/worlds/` (`gz sim simulators/worlds/open_aisle.sdf` after Gazebo is installed).

## Tests

```bash
pip install pytest
python3 -m pytest -q
```
