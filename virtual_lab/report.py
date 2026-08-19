from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    slim = json.loads(json.dumps(payload, default=str))
    path.write_text(json.dumps(slim, indent=2), encoding="utf-8")


def write_dashboard(payload: dict, path: Path) -> None:
    kpis = payload.get("kpis", {})
    cards = "".join(
        f'<div class="card"><div class="v">{html.escape(str(v))}</div>'
        f'<div class="l">{html.escape(str(k))}</div></div>'
        for k, v in kpis.items()
    )
    blocks = []
    for exp in payload.get("experiments", []):
        body = html.escape(json.dumps({k: v for k, v in exp.items() if k != "name"}, indent=2))
        passed = "PASS" if exp.get("passed") else "CHECK"
        blocks.append(
            f"<section><h2>{html.escape(exp.get('name', ''))} "
            f"<span class='tag'>{passed}</span></h2><pre>{body}</pre></section>"
        )
    scope = html.escape(payload.get("scope", ""))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>Virtual lab dashboard</title>
<style>
 body {{ font-family: Georgia, serif; margin: 0; background: #f4f7fb; color: #1f2a33; }}
 header {{ background: #0f2c59; color: #fff; padding: 28px 36px; }}
 h1 {{ margin: 0 0 6px; }}
 .wrap {{ padding: 24px 36px 48px; }}
 .row {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0 28px; }}
 .card {{ background: #fff; border: 1px solid #c9d4e0; padding: 14px 18px; min-width: 140px; }}
 .v {{ font-size: 22px; font-weight: bold; color: #0f2c59; }}
 .l {{ font-size: 12px; color: #5c6b7a; }}
 section {{ background: #fff; border: 1px solid #c9d4e0; padding: 16px 20px; margin-bottom: 16px; }}
 pre {{ white-space: pre-wrap; font-size: 12px; }}
 .tag {{ background: #1b6b93; color: #fff; font-size: 11px; padding: 2px 8px; }}
</style></head>
<body>
<header>
  <h1>Virtual Robotics Testing and Optimization</h1>
  <div>Evaluation dashboard -- {scope}</div>
  <div style="opacity:.7;margin-top:6px">{stamp}</div>
</header>
<div class="wrap">
  <div class="row">{cards}</div>
  {''.join(blocks)}
</div>
</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
