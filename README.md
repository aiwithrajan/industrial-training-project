# Virtual Robotics Testing & Optimization Platform

Industrial training project: a virtual test lab that finds robot failures in simulation before hardware deployment.

## Documents

| File | Purpose |
| --- | --- |
| [Executive Summary.pdf](Executive%20Summary.pdf) | Full company brief (problem, novelty, roadmap, experiments) |
| [docs/One-Page Pitch.pdf](docs/One-Page%20Pitch.pdf) | One-page approval pitch |

Regenerate PDFs:

```bash
pip install -r scripts/requirements-pdf.txt
python3 scripts/generate_executive_summary.py
python3 scripts/generate_one_page_pitch.py
```

## Month 1–2 MVP (this repo)

A **2D digital twin** you can run without Gazebo or a GPU. It covers the first roadmap slice:

- Warehouse + differential-drive robot model
- A→B navigation with obstacle avoidance stop
- Collision / out-of-bounds checks
- Trajectory logs and an SVG playback map
- A small knowledge graph of robot, map, and task

Later months add adversarial search, Bayesian tuning, and ROS 2 / Gazebo.

### Run

```bash
python3 -m virtual_lab run --scenario scenarios/open_aisle.json --out runs/open.json
python3 -m virtual_lab run --scenario scenarios/blocked_aisle.json --out runs/blocked.json --allow-failure
python3 -m virtual_lab compare scenarios/open_aisle.json scenarios/blocked_aisle.json
```

Open aisle should reach the goal. Blocked aisle is the “what if the center aisle is closed?” case — the baseline controller has no global planner, so the run fails (timeout or collision). That gap is what months 3–4 (adversarial scenarios + better search) are for.

### Tests

```bash
pip install pytest
python3 -m pytest -q
```
