from __future__ import annotations

from typing import Any

from virtual_lab.models import Scenario


def twin_graph(scenario: Scenario) -> dict[str, Any]:
    """Minimal software knowledge graph for the robot + warehouse."""
    return {
        "nodes": [
            {"id": "warehouse", "type": "environment", "width": scenario.warehouse.width, "height": scenario.warehouse.height},
            {"id": "robot", "type": "mobile_base", "radius": scenario.robot.radius},
            {"id": "lidar", "type": "sensor", "parent": "robot"},
            {"id": "start", "type": "pose", "x": scenario.start.x, "y": scenario.start.y},
            {"id": "goal", "type": "pose", "x": scenario.goal.x, "y": scenario.goal.y},
            *[
                {
                    "id": f"obstacle_{i}",
                    "type": "obstacle",
                    "bounds": [o.x0, o.y0, o.x1, o.y1],
                }
                for i, o in enumerate(scenario.warehouse.obstacles)
            ],
        ],
        "edges": [
            {"from": "robot", "to": "warehouse", "rel": "operates_in"},
            {"from": "lidar", "to": "robot", "rel": "mounted_on"},
            {"from": "start", "to": "goal", "rel": "task_navigate"},
            *[
                {"from": f"obstacle_{i}", "to": "warehouse", "rel": "contained_in"}
                for i in range(len(scenario.warehouse.obstacles))
            ],
        ],
    }
