from __future__ import annotations

import math

from virtual_lab.models import Pose, Scenario, wrap_angle
from virtual_lab.safety import collision


def command(pose: Pose, scenario: Scenario) -> tuple[float, float]:
    """Unicycle P-control toward the goal, slowing for heading error and arrival."""
    robot = scenario.robot
    dx = scenario.goal.x - pose.x
    dy = scenario.goal.y - pose.y
    dist = math.hypot(dx, dy)
    desired = math.atan2(dy, dx)
    heading_err = wrap_angle(desired - pose.theta)
    yaw = max(-robot.max_yaw_rate, min(robot.max_yaw_rate, 3.2 * heading_err))
    speed = scenario.speed * max(0.15, min(1.0, dist / 1.5))
    speed *= max(0.2, 1.0 - abs(heading_err) / math.pi)
    speed = min(speed, robot.max_speed)
    if dist < scenario.goal_tolerance * 0.6:
        speed = 0.0
        yaw = 0.0
    return speed, yaw


def step(pose: Pose, speed: float, yaw: float, dt: float) -> Pose:
    theta = pose.theta + yaw * dt
    return Pose(
        x=pose.x + speed * math.cos(theta) * dt,
        y=pose.y + speed * math.sin(theta) * dt,
        theta=wrap_angle(theta),
    )


def would_collide(pose: Pose, speed: float, yaw: float, dt: float, scenario: Scenario) -> bool:
    nxt = step(pose, speed, yaw, dt)
    return collision(nxt, scenario) is not None
