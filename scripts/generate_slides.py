#!/usr/bin/env python3
"""Company demo slides (16:9)."""

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

NAVY = colors.HexColor("#0F2C59")
TEAL = colors.HexColor("#1B6B93")
GOLD = colors.HexColor("#D4A017")
ACCENT = colors.HexColor("#C44536")
WHITE = colors.white
MUTED = colors.HexColor("#5C6B7A")
LIGHT = colors.HexColor("#F4F7FB")

W, H = 13.333 * inch, 7.5 * inch


def _bg(c, fill=NAVY):
    c.setFillColor(fill)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _footer(c, n, total=8):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 0.42 * inch, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, 0.42 * inch, W, 0.04 * inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Times-Roman", 9)
    c.drawString(0.5 * inch, 0.16 * inch, "Industrial Training Project  |  Virtual Robotics Testing")
    c.drawRightString(W - 0.5 * inch, 0.16 * inch, f"{n} / {total}")


def _header_bar(c, title):
    c.setFillColor(NAVY)
    c.rect(0, H - 0.85 * inch, W, 0.85 * inch, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 0.89 * inch, W, 0.05 * inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Times-Bold", 22)
    c.drawString(0.55 * inch, H - 0.55 * inch, title)


def _bullets(c, items, x, y, size=14, leading=26):
    c.setFont("Times-Roman", size)
    for item in items:
        c.setFillColor(TEAL)
        c.circle(x, y + 4, 3.2, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#1F2A33"))
        c.drawString(x + 14, y, item)
        y -= leading
    return y


def slide_title(c):
    _bg(c, NAVY)
    c.setFillColor(TEAL)
    c.rect(0, 0, 0.28 * inch, H, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0.28 * inch, H - 1.15 * inch, W, 0.08 * inch, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont("Times-Bold", 13)
    c.drawString(0.7 * inch, H - 1.55 * inch, "INDUSTRIAL TRAINING PROJECT")
    c.setFillColor(WHITE)
    c.setFont("Times-Bold", 36)
    c.drawString(0.7 * inch, H - 2.25 * inch, "Virtual Robotics Testing")
    c.setFont("Times-Italic", 18)
    c.setFillColor(colors.HexColor("#D7E4F0"))
    c.drawString(0.7 * inch, H - 2.7 * inch, "Catch failures in simulation. Deploy robots faster and safer.")
    c.setFont("Times-Roman", 14)
    c.drawString(0.7 * inch, 1.4 * inch, "Live demo  |  2D twin today  |  Gazebo / Isaac when installed")
    c.setFillColor(ACCENT)
    c.rect(0.28 * inch, 0.95 * inch, W, 0.08 * inch, fill=1, stroke=0)


def slide_problem(c):
    _bg(c, WHITE)
    _header_bar(c, "The problem")
    _footer(c, 2)
    _bullets(
        c,
        [
            "Hardware trial-and-error is slow, costly, and unsafe.",
            "Edge cases (blocked aisles, sensor dropouts) slip into production.",
            "Gazebo, Webots, and Isaac give physics -- not an automated test lab.",
            "Digital twins today optimize logistics more than robot control.",
        ],
        0.7 * inch,
        H - 1.6 * inch,
    )


def slide_solution(c):
    _bg(c, WHITE)
    _header_bar(c, "The platform")
    _footer(c, 3)
    _bullets(
        c,
        [
            "Digital twin of the warehouse + differential-drive robot.",
            "AI layer: adversarial what-if search, MCMC, grammar maps.",
            "Bayesian speed tuning and a CBF safety shield.",
            "Same scenarios run on twin, Gazebo/ROS 2, or Isaac Sim.",
        ],
        0.7 * inch,
        H - 1.6 * inch,
    )


def slide_demo(c):
    _bg(c, WHITE)
    _header_bar(c, "Live demo: what if the aisle is blocked?")
    _footer(c, 4)
    # two boxes
    for i, (title, color, note) in enumerate(
        [
            ("Open aisle", TEAL, "Baseline controller reaches the goal."),
            ("Blocked aisle", ACCENT, "No global planner -- timeout / stuck."),
        ]
    ):
        x = 0.6 * inch + i * 6.3 * inch
        c.setFillColor(LIGHT)
        c.roundRect(x, 1.1 * inch, 5.9 * inch, 4.9 * inch, 8, fill=1, stroke=0)
        c.setFillColor(color)
        c.roundRect(x, 5.5 * inch, 5.9 * inch, 0.5 * inch, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Times-Bold", 16)
        c.drawString(x + 0.25 * inch, 5.65 * inch, title)
        c.setFillColor(colors.HexColor("#1F2A33"))
        c.setFont("Times-Roman", 13)
        c.drawString(x + 0.25 * inch, 5.05 * inch, note)
        c.setFont("Times-Italic", 12)
        c.setFillColor(MUTED)
        c.drawString(x + 0.25 * inch, 1.4 * inch, "Open docs/demo/index.html to play the path.")


def slide_search(c):
    _bg(c, WHITE)
    _header_bar(c, "Adversarial search beats random")
    _footer(c, 5)
    rows = [("Method", "Failure rate"), ("Random crates", "30%"), ("MCMC", "55%"), ("Adversarial hill-climb", "90%")]
    y = H - 1.7 * inch
    for i, (a, b) in enumerate(rows):
        c.setFillColor(NAVY if i == 0 else (LIGHT if i % 2 == 0 else WHITE))
        c.rect(0.7 * inch, y - 8, 11.8 * inch, 0.48 * inch, fill=1, stroke=0)
        c.setFillColor(WHITE if i == 0 else NAVY)
        c.setFont("Times-Bold" if i == 0 else "Times-Roman", 16)
        c.drawString(0.9 * inch, y + 6, a)
        c.drawString(7.5 * inch, y + 6, b)
        y -= 0.55 * inch
    c.setFillColor(MUTED)
    c.setFont("Times-Italic", 12)
    c.drawString(0.7 * inch, 1.15 * inch, "20 trials on the open-aisle map. Adversarial search pushes a crate onto the lane.")


def slide_tune(c):
    _bg(c, WHITE)
    _header_bar(c, "Tuning and safety")
    _footer(c, 6)
    boxes = [
        ("+19.9%", "Throughput vs default speed", TEAL),
        ("CBF on", "Open aisle still succeeds, 0 violations", NAVY),
        ("3 engines", "twin / gazebo / isaac --backend", ACCENT),
    ]
    for i, (v, lab, col) in enumerate(boxes):
        x = 0.7 * inch + i * 4.1 * inch
        c.setFillColor(col)
        c.roundRect(x, 3.3 * inch, 3.8 * inch, 2.4 * inch, 10, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Times-Bold", 28)
        c.drawCentredString(x + 1.9 * inch, 4.7 * inch, v)
        c.setFont("Times-Roman", 12)
        c.drawCentredString(x + 1.9 * inch, 4.15 * inch, lab)
    _bullets(
        c,
        [
            "Bayesian optimization of cruise speed under the CBF shield.",
            "Domain-randomized Q-learning is the sim-to-sim proxy (friction 0.8 / 1.0 / 1.15).",
        ],
        0.7 * inch,
        2.6 * inch,
        size=13,
        leading=22,
    )


def slide_how(c):
    _bg(c, WHITE)
    _header_bar(c, "How to run")
    _footer(c, 7)
    lines = [
        "python3 -m pytest -q",
        "python3 -m virtual_lab demo",
        "python3 -m virtual_lab complete --out docs/evaluation",
        "python3 -m virtual_lab run --backend gazebo --scenario scenarios/open_aisle.json",
        "gz sim simulators/worlds/open_aisle.sdf",
    ]
    y = H - 1.7 * inch
    c.setFillColor(NAVY)
    c.roundRect(0.6 * inch, 1.2 * inch, 12.1 * inch, 5.1 * inch, 8, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont("Times-Bold", 12)
    c.drawString(0.9 * inch, H - 1.55 * inch, "TERMINAL")
    c.setFillColor(WHITE)
    c.setFont("Courier", 14)
    for line in lines:
        c.drawString(0.95 * inch, y - 0.15 * inch, "$  " + line)
        y -= 0.7 * inch


def slide_ask(c):
    _bg(c, NAVY)
    c.setFillColor(GOLD)
    c.setFont("Times-Bold", 13)
    c.drawString(0.7 * inch, H - 1.3 * inch, "ASK")
    c.setFillColor(WHITE)
    c.setFont("Times-Bold", 28)
    c.drawString(0.7 * inch, H - 2.1 * inch, "Approve the industrial-training MVP")
    c.setFont("Times-Roman", 16)
    c.setFillColor(colors.HexColor("#D7E4F0"))
    _bullets = [
        "Today: 2D twin, adversarial search, Bayesian tuning, demo + slides.",
        "Next on a workstation: Gazebo/ROS 2, then Isaac on GPU.",
        "Human review stays in the loop -- the platform never deploys itself.",
    ]
    y = H - 3.0 * inch
    c.setFont("Times-Roman", 16)
    for b in _bullets:
        c.drawString(0.7 * inch, y, b)
        y -= 0.45 * inch
    c.setFillColor(ACCENT)
    c.rect(0, 0.9 * inch, W, 0.08 * inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Times-Italic", 12)
    c.drawString(0.7 * inch, 0.45 * inch, "KPIs: failures per sim-hour  |  coverage vs manual  |  throughput  |  sim-to-real gap")


def build(path: str) -> None:
    c = canvas.Canvas(path, pagesize=(W, H))
    c.setTitle("VRTOP demo slides")
    c.setAuthor("Industrial Training Project")
    for fn in (slide_title, slide_problem, slide_solution, slide_demo, slide_search, slide_tune, slide_how, slide_ask):
        fn(c)
        c.showPage()
    c.save()
    print(f"Wrote {path}")


if __name__ == "__main__":
    build("/workspace/docs/Demo Slides.pdf")
