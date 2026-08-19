# Adding Gazebo / ROS 2 and Isaac Sim

The platform already runs a **2D twin** (`--backend twin`). Gazebo and Isaac Sim are **drop-in physics backends**. Search, Bayesian tuning, RL, and CBF stay in Python; only the step/collision loop changes.

```
python3 -m virtual_lab doctor
python3 -m virtual_lab run --backend twin   --scenario scenarios/open_aisle.json
python3 -m virtual_lab run --backend gazebo --scenario scenarios/open_aisle.json
python3 -m virtual_lab run --backend isaac  --scenario scenarios/open_aisle.json
```

`doctor` prints which engines are installed. If Gazebo or Isaac is missing, the command fails with the exact apt/Docker lines below.

## What you need

| Backend | Machine | GPU | Typical use |
| --- | --- | --- | --- |
| `twin` | any Python 3.11+ | no | CI, algorithms, this repo today |
| `gazebo` | Ubuntu 22.04/24.04 + ROS 2 | no | ROS robots, LiDAR, contacts |
| `isaac` | Ubuntu 22.04 + NVIDIA GPU | yes | vision, domain rand, parallel RL |

Sim-to-sim gap (month 5): train on `twin` or `gazebo`, evaluate on `isaac` (or the other way around).

---

## 1. Gazebo + ROS 2 (recommended next step)

### Install on Ubuntu 22.04 (Humble + Fortress)

```bash
sudo apt update
sudo apt install -y ros-humble-desktop ros-humble-ros-gz ros-humble-ros-gz-sim \
    ros-humble-ros-gz-bridge python3-colcon-common-extensions
source /opt/ros/humble/setup.bash
```

### Ubuntu 24.04 (Jazzy + Harmonic)

```bash
sudo apt install -y ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-ros-gz-sim
source /opt/ros/jazzy/setup.bash
```

### Build this repo's package

```bash
cd simulators/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install
source install/setup.bash
cd ../..
export PYTHONPATH=$PWD
python3 -m virtual_lab doctor
python3 -m virtual_lab run --backend gazebo --scenario scenarios/open_aisle.json --allow-failure
```

What that does:

1. `virtual_lab/backends/gazebo_sdf.py` turns a scenario JSON into a Gazebo SDF world (floor, shelves, diff-drive robot, LiDAR).
2. `ros2 launch vrtop_gazebo warehouse.launch.py` starts `gz sim` and a ROS 2 bridge (`/cmd_vel`, `/odom`).
3. `vrtop_gazebo/episode_node.py` uses the **same P-controller + CBF** as the 2D twin and writes a `RunResult` JSON.

### Docker (no local ROS)

```bash
docker compose --profile gazebo build
docker compose --profile gazebo run --rm gazebo
```

---

## 2. NVIDIA Isaac Sim

Isaac does **not** install from `apt`. You need a recent NVIDIA driver and either the Omniverse Isaac Sim download or the NGC container.

### Workstation install

1. Follow [Isaac Sim installation](https://docs.isaacsim.omniverse.nvidia.com/).
2. Use Isaac's `python.sh`, not system Python:

```bash
./python.sh simulators/isaac/run_episode.py \
  --scenario scenarios/open_aisle.json \
  --out /tmp/isaac_result.json \
  --headless
```

Or, if `import isaacsim` works in your env:

```bash
python3 -m virtual_lab run --backend isaac --scenario scenarios/open_aisle.json --allow-failure
```

Dry checks without a GPU:

```bash
python3 simulators/isaac/run_episode.py --scenario scenarios/open_aisle.json --out /tmp/prims.json --dry-export
python3 simulators/isaac/run_episode.py --scenario scenarios/open_aisle.json --out /tmp/twin.json --dry-run
```

### Docker (GPU + NGC login)

```bash
# nvidia-container-toolkit and NGC access required
docker compose --profile isaac build
docker compose --profile isaac run --rm isaac
```

The Isaac container tag is `nvcr.io/nvidia/isaac-sim:4.5.0`. Change it in `docker/Dockerfile.isaac` if NVIDIA publishes a newer image.

---

## 3. How the code is wired

| Piece | Role |
| --- | --- |
| `virtual_lab/backends/` | `twin` / `gazebo` / `isaac` share `simulate(scenario) -> RunResult` |
| `simulators/ros2_ws/src/vrtop_gazebo/` | colcon package: launch + episode node |
| `simulators/isaac/run_episode.py` | Isaac World + cuboid shelves |
| `docker-compose.yml` | `gazebo` and `isaac` profiles |

Adversarial search and Bayesian tuning still generate `Scenario` objects. Point them at another engine later by passing `backend=` into `simulate` once you want GPU batches.

---

## 4. Optional: Nav2 and TurtleBot3

For a stock ROS navigation stack instead of our P-controller:

```bash
sudo apt install -y ros-$ROS_DISTRO-navigation2 ros-$ROS_DISTRO-turtlebot3-gazebo
export TURTLEBOT3_MODEL=waffle
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Keep VRTOP scenarios for failure search; use Nav2 as an alternate policy. That is a swap of the controller, not of the backend interface.
