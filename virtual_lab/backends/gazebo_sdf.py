from __future__ import annotations

from virtual_lab.models import AABB, Scenario, Warehouse


def scenario_to_sdf(scenario: Scenario) -> str:
    """Export a warehouse scenario to an SDF 1.9 world for Gazebo / gz-sim."""
    w = scenario.warehouse.width
    h = scenario.warehouse.height
    models = [
        _ground(w, h),
        _walls(w, h),
        _robot(scenario),
        _goal(scenario),
    ]
    for i, box in enumerate(scenario.warehouse.obstacles):
        models.append(_box(f"shelf_{i}", box, color="0.12 0.42 0.58 1"))
    inner = "\n".join(models)
    return f"""<?xml version="1.0" ?>
<sdf version="1.9">
  <world name="{_xml(scenario.name)}">
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
    <gravity>0 0 -9.8</gravity>
    <magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field>
    <scene>
      <ambient>0.6 0.6 0.65 1</ambient>
      <background>0.85 0.88 0.92 1</background>
    </scene>
{inner}
  </world>
</sdf>
"""


def _xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _ground(w: float, h: float) -> str:
    return f"""    <model name="floor">
      <static>true</static>
      <pose>{w/2:.3f} {h/2:.3f} 0 0 0 0</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{w:.3f} {h:.3f} 0.05</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{w:.3f} {h:.3f} 0.05</size></box></geometry>
          <material><ambient>0.75 0.75 0.78 1</ambient></material>
        </visual>
      </link>
    </model>"""


def _walls(w: float, h: float) -> str:
    t = 0.2
    boxes = [
        (w / 2, -t / 2, w + 2 * t, t),
        (w / 2, h + t / 2, w + 2 * t, t),
        (-t / 2, h / 2, t, h),
        (w + t / 2, h / 2, t, h),
    ]
    chunks = []
    for i, (x, y, bw, bh) in enumerate(boxes):
        chunks.append(_box(f"wall_{i}", AABB(x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2), color="0.2 0.25 0.35 1"))
    return "\n".join(chunks)


def _box(name: str, box: AABB, color: str) -> str:
    cx = (box.x0 + box.x1) / 2
    cy = (box.y0 + box.y1) / 2
    sx = max(box.x1 - box.x0, 0.05)
    sy = max(box.y1 - box.y0, 0.05)
    sz = 1.4
    return f"""    <model name="{_xml(name)}">
      <static>true</static>
      <pose>{cx:.3f} {cy:.3f} {sz/2:.3f} 0 0 0</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material><ambient>{color}</ambient></material>
        </visual>
      </link>
    </model>"""


def _goal(scenario: Scenario) -> str:
    return f"""    <model name="goal">
      <static>true</static>
      <pose>{scenario.goal.x:.3f} {scenario.goal.y:.3f} 0.02 0 0 0</pose>
      <link name="link">
        <visual name="vis">
          <geometry><cylinder><radius>0.25</radius><length>0.02</length></cylinder></geometry>
          <material><ambient>0.83 0.63 0.09 1</ambient></material>
        </visual>
      </link>
    </model>"""


def _robot(scenario: Scenario) -> str:
    r = scenario.robot.radius
    x, y, th = scenario.start.x, scenario.start.y, scenario.start.theta
    return f"""    <model name="robot">
      <pose>{x:.3f} {y:.3f} {r:.3f} 0 0 {th:.4f}</pose>
      <link name="base">
        <inertial>
          <mass>4.0</mass>
          <inertia><ixx>0.05</ixx><iyy>0.05</iyy><izz>0.08</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia>
        </inertial>
        <collision name="col"><geometry><cylinder><radius>{r:.3f}</radius><length>0.18</length></cylinder></geometry></collision>
        <visual name="vis">
          <geometry><cylinder><radius>{r:.3f}</radius><length>0.18</length></cylinder></geometry>
          <material><ambient>0.77 0.27 0.21 1</ambient></material>
        </visual>
        <sensor name="lidar" type="gpu_lidar">
          <pose>0 0 0.12 0 0 0</pose>
          <lidar>
            <scan><horizontal><samples>120</samples><min_angle>-1.57</min_angle><max_angle>1.57</max_angle></horizontal></scan>
            <range><min>0.08</min><max>12</max></range>
          </lidar>
          <always_on>1</always_on>
          <visualize>true</visualize>
          <update_rate>10</update_rate>
        </sensor>
      </link>
      <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
        <frame_id>robot/base</frame_id>
        <child_frame_id>robot/base</child_frame_id>
        <topic>/cmd_vel</topic>
        <wheel_separation>{scenario.robot.wheelbase:.3f}</wheel_separation>
        <wheel_radius>0.05</wheel_radius>
        <max_linear_acceleration>2</max_linear_acceleration>
        <min_linear_acceleration>-2</min_linear_acceleration>
      </plugin>
      <plugin filename="gz-sim-odometry-publisher-system" name="gz::sim::systems::OdometryPublisher">
        <odom_topic>/odom</odom_topic>
        <tf_topic>/tf</tf_topic>
      </plugin>
    </model>"""


def warehouse_bounds_ok(warehouse: Warehouse) -> bool:
    return warehouse.width > 2 and warehouse.height > 2
