"""
Phase 1: Modélisation et Simulation
Module de cinématique et simulation du bras robotique 2DDL
"""

__all__ = ['RobotConfig', 'config', 'Kinematics', 'RobotSimulator']
__version__ = '1.0.0'


def __getattr__(name):
    if name in {"RobotConfig", "config"}:
        from .config import RobotConfig, config
        return {"RobotConfig": RobotConfig, "config": config}[name]
    if name == "Kinematics":
        from .kinematics import Kinematics
        return Kinematics
    if name == "RobotSimulator":
        from .simulator import RobotSimulator
        return RobotSimulator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Made with Bob
