from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    theta: float = 0.0

    def distance_to(self, other: Pose) -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def jitter(self, rng, sigma: float) -> Pose:
        if sigma <= 0:
            return self
        return Pose(
            self.x + rng.gauss(0, sigma),
            self.y + rng.gauss(0, sigma),
            wrap_angle(self.theta + rng.gauss(0, sigma * 0.4)),
        )


@dataclass(frozen=True)
class AABB:
    x0: float
    y0: float
    x1: float
    y1: float

    def inflate(self, r: float) -> AABB:
        return AABB(self.x0 - r, self.y0 - r, self.x1 + r, self.y1 + r)

    def shift(self, dx: float, dy: float) -> AABB:
        return AABB(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def contains_point(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1

    def intersects_circle(self, x: float, y: float, radius: float) -> bool:
        cx = min(max(x, self.x0), self.x1)
        cy = min(max(y, self.y0), self.y1)
        return math.hypot(x - cx, y - cy) <= radius

    def as_list(self) -> list[float]:
        return [self.x0, self.y0, self.x1, self.y1]


@dataclass
class Warehouse:
    width: float
    height: float
    obstacles: Sequence[AABB] = field(default_factory=tuple)

    def in_bounds(self, x: float, y: float, radius: float) -> bool:
        return radius <= x <= self.width - radius and radius <= y <= self.height - radius


@dataclass
class Robot:
    radius: float = 0.35
    max_speed: float = 1.2
    max_yaw_rate: float = 2.0
    wheelbase: float = 0.3


@dataclass
class Scenario:
    name: str
    warehouse: Warehouse
    start: Pose
    goal: Pose
    robot: Robot = field(default_factory=Robot)
    dt: float = 0.05
    max_time: float = 60.0
    goal_tolerance: float = 0.45
    speed: float = 0.9
    notes: str = ""
    friction: float = 1.0
    sensor_noise: float = 0.0
    heading_gain: float = 3.2
    use_cbf: bool = False
    cbf_margin: float = 0.55
    seed: int = 0

    def evolved(self, **kwargs) -> Scenario:
        return replace(self, **kwargs)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "notes": self.notes,
            "warehouse": {
                "width": self.warehouse.width,
                "height": self.warehouse.height,
                "obstacles": [o.as_list() for o in self.warehouse.obstacles],
            },
            "start": [self.start.x, self.start.y, self.start.theta],
            "goal": [self.goal.x, self.goal.y, self.goal.theta],
            "speed": self.speed,
            "dt": self.dt,
            "max_time": self.max_time,
            "goal_tolerance": self.goal_tolerance,
            "friction": self.friction,
            "sensor_noise": self.sensor_noise,
            "heading_gain": self.heading_gain,
            "use_cbf": self.use_cbf,
            "cbf_margin": self.cbf_margin,
            "robot": {
                "radius": self.robot.radius,
                "max_speed": self.robot.max_speed,
                "max_yaw_rate": self.robot.max_yaw_rate,
            },
        }

    @staticmethod
    def from_dict(data: dict) -> Scenario:
        wh = data["warehouse"]
        obstacles = tuple(AABB(*row) for row in wh.get("obstacles", []))
        start = Pose(*data["start"])
        goal = Pose(*data["goal"])
        robot_cfg = data.get("robot", {})
        robot = Robot(**robot_cfg) if robot_cfg else Robot()
        return Scenario(
            name=data.get("name", "unnamed"),
            warehouse=Warehouse(wh["width"], wh["height"], obstacles),
            start=start,
            goal=goal,
            robot=robot,
            dt=float(data.get("dt", 0.05)),
            max_time=float(data.get("max_time", 60.0)),
            goal_tolerance=float(data.get("goal_tolerance", 0.45)),
            speed=float(data.get("speed", 0.9)),
            notes=data.get("notes", ""),
            friction=float(data.get("friction", 1.0)),
            sensor_noise=float(data.get("sensor_noise", 0.0)),
            heading_gain=float(data.get("heading_gain", 3.2)),
            use_cbf=bool(data.get("use_cbf", False)),
            cbf_margin=float(data.get("cbf_margin", 0.55)),
            seed=int(data.get("seed", 0)),
        )

    @staticmethod
    def load(path: str | Path) -> Scenario:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return Scenario.from_dict(payload)


def wrap_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def iter_waypoints(start: Pose, goal: Pose, n: int = 8) -> Iterable[Pose]:
    for i in range(1, n + 1):
        t = i / n
        yield Pose(start.x + t * (goal.x - start.x), start.y + t * (goal.y - start.y))
