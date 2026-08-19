from __future__ import annotations

import json
from pathlib import Path

from virtual_lab.backends.gazebo_sdf import scenario_to_sdf
from virtual_lab.backends.isaac import scenario_to_isaac_prims
from virtual_lab.models import Scenario
from virtual_lab.simulator import simulate
from virtual_lab.visualize import to_svg


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def export_worlds(out: Path | None = None) -> dict[str, str]:
    out = out or (_root() / "simulators" / "worlds")
    out.mkdir(parents=True, exist_ok=True)
    written = {}
    for name in ("open_aisle", "blocked_aisle"):
        sc = Scenario.load(_root() / "scenarios" / f"{name}.json")
        sdf_path = out / f"{name}.sdf"
        prim_path = out / f"{name}.isaac.json"
        sdf_path.write_text(scenario_to_sdf(sc), encoding="utf-8")
        prim_path.write_text(json.dumps(scenario_to_isaac_prims(sc), indent=2), encoding="utf-8")
        written[name] = str(sdf_path)
    return written


def build_demo(out: Path | None = None) -> Path:
    out = out or (_root() / "docs" / "demo")
    out.mkdir(parents=True, exist_ok=True)
    runs = {}
    for name in ("open_aisle", "blocked_aisle"):
        sc = Scenario.load(_root() / "scenarios" / f"{name}.json")
        result = simulate(sc)
        to_svg(sc, result, out / f"{name}.svg")
        step = max(1, len(result.samples) // 80)
        runs[name] = {
            "summary": result.summary(),
            "width": sc.warehouse.width,
            "height": sc.warehouse.height,
            "radius": sc.robot.radius,
            "start": [sc.start.x, sc.start.y],
            "goal": [sc.goal.x, sc.goal.y],
            "obstacles": [b.as_list() for b in sc.warehouse.obstacles],
            "path": [[s.x, s.y] for s in result.samples[::step]],
        }
    eval_path = _root() / "docs" / "evaluation" / "evaluation.json"
    kpis = {}
    if eval_path.exists():
        kpis = json.loads(eval_path.read_text(encoding="utf-8")).get("kpis", {})
    worlds = export_worlds(_root() / "simulators" / "worlds")
    payload = {"kpis": kpis, "runs": runs, "worlds": worlds}
    (out / "demo.json").write_text(json.dumps(payload), encoding="utf-8")
    (out / "index.html").write_text(_html(payload), encoding="utf-8")
    return out / "index.html"


def _html(payload: dict) -> str:
    data = json.dumps(payload)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>VRTOP live demo</title>
<style>
  body {{ margin:0; font-family: Georgia, serif; background:#f4f7fb; color:#1f2a33; }}
  header {{ background:#0f2c59; color:#fff; padding:20px 28px; }}
  h1 {{ margin:0 0 4px; font-size:22px; }}
  .sub {{ opacity:.85; font-size:14px; }}
  .wrap {{ padding:20px 28px 40px; }}
  .kpis {{ display:flex; gap:10px; flex-wrap:wrap; margin:12px 0 20px; }}
  .card {{ background:#fff; border:1px solid #c9d4e0; padding:10px 14px; min-width:120px; }}
  .v {{ font-size:20px; color:#0f2c59; font-weight:bold; }}
  .l {{ font-size:11px; color:#5c6b7a; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  canvas {{ width:100%; background:#fff; border:1px solid #c9d4e0; }}
  button {{ background:#1b6b93; color:#fff; border:0; padding:8px 14px; cursor:pointer; font:inherit; }}
  pre {{ background:#0f2c59; color:#d7e4f0; padding:12px; overflow:auto; font-size:12px; }}
  @media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>Virtual Robotics Testing live demo</h1>
  <div class="sub">Open aisle reaches the goal. Blocked aisle is the what-if failure.</div>
</header>
<div class="wrap">
  <div class="kpis" id="kpis"></div>
  <p><button type="button" id="play">Play both runs</button></p>
  <div class="grid">
    <div><h3>open_aisle</h3><canvas id="c-open_aisle" width="640" height="400"></canvas><p id="s-open_aisle"></p></div>
    <div><h3>blocked_aisle</h3><canvas id="c-blocked_aisle" width="640" height="400"></canvas><p id="s-blocked_aisle"></p></div>
  </div>
  <h3>Run it</h3>
<pre>python3 -m virtual_lab doctor
python3 -m virtual_lab run --scenario scenarios/open_aisle.json
python3 -m virtual_lab search
gz sim simulators/worlds/open_aisle.sdf</pre>
</div>
<script>
const DATA = {data};
function kpi() {{
  const box = document.getElementById('kpis');
  Object.entries(DATA.kpis || {{}}).forEach(([k,v]) => {{
    const d = document.createElement('div');
    d.className = 'card';
    d.innerHTML = '<div class="v">'+v+'</div><div class="l">'+k+'</div>';
    box.appendChild(d);
  }});
}}
function draw(name, t) {{
  const run = DATA.runs[name];
  const c = document.getElementById('c-'+name);
  const ctx = c.getContext('2d');
  const sx = c.width / (run.width + 2);
  const sy = c.height / (run.height + 2);
  const X = x => (x+1)*sx;
  const Y = y => c.height - (y+1)*sy;
  ctx.clearRect(0,0,c.width,c.height);
  ctx.fillStyle = '#f4f7fb';
  ctx.fillRect(0,0,c.width,c.height);
  ctx.strokeStyle = '#0f2c59';
  ctx.strokeRect(X(0), Y(run.height), run.width*sx, run.height*sy);
  ctx.fillStyle = '#1b6b93';
  run.obstacles.forEach(b => {{
    ctx.fillRect(X(b[0]), Y(b[3]), (b[2]-b[0])*sx, (b[3]-b[1])*sy);
  }});
  ctx.fillStyle = '#d4a017';
  ctx.beginPath(); ctx.arc(X(run.start[0]), Y(run.start[1]), 5, 0, 7); ctx.fill();
  ctx.fillStyle = '#0f2c59';
  ctx.beginPath(); ctx.arc(X(run.goal[0]), Y(run.goal[1]), 6, 0, 7); ctx.fill();
  const n = Math.max(1, Math.floor(run.path.length * t));
  ctx.strokeStyle = run.summary.success ? '#1b6b93' : '#c44536';
  ctx.lineWidth = 2;
  ctx.beginPath();
  run.path.slice(0,n).forEach((p,i) => i?ctx.lineTo(X(p[0]),Y(p[1])):ctx.moveTo(X(p[0]),Y(p[1])));
  ctx.stroke();
  if (n) {{
    const p = run.path[n-1];
    ctx.beginPath(); ctx.arc(X(p[0]), Y(p[1]), run.radius*sx, 0, 7); ctx.fillStyle = ctx.strokeStyle; ctx.fill();
  }}
  document.getElementById('s-'+name).textContent = run.summary.outcome+' / '+run.summary.duration_s+'s';
}}
function play() {{
  const t0 = performance.now();
  function frame(now) {{
    const t = Math.min(1, (now-t0)/2800);
    draw('open_aisle', t);
    draw('blocked_aisle', t);
    if (t<1) requestAnimationFrame(frame);
  }}
  requestAnimationFrame(frame);
}}
kpi();
draw('open_aisle', 1);
draw('blocked_aisle', 1);
document.getElementById('play').onclick = play;
</script>
</body></html>
"""
