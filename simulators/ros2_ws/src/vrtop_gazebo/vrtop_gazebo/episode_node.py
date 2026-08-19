"""ROS 2 node: drive the Gazebo robot with the same P-controller as the 2D twin."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

# Allow importing the repo's virtual_lab when sourced from the workspace overlay.
REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from virtual_lab.controller import apply_cbf, command  # noqa: E402
from virtual_lab.models import Pose, Scenario  # noqa: E402
from virtual_lab.safety import barrier_value, collision, min_clearance  # noqa: E402
from virtual_lab.simulator import RunResult, Sample, write_run  # noqa: E402


def yaw_from_quat(z: float, w: float) -> float:
    return math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)


class EpisodeNode(Node):
    def __init__(self) -> None:
        super().__init__("vrtop_episode")
        self.declare_parameter("scenario_path", "")
        self.declare_parameter("result_path", "/tmp/vrtop_gz_result.json")
        scenario_path = self.get_parameter("scenario_path").get_parameter_value().string_value
        self.result_path = Path(self.get_parameter("result_path").get_parameter_value().string_value)
        self.scenario = Scenario.load(scenario_path)
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.create_subscription(Odometry, "/odom", self._on_odom, 10)
        self.pose = self.scenario.start
        self.samples: list[Sample] = []
        self.path_length = 0.0
        self.t = 0.0
        self.worst_clear = 1e9
        self.worst_h = 1e9
        self.violations = 0
        self.done = False
        self.create_timer(self.scenario.dt, self._tick)

    def _on_odom(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.pose = Pose(p.x, p.y, yaw_from_quat(q.z, q.w))

    def _tick(self) -> None:
        if self.done:
            return
        sc = self.scenario
        speed, yaw = command(self.pose, sc)
        speed, yaw = apply_cbf(self.pose, speed, yaw, sc)
        twist = Twist()
        twist.linear.x = float(speed)
        twist.angular.z = float(yaw)
        self.pub.publish(twist)
        event = collision(self.pose, sc)
        clearance = min_clearance(self.pose, sc.warehouse)
        h = barrier_value(self.pose, sc)
        self.worst_clear = min(self.worst_clear, clearance)
        self.worst_h = min(self.worst_h, h)
        if h < 0:
            self.violations += 1
        if self.samples:
            prev = self.samples[-1]
            self.path_length += math.hypot(self.pose.x - prev.x, self.pose.y - prev.y)
        self.t += sc.dt
        self.samples.append(
            Sample(self.t, self.pose.x, self.pose.y, self.pose.theta, speed, yaw, clearance, h, event)
        )
        outcome = None
        if event:
            outcome = event
        elif self.pose.distance_to(sc.goal) <= sc.goal_tolerance:
            outcome = "goal"
        elif self.t >= sc.max_time:
            outcome = "timeout"
        if outcome:
            self.done = True
            twist = Twist()
            self.pub.publish(twist)
            result = RunResult(
                scenario=sc.name,
                success=outcome == "goal",
                outcome=outcome,
                duration=self.t,
                path_length=self.path_length,
                min_clearance=self.worst_clear,
                min_barrier=self.worst_h,
                samples=self.samples,
                violations=self.violations,
            )
            write_run(result, self.result_path)
            self.get_logger().info(f"episode done: {outcome} -> {self.result_path}")
            raise SystemExit(0)


def main() -> None:
    rclpy.init()
    node = EpisodeNode()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
