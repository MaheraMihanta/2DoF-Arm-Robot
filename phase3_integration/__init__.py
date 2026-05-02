"""
Phase 3: Intégration
Module d'intégration complète du système de contrôle
"""

__all__ = ['RobotController', 'ControlMode', 'RobotGUI']
__version__ = '1.0.0'


def __getattr__(name):
    if name in {"RobotController", "ControlMode"}:
        from .robot_controller import RobotController, ControlMode
        return {"RobotController": RobotController, "ControlMode": ControlMode}[name]
    if name == "RobotGUI":
        from .gui import RobotGUI
        return RobotGUI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Made with Bob
