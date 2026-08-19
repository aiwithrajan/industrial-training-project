from __future__ import annotations

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
    """Approximate distance to nearest obstacle or wall (center to geometry)."""
    wall = min(pose.x, pose.y, warehouse.width - pose.x, warehouse.height - pose.y)
    best = wall
    for box in warehouse.obstacles:
        cx = min(max(pose.x, box.x0), box.x1)
        cy = min(max(pose.y, box.y0), box.y1)
        dist = ((pose.x - cx) ** 2 + (pose.y - cy) ** 2) ** 0.5
        best = min(best, dist)
    return best
