from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    world = LaunchConfiguration("world")
    scenario = LaunchConfiguration("scenario")
    result = LaunchConfiguration("result")
    return LaunchDescription(
        [
            DeclareLaunchArgument("world"),
            DeclareLaunchArgument("scenario"),
            DeclareLaunchArgument("result"),
            ExecuteProcess(
                cmd=["gz", "sim", "-s", "-r", world],
                output="screen",
            ),
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                arguments=[
                    "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                    "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
                ],
                output="screen",
            ),
            TimerAction(
                period=2.0,
                actions=[
                    Node(
                        package="vrtop_gazebo",
                        executable="episode",
                        name="vrtop_episode",
                        parameters=[
                            {"scenario_path": scenario},
                            {"result_path": result},
                        ],
                        output="screen",
                    )
                ],
            ),
        ]
    )
