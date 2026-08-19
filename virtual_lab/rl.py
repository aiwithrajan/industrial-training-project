from __future__ import annotations

import math
import random
from dataclasses import dataclass

from virtual_lab.controller import apply_cbf, step
from virtual_lab.models import Pose, Scenario, wrap_angle
from virtual_lab.simulator import simulate


def _state(pose: Pose, scenario: Scenario) -> tuple[int, int, int]:
    ix = min(max(int(pose.x), 0), int(scenario.warehouse.width) - 1)
    iy = min(max(int(pose.y), 0), int(scenario.warehouse.height) - 1)
    heading = int((wrap_angle(pose.theta) + math.pi) / (2 * math.pi / 8)) % 8
    return ix, iy, heading


def _act(pose: Pose, scenario: Scenario, action: int) -> tuple[float, float]:
    if action == 1:
        return scenario.speed * 0.35, scenario.robot.max_yaw_rate
    if action == 2:
        return scenario.speed * 0.35, -scenario.robot.max_yaw_rate
    return scenario.speed, 0.0


@dataclass
class RLPolicy:
    q: dict
    epsilon: float = 0.0

    def __call__(self, pose: Pose, scenario: Scenario) -> tuple[float, float]:
        s = _state(pose, scenario)
        qv = self.q.get(s, [0.0, 0.0, 0.0])
        action = max(range(3), key=lambda a: qv[a])
        return _act(pose, scenario, action)


def train_q(
    scenario: Scenario,
    episodes: int = 220,
    rng: random.Random | None = None,
    domain_randomize: bool = True,
) -> RLPolicy:
    rng = rng or random.Random(3)
    q: dict[tuple[int, int, int], list[float]] = {}
    alpha, gamma = 0.25, 0.95
    for ep in range(episodes):
        eps = max(0.05, 0.6 * (1 - ep / episodes))
        friction = rng.uniform(0.75, 1.15) if domain_randomize else 1.0
        noise = rng.uniform(0.0, 0.08) if domain_randomize else 0.0
        env = scenario.evolved(
            friction=friction,
            sensor_noise=noise,
            max_time=22.0,
            name=f"rl-train-{ep}",
            seed=rng.randint(0, 10_000),
        )
        pose = env.start
        for _ in range(int(env.max_time / env.dt)):
            s = _state(pose, env)
            q.setdefault(s, [0.0, 0.0, 0.0])
            action = rng.randrange(3) if rng.random() < eps else max(range(3), key=lambda a: q[s][a])
            speed, yaw = _act(pose, env, action)
            speed, yaw = apply_cbf(pose, speed, yaw, env)
            nxt = step(pose, speed, yaw, env.dt, env.friction)
            from virtual_lab.safety import collision

            fail = collision(nxt, env)
            dist = nxt.distance_to(env.goal)
            reward = -0.02 - (0.04 * dist / 20.0)
            done = False
            if fail:
                reward = -1.5
                done = True
            elif dist <= env.goal_tolerance:
                reward = 1.5
                done = True
            s2 = _state(nxt, env)
            q.setdefault(s2, [0.0, 0.0, 0.0])
            target = reward if done else reward + gamma * max(q[s2])
            q[s][action] += alpha * (target - q[s][action])
            pose = nxt
            if done:
                break
    return RLPolicy(q=q)


def evaluate_policy(scenario: Scenario, policy: RLPolicy, frictions: list[float]) -> list[dict]:
    rows = []
    for f in frictions:
        env = scenario.evolved(friction=f, name=f"{scenario.name}-mu{f:.2f}", use_cbf=True)
        result = simulate(env, policy=policy)
        rows.append({"friction": f, **result.summary()})
    return rows


def sensor_dropout_eval(scenario: Scenario, policy: RLPolicy | None) -> dict:
    from virtual_lab.controller import command as p_control

    policy_fn = policy if policy is not None else p_control
    clean = scenario.evolved(sensor_noise=0.0, use_cbf=True, name="clean")
    noisy = scenario.evolved(sensor_noise=0.18, use_cbf=True, name="lidar-drop")
    a = simulate(clean, policy=policy_fn)
    b = simulate(noisy, policy=policy_fn)
    return {
        "clean_success": a.success,
        "noisy_success": b.success,
        "clean": a.summary(),
        "noisy": b.summary(),
    }
