from __future__ import annotations

import math

from virtual_lab.models import Pose, Scenario, wrap_angle
from virtual_lab.safety import barrier_value, collision, nearest_repulsion


def command(pose: Pose, scenario: Scenario) -> tuple[float, float]:
    """Unicycle P-control toward the goal, slowing for heading error and arrival."""
    robot = scenario.robot
    dx = scenario.goal.x - pose.x
    dy = scenario.goal.y - pose.y
    dist = math.hypot(dx, dy)
    desired = math.atan2(dy, dx)
    heading_err = wrap_angle(desired - pose.theta)
    yaw = max(-robot.max_yaw_rate, min(robot.max_yaw_rate, scenario.heading_gain * heading_err))
    speed = scenario.speed * max(0.15, min(1.0, dist / 1.5))
    speed *= max(0.2, 1.0 - abs(heading_err) / math.pi)
    speed = min(speed, robot.max_speed)
    if dist < scenario.goal_tolerance * 0.6:
        speed = 0.0
        yaw = 0.0
    return speed, yaw


def apply_cbf(pose: Pose, speed: float, yaw: float, scenario: Scenario) -> tuple[float, float]:
    """Shield: cut speed and yaw away from obstacles when the barrier is small."""
    if not scenario.use_cbf:
        return speed, yaw
    h = barrier_value(pose, scenario)
    if h >= 0.12:
        return speed, yaw
    rx, ry = nearest_repulsion(pose, scenario.warehouse)
    away = math.atan2(ry, rx)
    err = wrap_angle(away - pose.theta)
    yaw = max(-scenario.robot.max_yaw_rate, min(scenario.robot.max_yaw_rate, 4.0 * err))
    scale = max(0.0, min(1.0, (h + 0.12) / 0.24))
    return speed * scale, yaw


def step(pose: Pose, speed: float, yaw: float, dt: float, friction: float = 1.0) -> Pose:
    v = speed * friction
    theta = pose.theta + yaw * dt
    return Pose(
        x=pose.x + v * math.cos(theta) * dt,
        y=pose.y + v * math.sin(theta) * dt,
        theta=wrap_angle(theta),
    )


def would_collide(
    pose: Pose, speed: float, yaw: float, dt: float, scenario: Scenario
) -> bool:
    nxt = step(pose, speed, yaw, dt, scenario.friction)
    return collision(nxt, scenario) is not None
