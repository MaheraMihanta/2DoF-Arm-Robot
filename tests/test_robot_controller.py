"""
Tests ciblés sur le contrôleur principal et les trajectoires animées.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from phase1_simulation.config import RobotConfig
from phase3_integration.robot_controller import ControlMode, RobotController


@pytest.fixture
def fast_config():
    config = RobotConfig()
    config.simulation_dt = 0.001
    config.min_animation_duration = 0.0
    config.max_animation_duration = 0.0
    return config


@pytest.fixture
def robot(fast_config):
    controller = RobotController(fast_config, ControlMode.SIMULATION)
    yield controller
    controller.disconnect()


def test_move_to_position_updates_final_pose(robot):
    success = robot.move_to_position(250.0, 150.0, elbow_up=True, feed_rate=1200.0)
    assert success is True

    x, y = robot.get_current_position()
    assert np.isclose(x, 250.0, atol=1e-3)
    assert np.isclose(y, 150.0, atol=1e-3)


def test_plan_square_trajectory_returns_points(robot):
    trajectory = robot.plan_square_trajectory(240.0, 150.0, side_length=60.0, points_per_edge=8)
    assert trajectory is not None
    assert trajectory.shape[1] == 4
    assert len(trajectory) > 20


def test_execute_trajectory_finishes_at_last_point(robot):
    trajectory = robot.plan_circle_trajectory(235.0, 150.0, radius=25.0, num_points=24)
    assert trajectory is not None

    success = robot.execute_trajectory(trajectory, feed_rate=1400.0, trajectory_name="test cercle")
    assert success is True

    x, y = robot.get_current_position()
    assert np.isclose(x, trajectory[-1, 0], atol=1e-3)
    assert np.isclose(y, trajectory[-1, 1], atol=1e-3)
    assert len(robot.position_history) > 1
