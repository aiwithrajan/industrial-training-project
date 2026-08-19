from setuptools import find_packages, setup

package_name = "vrtop_gazebo"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/warehouse.launch.py"]),
        ("share/" + package_name + "/config", ["config/bridge.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Rajan Mishra",
    maintainer_email="jarajan123@gmail.com",
    description="Gazebo / ROS 2 bringup for VRTOP",
    license="MIT",
    entry_points={
        "console_scripts": [
            "episode = vrtop_gazebo.episode_node:main",
        ],
    },
)
