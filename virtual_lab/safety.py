from __future__ import annotations

import math

from virtual_lab.models import Pose, Scenario, Warehouse


def collision(pose: Pose, scenario: Scenario) -> str | None:
    robot = scenario.robot
    warehouse = scenario.warehouse
    if not warehouse.in_bounds(pose.x, pose.y, robot.radius):
        return "out_of_bounds"
    for i, box in enumerate(warehouse.obstacles):
        if box.intersects_circle(pose.x, pose.y, robot.radius):
            return f"obstacle_{i}"
    return None


def min_clearance(pose: Pose, warehouse: Warehouse) -> float:
    wall = min(pose.x, pose.y, warehouse.width - pose.x, warehouse.height - pose.y)
    best = wall
    for box in warehouse.obstacles:
        cx = min(max(pose.x, box.x0), box.x1)
        cy = min(max(pose.y, box.y0), box.y1)
        dist = math.hypot(pose.x - cx, pose.y - cy)
        best = min(best, dist)
    return best


def nearest_repulsion(pose: Pose, warehouse: Warehouse) -> tuple[float, float]:
    """Unit vector pointing away from the nearest obstacle surface (or wall)."""
    best = 1e9
    vx, vy = 0.0, 0.0
    walls = [
        (pose.x, 0.0, 0.0, 1.0),
        (pose.x, warehouse.height, 0.0, -1.0),
        (0.0, pose.y, 1.0, 0.0),
        (warehouse.width, pose.y, -1.0, 0.0),
    ]
    for px, py, nx, ny in walls:
        d = math.hypot(pose.x - px, pose.y - py)
        if d < best:
            best, vx, vy = d, nx, ny
    for box in warehouse.obstacles:
        cx = min(max(pose.x, box.x0), box.x1)
        cy = min(max(pose.y, box.y0), box.y1)
        dx, dy = pose.x - cx, pose.y - cy
        d = math.hypot(dx, dy)
        if d < 1e-9:
            dx, dy, d = 1.0, 0.0, 1e-9
        if d < best:
            best = d
            vx, vy = dx / d, dy / d
    return vx, vy


def barrier_value(pose: Pose, scenario: Scenario) -> float:
    """CBF: h = clearance_to_body - margin. Safe when h >= 0."""
    clearance = min_clearance(pose, scenario.warehouse) - scenario.robot.radius
    return clearance - scenario.cbf_margin
