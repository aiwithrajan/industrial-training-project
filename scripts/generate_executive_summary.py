#!/usr/bin/env python3
"""Generate Executive Summary.pdf for the Virtual Robotics Testing platform."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
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
ROW_ALT = colors.HexColor("#EEF3F8")
WHITE = colors.white
LINE = colors.HexColor("#C9D4E0")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


class ColoredRule(Flowable):
    def __init__(self, width, color=TEAL, thickness=1.4):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 1, self.width, 1)


class GanttChart(Flowable):
    def __init__(self, width, height=78 * mm):
        super().__init__()
        self.width = width
        self.height = height
        self.tasks = [
            ("Simulator selection & setup", 0, 2, 0),
            ("Warehouse & robot modeling", 0, 2, 0),
            ("Basic navigation tests", 0.5, 2, 0),
            ("Adversarial scenario module", 2, 4, 1),
            ("Bayesian / EA tuning module", 2, 4, 1),
            ("Reporting dashboard MVP", 2.5, 4, 1),
            ("Reinforcement learning policy", 4, 5, 2),
            ("Sim-to-sim robustness tests", 4, 5, 2),
            ("Formal safety verification", 4.2, 5.5, 2),
            ("Final evaluation & reporting", 5, 6, 2),
        ]
        self.phases = [
            (0, 2, "Months 1–2: Setup", colors.HexColor("#1B6B93")),
            (2, 4, "Months 3–4: Core engines", colors.HexColor("#0F2C59")),
            (4, 6, "Months 5–6: Advanced features", colors.HexColor("#C44536")),
        ]
        self.bar_colors = [
            colors.HexColor("#1B6B93"),
            colors.HexColor("#0F2C59"),
            colors.HexColor("#C44536"),
        ]

    def draw(self):
        c = self.canv
        left = 58 * mm
        top = self.height - 8 * mm
        chart_w = self.width - left - 4 * mm
        row_h = 6.2 * mm
        months = 6

        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 9)
        c.drawString(0, top + 3.5 * mm, "Project timeline (6 months)")

        for i, label in enumerate(["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]):
            x = left + (i / months) * chart_w
            c.setFillColor(MUTED)
            c.setFont("Times-Roman", 7)
            c.drawCentredString(x + chart_w / months / 2, top + 0.5 * mm, label)
            c.setStrokeColor(LINE)
            c.setDash(1, 2)
            c.setLineWidth(0.3)
            c.line(x, 8 * mm, x, top - 1 * mm)
            c.setDash()

        c.setStrokeColor(LINE)
        c.line(left + chart_w, 8 * mm, left + chart_w, top - 1 * mm)

        for i, (name, start, end, phase) in enumerate(self.tasks):
            y = top - (i + 1) * row_h
            c.setFillColor(NAVY)
            c.setFont("Times-Roman", 7.2)
            c.drawRightString(left - 2.5 * mm, y + 1.6 * mm, name)
            x0 = left + (start / months) * chart_w
            x1 = left + (end / months) * chart_w
            c.setFillColor(self.bar_colors[phase])
            c.roundRect(x0, y + 0.8 * mm, max(x1 - x0, 2 * mm), 3.6 * mm, 1.4, fill=1, stroke=0)

        legend_y = 2.2 * mm
        x = left
        for start, end, label, col in self.phases:
            c.setFillColor(col)
            c.roundRect(x, legend_y, 4.5 * mm, 3 * mm, 1, fill=1, stroke=0)
            c.setFillColor(MUTED)
            c.setFont("Times-Roman", 6.5)
            c.drawString(x + 5.5 * mm, legend_y + 0.6 * mm, label)
            x += 48 * mm


class ArchitectureDiagram(Flowable):
    def __init__(self, width, height=92 * mm):
        super().__init__()
        self.width = width
        self.height = height

    def _box(self, c, x, y, w, h, title, body, fill, title_color=WHITE):
        c.setFillColor(fill)
        c.setStrokeColor(fill)
        c.roundRect(x, y, w, h, 3.2, fill=1, stroke=0)
        c.setFillColor(title_color)
        c.setFont("Times-Bold", 8)
        c.drawCentredString(x + w / 2, y + h - 11, title)
        c.setFillColor(WHITE if fill != LIGHT else NAVY)
        if fill == LIGHT:
            c.setFillColor(MUTED)
        c.setFont("Times-Roman", 6.6)
        for i, line in enumerate(body):
            c.drawCentredString(x + w / 2, y + h - 22 - i * 9, line)

    def _arrow(self, c, x1, y1, x2, y2, label=""):
        c.setStrokeColor(TEAL)
        c.setFillColor(TEAL)
        c.setLineWidth(1.1)
        c.line(x1, y1, x2, y2)
        ang = 0
        import math

        ang = math.atan2(y2 - y1, x2 - x1)
        size = 4
        c.saveState()
        c.translate(x2, y2)
        c.rotate(ang * 180 / math.pi)
        p = c.beginPath()
        p.moveTo(0, 0)
        p.lineTo(-size, 2.2)
        p.lineTo(-size, -2.2)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.restoreState()
        if label:
            c.setFillColor(ACCENT)
            c.setFont("Times-Italic", 6.5)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            c.drawCentredString(mx, my + 3, label)

    def draw(self):
        c = self.canv
        w = self.width
        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 9)
        c.drawString(0, self.height - 8, "System architecture")

        # layout
        bw, bh = 46 * mm, 22 * mm
        mid_x = w / 2
        lab_w = 62 * mm
        lab_h = 28 * mm
        lab_x = mid_x - lab_w / 2
        lab_y = 38 * mm

        self._box(
            c,
            2 * mm,
            self.height - 36 * mm,
            bw,
            bh,
            "Adversarial generator",
            ["Obstacle layout, lighting, noise", "AI agent / MCMC search"],
            ACCENT,
        )
        self._box(
            c,
            w - bw - 2 * mm,
            self.height - 36 * mm,
            bw,
            bh,
            "Training & optimization",
            ["RL / policy search", "Bayesian optimizer"],
            TEAL,
        )
        self._box(
            c,
            lab_x,
            lab_y,
            lab_w,
            lab_h,
            "Virtual lab (simulator)",
            ["Physics engine  ·  Policy / controller", "Sensor outputs  ·  Trajectories & events"],
            NAVY,
        )
        self._box(
            c,
            2 * mm,
            6 * mm,
            bw + 4 * mm,
            24 * mm,
            "Digital twin",
            ["Robot URDF & sensors", "Warehouse map  ·  Knowledge graph"],
            colors.HexColor("#244A7A"),
        )
        self._box(
            c,
            w - bw - 6 * mm,
            6 * mm,
            bw + 4 * mm,
            24 * mm,
            "Evaluation & reporting",
            ["Collision / CBF checker", "Metrics  ·  Visualization"],
            colors.HexColor("#8B3A32"),
        )

        self._arrow(c, 2 * mm + bw, self.height - 25 * mm, lab_x, lab_y + lab_h - 6, "perturbs")
        self._arrow(
            c,
            w - bw - 2 * mm,
            self.height - 25 * mm,
            lab_x + lab_w,
            lab_y + lab_h - 6,
            "trains",
        )
        self._arrow(c, 2 * mm + (bw + 4 * mm) / 2, 30 * mm, lab_x + 10 * mm, lab_y, "models")
        self._arrow(
            c,
            lab_x + lab_w - 10 * mm,
            lab_y,
            w - bw - 6 * mm + (bw + 4 * mm) / 2,
            30 * mm,
            "logs",
        )


def styles():
    ss = getSampleStyleSheet()
    ss.add(
        ParagraphStyle(
            "CoverKicker",
            fontName="Times-Bold",
            fontSize=9,
            textColor=GOLD,
            tracking=1.4,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            "CoverTitle",
            fontName="Times-Bold",
            fontSize=26,
            leading=30,
            textColor=WHITE,
            spaceAfter=10,
        )
    )
    ss.add(
        ParagraphStyle(
            "CoverSub",
            fontName="Times-Italic",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#D7E4F0"),
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            "H1",
            fontName="Times-Bold",
            fontSize=14,
            leading=18,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            "H2",
            fontName="Times-Bold",
            fontSize=11.5,
            leading=15,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    ss.add(
        ParagraphStyle(
            "Body",
            fontName="Times-Roman",
            fontSize=10,
            leading=13.4,
            textColor=colors.HexColor("#1F2A33"),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            "BulletBody",
            fontName="Times-Roman",
            fontSize=10,
            leading=13.2,
            textColor=colors.HexColor("#1F2A33"),
            alignment=TA_LEFT,
            leftIndent=12,
            firstLineIndent=-10,
            spaceAfter=3,
        )
    )
    ss.add(
        ParagraphStyle(
            "Caption",
            fontName="Times-Italic",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            "Footer",
            fontName="Times-Roman",
            fontSize=8,
            textColor=MUTED,
        )
    )
    ss.add(
        ParagraphStyle(
            "TableCell",
            fontName="Times-Roman",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1F2A33"),
        )
    )
    ss.add(
        ParagraphStyle(
            "TableHead",
            fontName="Times-Bold",
            fontSize=8,
            leading=10.5,
            textColor=WHITE,
        )
    )
    ss.add(
        ParagraphStyle(
            "Quote",
            fontName="Times-Italic",
            fontSize=10.5,
            leading=14.5,
            textColor=NAVY,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            "KPI",
            fontName="Times-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            alignment=TA_CENTER,
        )
    )
    ss.add(
        ParagraphStyle(
            "KPILabel",
            fontName="Times-Roman",
            fontSize=7.5,
            leading=9.5,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
    )
    ss.add(
        ParagraphStyle(
            "Ref",
            fontName="Times-Roman",
            fontSize=9,
            leading=11.5,
            textColor=colors.HexColor("#1F2A33"),
            leftIndent=14,
            firstLineIndent=-14,
            spaceAfter=2.5,
        )
    )
    return ss


def bullets(items, s):
    flow = [Paragraph(f"•  {item}", s["BulletBody"]) for item in items]
    flow.append(Spacer(1, 4))
    return flow


def kpi_row(s, triples):
    cells = []
    for value, label in triples:
        inner = Table(
            [[Paragraph(value, s["KPI"])], [Paragraph(label, s["KPILabel"])]],
            colWidths=[52 * mm],
        )
        inner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        cells.append(inner)
    t = Table([cells], colWidths=[58 * mm, 58 * mm, 58 * mm])
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def styled_table(header, rows, col_widths, s):
    data = [[Paragraph(h, s["TableHead"]) for h in header]]
    for row in rows:
        data.append([Paragraph(c, s["TableCell"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
        else:
            cmds.append(("BACKGROUND", (0, i), (-1, i), WHITE))
    t.setStyle(TableStyle(cmds))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 12 * mm, PAGE_W, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, PAGE_H - 12.6 * mm, PAGE_W, 1.6 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Times-Bold", 8)
    canvas.drawString(MARGIN, PAGE_H - 8 * mm, "VIRTUAL ROBOTICS TESTING & OPTIMIZATION PLATFORM")
    canvas.setFont("Times-Roman", 8)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 8 * mm, "Executive Summary")

    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 10 * mm, PAGE_W, 1.2 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(MARGIN, 4 * mm, "Industrial Training Project  ·  Confidential")
    canvas.drawRightString(PAGE_W - MARGIN, 4 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, 14 * mm, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(14 * mm, PAGE_H - 28 * mm, PAGE_W - 14 * mm, 4 * mm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(14 * mm, 42 * mm, PAGE_W - 14 * mm, 2.2 * mm, fill=1, stroke=0)

    canvas.setFillColor(GOLD)
    canvas.setFont("Times-Bold", 10)
    canvas.drawString(28 * mm, PAGE_H - 42 * mm, "INDUSTRIAL TRAINING PROJECT")
    canvas.setFillColor(WHITE)
    canvas.setFont("Times-Bold", 28)
    canvas.drawString(28 * mm, PAGE_H - 58 * mm, "Executive Summary")
    canvas.setFont("Times-Italic", 14)
    canvas.setFillColor(colors.HexColor("#D7E4F0"))
    canvas.drawString(28 * mm, PAGE_H - 70 * mm, "A Virtual Robotics Testing & Optimization Platform")

    y = PAGE_H - 96 * mm
    for line in [
        "Digital twins  ·  Adversarial failure search  ·  Sim-to-real robustness",
        "Warehouse, factory, and service-robot validation before hardware deployment",
    ]:
        canvas.setFont("Times-Roman", 11)
        canvas.drawString(28 * mm, y, line)
        y -= 16

    canvas.setFillColor(WHITE)
    canvas.setFont("Times-Bold", 10)
    canvas.drawString(28 * mm, 28 * mm, "Prepared for company review")
    canvas.setFont("Times-Roman", 10)
    canvas.drawString(28 * mm, 20 * mm, "Six-month MVP roadmap  ·  2026")
    canvas.restoreState()


def build():
    s = styles()
    out_docs = Path("/workspace/docs/Executive Summary.pdf")
    out_root = Path("/workspace/Executive Summary.pdf")
    out_docs.parent.mkdir(parents=True, exist_ok=True)
    out = out_docs

    story = []
    story.append(PageBreak())

    # Opening
    story.append(Paragraph("1. Executive overview", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Physical testing of warehouse robots is slow, costly, and risky. A Virtual Robotics "
            "Testing &amp; Optimization Platform addresses this by building detailed simulations "
            "(digital twins) of the robot and environment, then using AI to automatically generate "
            "and evaluate scenarios before real deployment. Unlike basic simulators (Gazebo, Webots, "
            "Isaac), the platform adds an intelligence layer: adversarial failure search, automated "
            "“what-if” scenario generation, domain-randomized training, and optimization of control "
            "parameters.",
            s["Body"],
        )
    )
    story.append(
        Paragraph(
            "NVIDIA and Exotec describe using digital twins to simulate and optimize warehouse fleets "
            "before deployment. This system similarly lets engineers ask “what if we drive 20% faster?” "
            "or “what if this sensor fails?” and get evidence-based answers without risking hardware.",
            s["Body"],
        )
    )
    story.append(
        kpi_row(
            s,
            [
                ("50%", "Estimated reduction in physical test cycles"),
                ("15%", "Target throughput gain from optimized parameters"),
                ("6 months", "MVP: digital twin → adversarial engine"),
            ],
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Key benefits include uncovering rare failure modes (adversarial search), optimizing "
            "performance (for example, finding the fastest safe speed), and ensuring safety and "
            "robustness via virtual verification. Target users are warehouse operators, factory "
            "automation teams, and service-robot integrators who must validate robot behaviors under "
            "many conditions. Primary metrics: failure-discovery rate, sim-to-real gap, test coverage, "
            "and compute cost.",
            s["Body"],
        )
    )

    story.append(Paragraph("2. Problem statement", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Challenges", s["H2"]))
    story.append(
        Paragraph(
            "Developers currently test robots by trial-and-error on hardware — time-consuming and "
            "dangerous. Edge cases (bad lighting, slippery floors, sensor glitches) are often missed, "
            "causing hidden failures in production.",
            s["Body"],
        )
    )
    story.append(Paragraph("Digital twin opportunity", s["H2"]))
    story.append(
        Paragraph(
            "Industries now build digital twins — virtual replicas of warehouses and factories — to "
            "plan and optimize operations. Existing twins mostly focus on logistics (fleet scheduling, "
            "layout) rather than robot control verification. This platform fills that gap as a virtual "
            "test lab with AI-driven analysis.",
            s["Body"],
        )
    )
    story.append(Paragraph("Gaps in existing tools", s["H2"]))
    story.append(
        Paragraph(
            "Common simulators provide high-fidelity physics, sensors, and graphics, but they lack "
            "automated testing workflows. None automatically generate adversarial scenarios or "
            "optimize robot policies.",
            s["Body"],
        )
    )
    story.extend(
        bullets(
            [
                "<b>Gazebo (ROS standard):</b> extensive robot models and free, but not designed for massive parallel RL or photorealistic rendering.",
                "<b>NVIDIA Isaac Sim:</b> GPU-accelerated, photorealistic simulation for ML training, with heavy GPU and proprietary constraints.",
                "<b>Webots:</b> easy world building and many sensors, but parallelizing large experiments is challenging.",
            ],
            s,
        )
    )
    story.append(Paragraph("Insight", s["H2"]))
    story.append(
        Paragraph(
            "Recent research on automatic robot failure synthesis shows that adversarial test "
            "generation, rare-event sampling, and property-based scenario methods can systematically "
            "find robot failures. Integrating these into a production platform is the novel contribution.",
            s["Body"],
        )
    )

    story.append(Paragraph("3. Novelty versus existing simulators", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 4))
    story.append(
        KeepTogether(
            [
                styled_table(
                    ["Simulator", "Strengths", "Limitations", "Best for"],
                    [
                        [
                            "Gazebo (ROS)",
                            "Open-source, huge community, many plugins and robot models",
                            "Slower GPU usage, limited parallelism, basic graphics",
                            "Functional tests: collision avoidance, basic navigation",
                        ],
                        [
                            "NVIDIA Isaac Sim",
                            "RTX ray tracing, accurate sensors, thousands of parallel robots for RL",
                            "Heavy GPU requirements; proprietary (on open PhysX)",
                            "Vision-based training at scale",
                        ],
                        [
                            "Webots (Cyberbotics)",
                            "Polished GUI, easy model creation, extensive documentation",
                            "Slower throughput; less RL community support",
                            "Teaching and rapid scene authoring",
                        ],
                    ],
                    [32 * mm, 50 * mm, 48 * mm, 44 * mm],
                    s,
                )
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "This platform’s novelty is an AI analytics layer on top of such simulators. Instead of "
            "only running scripted tests, it automatically crafts challenging scenarios and interprets "
            "results. A software knowledge graph of the robot and environment (robots, sensors, maps, "
            "tasks) drives scenario generation. An adversarial agent may place obstacles or tweak "
            "lighting to maximize risk — shifting testing from manual scripts to automated search.",
            s["Body"],
        )
    )
    story.append(
        Paragraph(
            "Combining simulation data with formal and statistical methods (control barrier functions, "
            "Bayesian optimization) yields safety margins and optimal parameters rather than engineer "
            "guesswork. Digital twin + AI-driven scenario search + optimization is beyond what any "
            "single existing simulator provides.",
            s["Body"],
        )
    )

    story.append(Paragraph("4. Target users and industrial use-cases", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "Enterprises deploying mobile robots in warehouses and factories, or autonomous service "
            "robots (hospitality, healthcare). Typical users: robotics engineers, QA teams, and system "
            "integrators.",
            s["Body"],
        )
    )
    story.extend(
        bullets(
            [
                "<b>Warehousing (fulfillment centers):</b> pick, pack, and carry goods. Ensure collision-free navigation among dynamic obstacles, reliability under sensor noise, and compatibility with fleet management. Example: simulate 20 forklifts doing inventory, then test “what if aisle 5 becomes blocked” or optimize speed profiles for throughput.",
                "<b>Factory automation:</b> mobile manipulators on an assembly line. Virtually test a new configuration (arm mounting, sensor placement) and identify failing cases (incomplete grasp due to lighting) before building hardware.",
                "<b>Service robots (hotels, hospitals):</b> delivery or cleaning in complex indoor environments. Generate emergency scenarios (obstacle, low battery) and verify safe fallback actions virtually.",
            ],
            s,
        )
    )
    story.append(
        Paragraph(
            "Exotec notes that virtual warehouse models enable pre-testing of conveyor flows and robot "
            "control logic before installation. NVIDIA confirms that a simulation-first approach "
            "validates robot fleets’ coordination in dynamic environments. This work adds robust "
            "what-if and failure analysis on top of that foundation.",
            s["Body"],
        )
    )

    story.append(Paragraph("5. Key research questions and dimensions", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "Each dimension is a core platform capability, with data needs, methods, and metrics.",
            s["Body"],
        )
    )

    dims = [
        (
            "5.1 Adversarial failure discovery — “What breaks?”",
            "What simulation conditions cause the robot to fail (collide, deviate, or miss tasks)?",
            "<b>Data:</b> simulator runs (trajectories, sensor logs), failure labels (collisions, deadlocks), environment parameters, and optional formal hazard specs.",
            "<b>Methods:</b> adversarial RL (a red-team agent that perturbs the environment); formal test generation (control barrier functions to find hard obstacles); Bayesian optimization / MCMC to sample worst-case parameters; differentiable simulation for gradients; property-based scenario enumerators.",
            "<b>Metrics:</b> failure discovery rate, coverage (diversity of failure modes), worst-case cost reduction (safety-margin improvement), false positives, compute time per discovered fault.",
        ),
        (
            "5.2 Automated scenario generation — “How to test?”",
            "How to systematically generate diverse test scenarios (layouts, dynamics, light/sensor conditions)?",
            "<b>Data:</b> warehouse maps, robot models, task definitions, scenario templates, hazard ontologies.",
            "<b>Methods:</b> grammar-based combinatorial world generation; generative models (GANs or LLMs) for scene variations; ontology-driven adversarial scenarios; heuristic random search; executable test-scenario and property-testing frameworks.",
            "<b>Metrics:</b> scenario novelty vs seed cases, parameter-space coverage, rate of new failure modes, physical realism, user effort saved versus manual design.",
        ),
        (
            "5.3 Sim-to-real transfer and domain randomization — “Reality gap”",
            "How to ensure controllers trained or proven safe in simulation will perform in the real world?",
            "<b>Data:</b> if a real robot is available, sensor/actuator logs for calibration; otherwise physics parameter ranges.",
            "<b>Methods:</b> domain randomization of textures, masses, friction, and noise; system identification via Bayesian inference; pixel-level randomization for vision; multimodal mix of sim and synthetic augmentation; sim-to-sim ensembles; robust RL (RARL-like) for worst-case adaptation.",
            "<b>Metrics:</b> sim-to-real gap (success rate / error difference vs later real test), domain-gap feature distributions, sample efficiency, adherence to known physics bounds. Near-term proxy: compare two simulator configurations as stand-ins for “reality.”",
        ),
        (
            "5.4 Digital twin fidelity",
            "How accurate must the simulation be? Which aspects of reality (friction, latency) need precise modeling?",
            "<b>Data:</b> CAD warehouse models, sensor specifications, system logs.",
            "<b>Methods:</b> differentiable physics (gradient / MCMC parameter inference); multi-fidelity modeling (learned replacements for slow subsystems); formal uncertainty with confidence intervals on sim predictions.",
            "<b>Metrics:</b> calibration error vs any later ground truth; sensitivity of outcomes to parameter variation; fidelity–reward tradeoff (performance lost when simplifying the sim for speed).",
        ),
        (
            "5.5 Safety verification",
            "Does the system guarantee safety constraints (no collisions, stay in bounds)?",
            "<b>Data:</b> safety-rule specifications (e.g. keep 0.5 m from obstacles) plus simulation traces.",
            "<b>Methods:</b> control barrier functions or model checking on the digital twin; adversarial verification that no generated scenario breaches safety; shielding with pre-computed safe fallbacks.",
            "<b>Metrics:</b> safety margin (minimum obstacle distance), violation rate, verification coverage (percent of state space certified).",
        ),
        (
            "5.6 Control / policy optimization — “What is best?”",
            "What robot parameters (speed, PID gains, waypoints) maximize performance under constraints?",
            "<b>Data:</b> sim performance (completion time, energy, error) and parametric configurations.",
            "<b>Methods:</b> Bayesian optimization or evolutionary algorithms for continuous control parameters; reinforcement learning with reward shaping; gradient-based controller optimization if the sim is differentiable; meta-learning for task adaptation.",
            "<b>Metrics:</b> KPI lift vs baseline (throughput, travel time, energy); sample efficiency; robustness (sensitivity to parameter change).",
        ),
    ]
    for title, q, data, methods, metrics in dims:
        block = [
            Paragraph(title, s["H2"]),
            Paragraph(f"<i>Question:</i> {q}", s["Body"]),
            Paragraph(data, s["Body"]),
            Paragraph(methods, s["Body"]),
            Paragraph(metrics, s["Body"]),
        ]
        story.extend(block)

    story.append(Paragraph("6. Implementation roadmap (6 months)", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Months 1–2 — MVP", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Simulator and digital twin:</b> Gazebo with ROS 2; simple warehouse and differential-drive robot (e.g. TurtleBot); CAD/map load; LiDAR and camera.",
                "<b>Virtual lab basics:</b> navigate A→B with obstacle avoidance.",
                "<b>Data logging:</b> trajectory logs and performance metrics.",
                "<b>Verification:</b> rudimentary safety checks (collision detect).",
            ],
            s,
        )
    )
    story.append(Paragraph("Months 3–4 — Core engines", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Adversarial scenario generator:</b> perturb obstacle placement, lighting, and friction; start with random search plus heuristics (e.g. gradient on obstacle positions to cause failure).",
                "<b>Failure discovery:</b> batch simulations, logged failure scenarios, visualized common patterns.",
                "<b>Parameter tuning:</b> Bayesian optimization (BOHB or scikit-optimize) for speed and control gains, minimizing travel time under safety constraints.",
                "<b>UI / reporting MVP:</b> dashboard of scenarios and impacts (tables and plots).",
            ],
            s,
        )
    )
    story.append(Paragraph("Month 5 — Learning and robustness", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>RL loop:</b> Stable-Baselines3 navigation/policy in sim with domain randomization (textures, noise).",
                "<b>Sim-to-sim transfer:</b> compare policy performance under varied friction and similar shifts.",
                "<b>Formal safety tests:</b> simple CBFs or rule-checkers on navigation safety margin under discovered scenarios.",
            ],
            s,
        )
    )
    story.append(Paragraph("Month 6 — Advanced search and delivery", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Advanced adversarial search:</b> gradient-based or MCMC failure search (Metropolis sampling as in Dawson et al.).",
                "<b>Synthetic scenarios:</b> grammar/ontology for new map layouts.",
                "<b>Evaluation:</b> formalize metrics (failure detection rate, optimization lift) and run experiments.",
                "<b>Documentation:</b> final report and interactive demo (slides or notebook).",
            ],
            s,
        )
    )
    story.append(Paragraph("Milestones", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>End of month 2:</b> functional simulator with logging; basic scenario analysis.",
                "<b>End of month 4:</b> adversarial failure cases identified; tuning engine yields a performance boost (target 10–20% faster routing).",
                "<b>End of month 6:</b> RL policy trained in sim; robust against domain shifts; comprehensive test reports.",
            ],
            s,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        KeepTogether(
            [
                GanttChart(174 * mm),
                Paragraph("Figure 1. Six-month delivery timeline.", s["Caption"]),
            ]
        )
    )

    story.append(
        KeepTogether(
            [
                Paragraph("7. System architecture", s["H1"]),
                ColoredRule(174 * mm, TEAL),
                Spacer(1, 3),
                Paragraph(
                    "Each component interfaces with the virtual lab (simulator) and the digital twin knowledge base.",
                    s["Body"],
                ),
                ArchitectureDiagram(174 * mm),
                Paragraph("Figure 2. High-level platform architecture.", s["Caption"]),
            ]
        )
    )
    story.extend(
        bullets(
            [
                "<b>Digital twin:</b> graph of robot parameters, warehouse layout, and prior scenario data.",
                "<b>Virtual lab:</b> chosen simulator (Gazebo / Isaac) runs physics and kinematics from twin models.",
                "<b>Scenario generator:</b> AI module choosing adversarial parameters (obstacles, sensor noise) to maximize risk.",
                "<b>Training / optimization engine:</b> RL or parameter search for controllers, policies, or settings.",
                "<b>Evaluation and reporting:</b> monitors collisions and rule violations (e.g. CBFs), computes metrics, and feeds an engineer dashboard.",
            ],
            s,
        )
    )

    story.append(Paragraph("8. Algorithms and approaches", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 4))
    story.append(
        styled_table(
            ["Approach", "Category", "Pros", "Cons", "Compute"],
            [
                [
                    "Reinforcement learning (PPO, SAC)",
                    "Policy learning",
                    "Learns complex control; robust with enough data",
                    "Sample-inefficient; can overfit simulation",
                    "High (GPU)",
                ],
                [
                    "Domain randomization",
                    "Sim-to-real",
                    "Improves real-world robustness; no real data required",
                    "Many variations; synthetic noise may not match reality",
                    "Medium",
                ],
                [
                    "Bayesian optimization",
                    "Parameter tuning",
                    "Sample-efficient for low-dimensional control tuning",
                    "Local optima; no temporal aspect",
                    "Low–med",
                ],
                [
                    "Gradient-based (DiffSim)",
                    "Parameter tuning",
                    "Fast convergence if the simulation is differentiable",
                    "Auto-diff sims are rare; model gradients can be unrealistic",
                    "Low",
                ],
                [
                    "Evolutionary algorithms",
                    "Parameter search",
                    "Simple to implement; explores a broad space",
                    "Many evaluations; slow convergence",
                    "High",
                ],
                [
                    "Adversarial RL (RARL)",
                    "Safety / robustness",
                    "Finds worst-case perturbations; improves worst-case safety",
                    "Training can be unstable and slow",
                    "Very high",
                ],
                [
                    "Formal verification (CBF / LTL)",
                    "Safety check",
                    "Guarantees under assumptions; finds boundary cases",
                    "Hard to scale; can be conservative",
                    "Medium",
                ],
                [
                    "MCMC / Bayesian inference",
                    "Failure synthesis",
                    "Samples high-risk scenarios; posterior over failure modes",
                    "Needs differentiable sim or a surrogate",
                    "High",
                ],
                [
                    "Black-box testing (random search)",
                    "Baseline testing",
                    "Simple; finds obvious failures",
                    "Misses rare cases; inefficient sampling",
                    "Low",
                ],
            ],
            [38 * mm, 28 * mm, 42 * mm, 42 * mm, 24 * mm],
            s,
        )
    )
    story.append(
        Paragraph(
            "See Dawson et al. (2023) for Bayesian failure sampling as a reference method.",
            s["Caption"],
        )
    )

    story.append(Paragraph("9. Experiment design", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Four core experiments evaluate the platform.", s["Body"]))

    story.append(Paragraph("9.1 Adversarial failure search", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Setup:</b> simulated 2D warehouse with random shelf obstacles; robot has a navigation policy.",
                "<b>Input:</b> vary obstacle positions and sensor noise via adversarial RL or MCMC.",
                "<b>Control:</b> random scenario sampling.",
                "<b>Measure:</b> number of distinct failure scenarios in N trials; minimal perturbation needed to cause failure.",
                "<b>Success:</b> adversarial method finds critical failures significantly faster than random (e.g. 90% of worst-case faults vs 50% with random).",
            ],
            s,
        )
    )
    story.append(Paragraph("9.2 Parameter optimization", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Setup:</b> robot delivers items across warehouse aisles; speed and acceleration limits are tunable.",
                "<b>Method:</b> Bayesian optimization for speeds that maximize throughput with no collisions.",
                "<b>Control:</b> default / manual parameters.",
                "<b>Measure:</b> throughput (items/hr), collision count, time to converge.",
                "<b>Success:</b> &gt;10–20% throughput increase with zero collisions, found in fewer simulations than grid search.",
            ],
            s,
        )
    )
    story.append(Paragraph("9.3 Sim-to-real validation (hypothetical)", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Approach:</b> after simulation, port the learned policy to a real differential-drive robot in a small test maze if hardware is available.",
                "<b>Design:</b> same map layout; compare time-to-goal and safety violations.",
                "<b>Controls:</b> if no robot, use two simulators (Gazebo vs Isaac) as discrepancy proxies.",
                "<b>Success:</b> real-world (or second-sim) performance within a defined band of simulation metrics — a minimal sim-to-real gap.",
            ],
            s,
        )
    )
    story.append(Paragraph("9.4 Sensor degradation robustness", s["H2"]))
    story.extend(
        bullets(
            [
                "<b>Setup:</b> introduce failures such as lost LiDAR or added camera noise in simulation.",
                "<b>Method:</b> compare a policy trained with vs without adversarial sensor noise.",
                "<b>Measure:</b> percent of tasks completed; collision rate under degraded sensors.",
                "<b>Success:</b> adversarial-noise training sustains high performance (&gt;80% success) under dropouts, while the baseline fails more often.",
            ],
            s,
        )
    )

    story.append(Paragraph("10. Tech stack and tools", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.extend(
        bullets(
            [
                "<b>Simulator:</b> Gazebo (ROS 2) for the MVP; optionally NVIDIA Isaac Sim or PyBullet for high-speed parallel runs.",
                "<b>Robot platform:</b> differential-drive URDF (TurtleBot3 or custom); ROS 2 Navigation stack as baseline.",
                "<b>AI / ML:</b> Python, ROS 2, Gymnasium, Stable-Baselines3 or RLlib, PyTorch / TensorFlow.",
                "<b>Optimization:</b> scikit-optimize or BayesianOptimization; DEAP / Optuna for evolutionary search.",
                "<b>Data and config:</b> JSON/YAML scenario parameters; SQLite or PostgreSQL for logs.",
                "<b>Visualization:</b> Dash/Plotly or ROS RViz for playback; Grafana for metrics.",
                "<b>Infrastructure:</b> Docker for reproducibility; optional Kubernetes; GPU if using Isaac Gym or heavy RL.",
            ],
            s,
        )
    )

    story.append(Paragraph("11. Datasets and benchmarks", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.extend(
        bullets(
            [
                "<b>Simulators:</b> Gazebo (Ignition), Webots, NVIDIA Isaac/Gym, PyBullet — ROS 2 or Gym interfaces.",
                "<b>Benchmarks:</b> ROS Navigation2 2D maze; Gazebo tracks.",
                "<b>Data:</b> synthetic runs for training; if available, open datasets such as Amazon ARM (pick-and-place) for vision.",
                "<b>Sensors:</b> synthetic LiDAR/camera with realistic noise models.",
                "<b>References:</b> NVIDIA Omniverse Mega-BLUEPRINT for fleet testing; published safe/unsafe object-placement scenarios.",
            ],
            s,
        )
    )

    story.append(Paragraph("12. Risks and considerations", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.extend(
        bullets(
            [
                "<b>Reality gap:</b> over-reliance on simulation can miss real nuances. Mitigate with domain randomization and calibration.",
                "<b>Adversarial catastrophe:</b> autonomous generation might produce unrealistic scenarios. Constrain the generator to physically plausible conditions.",
                "<b>Compute cost:</b> large-scale simulation (especially RL) is expensive. Prioritize efficient search and GPU / parallel clusters.",
                "<b>Ethics and safety:</b> policies tested in sim must still be treated as unsafe until reviewed. Highlight uncertainties. The platform must not autonomously deploy changes; always require human review.",
                "<b>Data privacy:</b> no personal data; primarily physical models.",
            ],
            s,
            )
        )

    story.append(Paragraph("13. Pitch and KPIs for company approval", s["H1"]))
    story.append(ColoredRule(174 * mm, TEAL))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Elevator pitch", s["H2"]))
    story.append(
        Paragraph(
            "“Our platform creates a virtual twin of your robot system and uses AI to systematically "
            "discover failures and optimize performance in simulation, so you can deploy robots faster, "
            "safer, and more efficiently.”",
            s["Quote"],
        )
    )
    story.append(Paragraph("Value proposition", s["H2"]))
    story.append(
        Paragraph(
            "Reduce expensive on-robot testing and downtime by catching issues in simulation first. "
            "Unlike conventional simulators, the platform generates adversarial stress tests and learns "
            "optimal settings automatically — insight and confidence before deployment.",
            s["Body"],
        )
    )
    story.append(Paragraph("Measurable KPIs", s["H2"]))
    story.extend(
        bullets(
            [
                "Number of critical failures discovered per sim-hour (higher is better).",
                "Simulated mission success rate (target &gt;95%) with the optimized policy.",
                "Reduction in simulated test cases needed versus manual design for the same coverage.",
                "Throughput improvement (% increase over baseline).",
                "Downstream: reduction in real-world failures after deployment (tracked post-demo).",
            ],
            s,
        )
    )

    refs = [
        "ESS ENN Associates, “Robot Simulation &amp; Digital Twins — Virtual Testing Before Deployment,” Apr. 2026.",
        "NVIDIA Developer Blog, “Simulating Robots in Industrial Facility Digital Twins,” Mar. 2025.",
        "Exotec, “Digital Twin for Warehouses,” Feb. 2024.",
        "Kaup et al., “A Review of Nine Physics Engines for Reinforcement Learning Research,” arXiv, 2024.",
        "Baptista, “Simulation Tools,” PhD blog, Oct. 2023.",
        "EmergentMind, “Automatic Robot Failure Synthesis” (topic summary), Dec. 2025.",
        "AwesomeSim2Real surveys of sim-to-real techniques, 2024.",
        "“Learning Robot Safety Policies via Adversarial Synthetic Scenarios,” arXiv, 2024.",
        "Pitkevich &amp; Makarov, “Survey on Sim-to-Real Transfer for Robotic Manipulation,” IEEE SISY, 2024.",
        "Robot Operating System (ROS) documentation; Gazebo and Isaac Sim product documentation.",
        "Dawson et al., Bayesian / MCMC failure sampling in simulation, 2023.",
    ]
    refs_block = [
        Paragraph("14. References", s["H1"]),
        ColoredRule(174 * mm, TEAL),
        Spacer(1, 4),
    ]
    refs_block.extend(Paragraph(f"[{i}] {r}", s["Ref"]) for i, r in enumerate(refs, 1))
    story.append(KeepTogether(refs_block))

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=20 * mm,
        bottomMargin=16 * mm,
        title="Executive Summary — Virtual Robotics Testing & Optimization Platform",
        author="Industrial Training Project",
        subject="Company-facing executive summary of a virtual robotics testing platform",
    )

    def first_page(canvas, doc_):
        cover_page(canvas, doc_)

    def later_pages(canvas, doc_):
        header_footer(canvas, doc_)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    import shutil

    shutil.copy(out_docs, out_root)
    print(f"Wrote {out_docs}")
    print(f"Wrote {out_root}")


if __name__ == "__main__":
    build()
