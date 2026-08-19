from __future__ import annotations

from pathlib import Path

from virtual_lab.models import Scenario
from virtual_lab.simulator import RunResult


def to_svg(scenario: Scenario, result: RunResult, path: str | Path, scale: float = 28.0) -> None:
    w = scenario.warehouse.width * scale
    h = scenario.warehouse.height * scale
    pad = 16

    def px(x: float, y: float) -> tuple[float, float]:
        return pad + x * scale, pad + (scenario.warehouse.height - y) * scale

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * pad}" height="{h + 2 * pad}">',
        f'<rect x="{pad}" y="{pad}" width="{w}" height="{h}" fill="#f4f7fb" stroke="#0f2c59" stroke-width="2"/>',
    ]
    for box in scenario.warehouse.obstacles:
        x, y = px(box.x0, box.y1)
        bw = (box.x1 - box.x0) * scale
        bh = (box.y1 - box.y0) * scale
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="#1b6b93" opacity="0.85"/>'
        )
    if result.samples:
        pts = " ".join(f"{px(s.x, s.y)[0]:.1f},{px(s.x, s.y)[1]:.1f}" for s in result.samples)
        color = "#1b6b93" if result.success else "#c44536"
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2"/>'
        )
        lx, ly = px(result.samples[-1].x, result.samples[-1].y)
        r = scenario.robot.radius * scale
        parts.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{r:.1f}" fill="{color}" opacity="0.7"/>')
    sx, sy = px(scenario.start.x, scenario.start.y)
    gx, gy = px(scenario.goal.x, scenario.goal.y)
    parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="5" fill="#d4a017"/>')
    parts.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="6" fill="#0f2c59"/>')
    parts.append(
        f'<text x="{pad}" y="{h + 2 * pad - 4}" font-size="11" font-family="Georgia, serif" fill="#5c6b7a">'
        f"{scenario.name}: {result.outcome} · {result.duration:.1f}s · path {result.path_length:.1f}m</text>"
    )
    parts.append("</svg>")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
