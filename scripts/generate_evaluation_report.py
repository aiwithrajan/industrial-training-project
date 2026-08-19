#!/usr/bin/env python3
"""Write docs/Evaluation Report.pdf from evaluation.json."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0F2C59")
MUTED = colors.HexColor("#5C6B7A")
LINE = colors.HexColor("#C9D4E0")
LIGHT = colors.HexColor("#F4F7FB")


def build(payload: dict, out: Path) -> None:
    styles = {
        "h": ParagraphStyle("h", fontName="Times-Bold", fontSize=14, textColor=NAVY, spaceBefore=8, spaceAfter=6),
        "b": ParagraphStyle("b", fontName="Times-Roman", fontSize=10, leading=13, alignment=TA_JUSTIFY, spaceAfter=6),
        "k": ParagraphStyle("k", fontName="Times-Bold", fontSize=11, textColor=NAVY, alignment=1),
        "l": ParagraphStyle("l", fontName="Times-Roman", fontSize=8, textColor=MUTED, alignment=1),
        "c": ParagraphStyle("c", fontName="Times-Roman", fontSize=8, leading=11),
        "th": ParagraphStyle("th", fontName="Times-Bold", fontSize=8, textColor=colors.white),
    }
    story = []
    story.append(Paragraph("Evaluation report: six-month platform", styles["h"]))
    story.append(Paragraph(payload.get("scope", ""), styles["b"]))
    kpis = list(payload.get("kpis", {}).items())
    cells = []
    for k, v in kpis:
        inner = Table(
            [[Paragraph(str(v), styles["k"])], [Paragraph(k.replace("_", " "), styles["l"])]]
        )
        inner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        cells.append(inner)
    if cells:
        story.append(Table([cells], colWidths=[175 * mm / max(len(cells), 1)] * len(cells)))
        story.append(Spacer(1, 8))
    rows = [
        [
            Paragraph("Experiment", styles["th"]),
            Paragraph("Passed", styles["th"]),
            Paragraph("Notes", styles["th"]),
        ]
    ]
    for exp in payload.get("experiments", []):
        rows.append(
            [
                Paragraph(exp.get("name", ""), styles["c"]),
                Paragraph("yes" if exp.get("passed") else "review", styles["c"]),
                Paragraph(exp.get("success_criterion", ""), styles["c"]),
            ]
        )
    table = Table(rows, colWidths=[45 * mm, 22 * mm, 108 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "This evaluation runs entirely on the in-repo 2D digital twin. Physics engines such as "
            "Gazebo or Isaac Sim can replace the virtual lab later; the adversarial search, Bayesian "
            "tuning, CBF shield, domain-randomized RL, and grammar layouts stay the same.",
            styles["b"],
        )
    )
    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="Evaluation Report",
        author="Industrial Training Project",
    )
    doc.build(story)
    print(f"Wrote {out}")


def main() -> None:
    root = Path("/workspace")
    eval_path = root / "docs" / "evaluation" / "evaluation.json"
    if not eval_path.exists():
        from virtual_lab.pipeline import complete

        complete(root / "docs" / "evaluation", quick=False)
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    build(payload, root / "docs" / "Evaluation Report.pdf")


if __name__ == "__main__":
    main()
