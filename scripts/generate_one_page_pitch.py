#!/usr/bin/env python3
"""Generate a one-page company pitch PDF."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0F2C59")
TEAL = colors.HexColor("#1B6B93")
ACCENT = colors.HexColor("#C44536")
GOLD = colors.HexColor("#D4A017")
LIGHT = colors.HexColor("#F4F7FB")
MUTED = colors.HexColor("#5C6B7A")
WHITE = colors.white
LINE = colors.HexColor("#C9D4E0")

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm


class Rule(Flowable):
    def __init__(self, width, color=GOLD, thickness=2):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 1

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.thickness, fill=1, stroke=0)


def styles():
    return {
        "kicker": ParagraphStyle(
            "kicker",
            fontName="Times-Bold",
            fontSize=8.5,
            textColor=GOLD,
            tracking=1.2,
            spaceAfter=4,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Times-Bold",
            fontSize=20,
            leading=24,
            textColor=WHITE,
            spaceAfter=4,
        ),
        "sub": ParagraphStyle(
            "sub",
            fontName="Times-Italic",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#D7E4F0"),
            spaceAfter=0,
        ),
        "h": ParagraphStyle(
            "h",
            fontName="Times-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY,
            spaceBefore=7,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Times-Roman",
            fontSize=9.5,
            leading=12.4,
            textColor=colors.HexColor("#1F2A33"),
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "quote": ParagraphStyle(
            "quote",
            fontName="Times-Italic",
            fontSize=10.5,
            leading=14,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "kpi": ParagraphStyle(
            "kpi",
            fontName="Times-Bold",
            fontSize=14,
            leading=16,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "kpil": ParagraphStyle(
            "kpil",
            fontName="Times-Roman",
            fontSize=7.5,
            leading=9.5,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Times-Roman",
            fontSize=9.2,
            leading=12,
            textColor=colors.HexColor("#1F2A33"),
            leftIndent=10,
            firstLineIndent=-10,
            spaceAfter=2.5,
        ),
        "tiny": ParagraphStyle(
            "tiny",
            fontName="Times-Roman",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }


def kpi_boxes(s, items):
    cells = []
    for value, label in items:
        inner = Table(
            [[Paragraph(value, s["kpi"])], [Paragraph(label, s["kpil"])]],
            colWidths=[42 * mm],
        )
        inner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        cells.append(inner)
    t = Table([cells], colWidths=[45 * mm] * 4)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 42 * mm, PAGE_W, 42 * mm, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, 8 * mm, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(8 * mm, PAGE_H - 42.8 * mm, PAGE_W - 8 * mm, 2.2 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont("Times-Bold", 9)
    canvas.drawString(MARGIN + 4 * mm, PAGE_H - 14 * mm, "INDUSTRIAL TRAINING PROJECT")
    canvas.setFillColor(WHITE)
    canvas.setFont("Times-Bold", 18)
    canvas.drawString(MARGIN + 4 * mm, PAGE_H - 24 * mm, "Virtual Robotics Testing & Optimization")
    canvas.setFillColor(colors.HexColor("#D7E4F0"))
    canvas.setFont("Times-Italic", 11)
    canvas.drawString(
        MARGIN + 4 * mm,
        PAGE_H - 33 * mm,
        "Catch failures in simulation. Deploy robots faster, safer, cheaper.",
    )
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, 11 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(8 * mm, 11 * mm, PAGE_W - 8 * mm, 1.4 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(MARGIN + 2 * mm, 4.5 * mm, "Industrial Training Project  ·  Company review")
    canvas.drawRightString(PAGE_W - MARGIN, 4.5 * mm, "One-page pitch  ·  2026")
    canvas.restoreState()


def build():
    s = styles()
    out = Path("/workspace/docs/One-Page Pitch.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    story = []
    story.append(Paragraph("Elevator pitch", s["h"]))
    story.append(Rule(174 * mm, TEAL, 1.2))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "“Our platform creates a virtual twin of your robot system and uses AI to systematically "
            "discover failures and optimize performance in simulation, so you can deploy robots faster, "
            "safer, and more efficiently.”",
            s["quote"],
        )
    )

    story.append(Paragraph("Value proposition", s["h"]))
    story.append(Rule(174 * mm, TEAL, 1.2))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "Physical testing of warehouse and service robots is slow, costly, and risky. Existing "
            "simulators (Gazebo, Webots, Isaac) provide physics — not an automated test lab. We add "
            "an intelligence layer: adversarial “what-if” search, domain randomization, and control "
            "optimization on a digital twin, so issues are found before hardware is at risk.",
            s["body"],
        )
    )

    story.append(Spacer(1, 3))
    story.append(
        kpi_boxes(
            s,
            [
                ("50%", "Fewer physical test cycles (estimate)"),
                ("15%", "Throughput gain from tuned parameters"),
                ("&gt;95%", "Target simulated mission success"),
                ("6 mo", "MVP: twin → adversarial engine"),
            ],
        )
    )

    story.append(Paragraph("Who it is for", s["h"]))
    story.append(Rule(174 * mm, TEAL, 1.2))
    story.append(Spacer(1, 2))
    for item in [
        "<b>Warehousing:</b> fleets of pick/pack/carry robots — blocked aisles, sensor noise, speed vs safety.",
        "<b>Factory automation:</b> mobile manipulators — new arm/sensor layouts before you build them.",
        "<b>Service robots:</b> hotels and hospitals — emergency fallbacks (obstacle, low battery) in software first.",
    ]:
        story.append(Paragraph(f"•  {item}", s["bullet"]))

    story.append(Paragraph("What makes it different", s["h"]))
    story.append(Rule(174 * mm, TEAL, 1.2))
    story.append(Spacer(1, 2))
    for item in [
        "Automatically generates adversarial stress tests instead of only running scripted scenes.",
        "Knowledge graph of robot, map, sensors, and tasks drives scenario search.",
        "Bayesian / RL optimization finds safe speed and gains; CBFs check safety margins.",
        "Human review is required — the platform never deploys changes on its own.",
    ]:
        story.append(Paragraph(f"•  {item}", s["bullet"]))

    story.append(Paragraph("Ask / next step", s["h"]))
    story.append(Rule(174 * mm, TEAL, 1.2))
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "Approve a six-month industrial-training MVP: Gazebo/ROS 2 digital twin (months 1–2), "
            "adversarial generator and Bayesian tuning (months 3–4), RL robustness and safety "
            "reports (months 5–6). Immediate proof: a 2D virtual lab that logs trajectories, "
            "detects collisions, and compares baseline vs blocked-aisle scenarios.",
            s["body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "KPIs to track: failures found per sim-hour  ·  coverage vs manual tests  ·  "
            "throughput vs baseline  ·  sim-to-real gap after demo.",
            s["tiny"],
        )
    )

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=MARGIN + 4 * mm,
        rightMargin=MARGIN,
        topMargin=46 * mm,
        bottomMargin=16 * mm,
        title="One-Page Pitch — Virtual Robotics Testing & Optimization",
        author="Industrial Training Project",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Wrote {out}")


if __name__ == "__main__":
    build()
