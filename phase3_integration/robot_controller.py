"""
Contrôleur principal du bras robotique 2DDL.
Intègre la cinématique, l'animation de simulation et la liaison GRBL.
"""

from __future__ import annotations

import time
import threading
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    from ..phase1_simulation.config import RobotConfig
    from ..phase1_simulation.kinematics import Kinematics
    from ..phase2_hardware.grbl_interface import GRBLInterface
    from ..phase2_hardware.motor_control import MotorController
except ImportError:
    import os
    import sys

    CURRENT_DIR = os.path.dirname(__file__)
    sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "phase1_simulation"))
    sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "phase2_hardware"))

    from config import RobotConfig
    from kinematics import Kinematics
    from grbl_interface import GRBLInterface
    from motor_control import MotorController


class ControlMode(Enum):
    """Modes de contrôle du robot."""

    SIMULATION = "simulation"
    HARDWARE = "hardware"
    HYBRID = "hybrid"


StateListener = Callable[[Dict[str, object]], None]


class RobotController:
    """Contrôleur principal du bras robotique."""

    def __init__(
        self,
        config: RobotConfig,
        mode: ControlMode = ControlMode.SIMULATION,
        grbl_port: Optional[str] = None,
    ):
        self.config = config
        self.mode = mode
        self.kinematics = Kinematics(config)

        self.current_theta1 = 0.0
        self.current_theta2 = 0.0
        self.target_theta1 = 0.0
        self.target_theta2 = 0.0

        self.grbl: Optional[GRBLInterface] = None
        self.motor_controller: Optional[MotorController] = None

        self.position_history: List[Tuple[float, float]] = []
        self.max_history = 2000
        self.last_error = ""
        self.is_busy = False
        self.active_trajectory_name: Optional[str] = None
        self.active_trajectory_index = 0
        self.active_trajectory_size = 0

        self._state_lock = threading.RLock()
        self._state_listeners: List[StateListener] = []

        if mode in (ControlMode.HARDWARE, ControlMode.HYBRID):
            if grbl_port is None:
                raise ValueError("grbl_port requis pour le mode hardware/hybrid")

            self.grbl = GRBLInterface(
                port=grbl_port,
                baudrate=config.grbl_baudrate,
            )
            if self.grbl.connect():
                self.motor_controller = MotorController(config, self.grbl)
                print(f"Mode {mode.value}: matériel connecté sur {grbl_port}")
            else:
                raise ConnectionError(f"Impossible de se connecter à GRBL sur {grbl_port}")
        else:
            print(f"Mode {mode.value}: simulation graphique active")

        self._append_position_history()
        self._emit_state()

    def add_state_listener(self, listener: StateListener, emit_current: bool = True):
        """Enregistre un listener appelé à chaque mise à jour d'état."""
        with self._state_lock:
            if listener not in self._state_listeners:
                self._state_listeners.append(listener)

        if emit_current:
            listener(self.get_state_snapshot())

    def remove_state_listener(self, listener: StateListener):
        """Supprime un listener d'état."""
        with self._state_lock:
            if listener in self._state_listeners:
                self._state_listeners.remove(listener)

    def _emit_state(self):
        snapshot = self.get_state_snapshot()
        for listener in list(self._state_listeners):
            try:
                listener(snapshot)
            except Exception:
                continue

    def _set_busy(self, busy: bool):
        with self._state_lock:
            self.is_busy = busy
        self._emit_state()

    def _set_error(self, message: str):
        with self._state_lock:
            self.last_error = message
        if message:
            print(message)
        self._emit_state()

    def _clear_error(self):
        with self._state_lock:
            self.last_error = ""
        self._emit_state()

    def _append_position_history(self, x: Optional[float] = None, y: Optional[float] = None):
        if x is None or y is None:
            x, y = self.kinematics.forward_kinematics(self.current_theta1, self.current_theta2)

        self.position_history.append((x, y))
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)

    def clear_position_history(self):
        """Efface l'historique visible de la trajectoire."""
        with self._state_lock:
            self.position_history.clear()
            self._append_position_history()
        self._emit_state()

    def get_state_snapshot(self) -> Dict[str, object]:
        """Retourne un instantané thread-safe de l'état courant."""
        with self._state_lock:
            x, y = self.kinematics.forward_kinematics(self.current_theta1, self.current_theta2)
            target_x, target_y = self.kinematics.forward_kinematics(
                self.target_theta1,
                self.target_theta2,
            )

            return {
                "mode": self.mode.value,
                "theta1": self.current_theta1,
                "theta2": self.current_theta2,
                "target_theta1": self.target_theta1,
                "target_theta2": self.target_theta2,
                "x": x,
                "y": y,
                "target_x": target_x,
                "target_y": target_y,
                "history": list(self.position_history),
                "is_busy": self.is_busy,
                "last_error": self.last_error,
                "trajectory_name": self.active_trajectory_name,
                "trajectory_index": self.active_trajectory_index,
                "trajectory_size": self.active_trajectory_size,
                "grbl_connected": bool(self.grbl and self.grbl.is_connected),
            }

    def _estimate_motion_duration(
        self,
        start_theta1: float,
        start_theta2: float,
        target_theta1: float,
        target_theta2: float,
        feed_rate: Optional[float] = None,
    ) -> float:
        delta1 = abs(target_theta1 - start_theta1)
        delta2 = abs(target_theta2 - start_theta2)

        speed_scale = 1.0
        if feed_rate:
            speed_scale = float(np.clip(feed_rate / 1000.0, 0.3, 4.0))

        velocity1 = self.config.max_angular_velocity_1 * speed_scale
        velocity2 = self.config.max_angular_velocity_2 * speed_scale

        duration = max(
            delta1 / max(velocity1, 1e-6),
            delta2 / max(velocity2, 1e-6),
            self.config.min_animation_duration,
        )
        return min(duration, self.config.max_animation_duration)

    def _animate_joint_motion(
        self,
        theta1: float,
        theta2: float,
        feed_rate: Optional[float] = None,
    ):
        start_theta1 = self.current_theta1
        start_theta2 = self.current_theta2

        duration = self._estimate_motion_duration(
            start_theta1,
            start_theta2,
            theta1,
            theta2,
            feed_rate,
        )
        steps = max(1, int(duration / self.config.simulation_dt))

        for step in range(1, steps + 1):
            alpha = step / steps
            eased_alpha = 0.5 - 0.5 * np.cos(np.pi * alpha)

            with self._state_lock:
                self.current_theta1 = start_theta1 + (theta1 - start_theta1) * eased_alpha
                self.current_theta2 = start_theta2 + (theta2 - start_theta2) * eased_alpha
                self._append_position_history()

            self._emit_state()
            if step < steps:
                time.sleep(self.config.simulation_dt)

        with self._state_lock:
            self.current_theta1 = theta1
            self.current_theta2 = theta2
            self._append_position_history()

        self._emit_state()

    def _move_to_angles_internal(
        self,
        theta1: float,
        theta2: float,
        feed_rate: Optional[float] = None,
        animate: bool = True,
        mark_busy: bool = True,
    ) -> bool:
        if not self.config.is_angle_valid(theta1, theta2):
            self._set_error(
                f"Erreur: angles hors limites ({np.degrees(theta1):.1f}°, {np.degrees(theta2):.1f}°)"
            )
            return False

        if mark_busy:
            self._set_busy(True)

        try:
            with self._state_lock:
                self.target_theta1 = theta1
                self.target_theta2 = theta2
            self._clear_error()

            if self.mode in (ControlMode.HARDWARE, ControlMode.HYBRID):
                if not self.motor_controller:
                    self._set_error("Erreur: contrôleur matériel non initialisé")
                    return False

                success = self.motor_controller.move_to_angles(theta1, theta2, feed_rate)
                if not success:
                    self._set_error("Erreur: échec de l'envoi de la commande GRBL")
                    return False

            if animate:
                self._animate_joint_motion(theta1, theta2, feed_rate)
            else:
                with self._state_lock:
                    self.current_theta1 = theta1
                    self.current_theta2 = theta2
                    self._append_position_history()
                self._emit_state()

            return True
        finally:
            if mark_busy:
                self._set_busy(False)

    def move_to_angles(
        self,
        theta1: float,
        theta2: float,
        feed_rate: Optional[float] = None,
        animate: bool = True,
    ) -> bool:
        """
        Déplace le robot vers les angles spécifiés.
        """
        return self._move_to_angles_internal(theta1, theta2, feed_rate, animate, mark_busy=True)

    def move_to_position(
        self,
        x: float,
        y: float,
        elbow_up: bool = True,
        feed_rate: Optional[float] = None,
        animate: bool = True,
    ) -> bool:
        """
        Déplace le robot vers une position cartésienne.
        """
        result = self.kinematics.inverse_kinematics(x, y, elbow_up)
        if result is None:
            self._set_error(f"Erreur: position ({x:.1f}, {y:.1f}) non atteignable")
            return False

        theta1, theta2 = result
        return self.move_to_angles(theta1, theta2, feed_rate, animate=animate)

    def execute_trajectory(
        self,
        trajectory: np.ndarray,
        feed_rate: Optional[float] = None,
        animate: bool = True,
        trajectory_name: str = "trajectoire",
    ) -> bool:
        """
        Exécute une trajectoire complète.
        """
        if trajectory is None or len(trajectory) == 0:
            self._set_error("Erreur: trajectoire vide")
            return False

        print(f"Exécution de {trajectory_name} ({len(trajectory)} points)")
        self._set_busy(True)

        with self._state_lock:
            self.active_trajectory_name = trajectory_name
            self.active_trajectory_index = 0
            self.active_trajectory_size = len(trajectory)
        self._emit_state()

        try:
            for index, point in enumerate(trajectory, start=1):
                x, y, theta1, theta2 = point
                with self._state_lock:
                    self.active_trajectory_index = index
                    self.target_theta1 = theta1
                    self.target_theta2 = theta2
                self._emit_state()

                success = self._move_to_angles_internal(
                    theta1,
                    theta2,
                    feed_rate,
                    animate=animate,
                    mark_busy=False,
                )
                if not success:
                    self._set_error(f"Échec à l'exécution du point {index}: ({x:.1f}, {y:.1f})")
                    return False

            print("Trajectoire complète exécutée")
            return True
        finally:
            with self._state_lock:
                self.active_trajectory_name = None
                self.active_trajectory_index = 0
                self.active_trajectory_size = 0
            self._set_busy(False)

    def plan_linear_trajectory(
        self,
        target_x: float,
        target_y: float,
        num_points: int = 50,
        elbow_up: bool = True,
    ) -> Optional[np.ndarray]:
        """
        Planifie une trajectoire linéaire dans l'espace cartésien.
        """
        current_x, current_y = self.get_current_position()
        return self.kinematics.compute_trajectory(
            (current_x, current_y),
            (target_x, target_y),
            num_points,
            elbow_up,
        )

    def _build_entry_segment(
        self,
        first_point: Tuple[float, float],
        points: int = 15,
        elbow_up: bool = True,
    ) -> Optional[np.ndarray]:
        current_x, current_y = self.get_current_position()
        if np.hypot(first_point[0] - current_x, first_point[1] - current_y) < 1e-6:
            return None
        return self.kinematics.compute_trajectory(
            (current_x, current_y),
            first_point,
            num_points=max(2, points),
            elbow_up=elbow_up,
        )

    @staticmethod
    def _combine_trajectories(*trajectories: Optional[np.ndarray]) -> Optional[np.ndarray]:
        valid_trajectories = [traj for traj in trajectories if traj is not None and len(traj) > 0]
        if not valid_trajectories:
            return None

        combined = [valid_trajectories[0]]
        for trajectory in valid_trajectories[1:]:
            combined.append(trajectory[1:] if len(trajectory) > 1 else trajectory)
        return np.vstack(combined)

    def plan_square_trajectory(
        self,
        center_x: float,
        center_y: float,
        side_length: float = 80.0,
        points_per_edge: int = 20,
        elbow_up: bool = True,
    ) -> Optional[np.ndarray]:
        half_side = side_length / 2.0
        waypoints = [
            (center_x - half_side, center_y - half_side),
            (center_x + half_side, center_y - half_side),
            (center_x + half_side, center_y + half_side),
            (center_x - half_side, center_y + half_side),
            (center_x - half_side, center_y - half_side),
        ]

        entry = self._build_entry_segment(waypoints[0], elbow_up=elbow_up)
        square = self.kinematics.compute_polyline_trajectory(
            waypoints,
            points_per_segment=points_per_edge,
            elbow_up=elbow_up,
        )
        return self._combine_trajectories(entry, square)

    def plan_circle_trajectory(
        self,
        center_x: float,
        center_y: float,
        radius: float = 40.0,
        num_points: int = 72,
        elbow_up: bool = True,
    ) -> Optional[np.ndarray]:
        circle = self.kinematics.compute_circular_trajectory(
            (center_x, center_y),
            radius=radius,
            num_points=num_points,
            elbow_up=elbow_up,
            closed=True,
        )
        if circle is None or len(circle) == 0:
            return None

        entry = self._build_entry_segment((circle[0, 0], circle[0, 1]), elbow_up=elbow_up)
        return self._combine_trajectories(entry, circle)

    def plan_zigzag_trajectory(
        self,
        origin_x: float,
        origin_y: float,
        width: float = 140.0,
        height: float = 90.0,
        passes: int = 6,
        points_per_segment: int = 12,
        elbow_up: bool = True,
    ) -> Optional[np.ndarray]:
        passes = max(2, int(passes))
        y_values = np.linspace(origin_y, origin_y + height, passes)

        waypoints: List[Tuple[float, float]] = []
        for index, y in enumerate(y_values):
            if index % 2 == 0:
                waypoints.append((origin_x, float(y)))
                waypoints.append((origin_x + width, float(y)))
            else:
                waypoints.append((origin_x + width, float(y)))
                waypoints.append((origin_x, float(y)))

        entry = self._build_entry_segment(waypoints[0], elbow_up=elbow_up)
        zigzag = self.kinematics.compute_polyline_trajectory(
            waypoints,
            points_per_segment=points_per_segment,
            elbow_up=elbow_up,
        )
        return self._combine_trajectories(entry, zigzag)

    def home(self, animate: bool = True) -> bool:
        """
        Retour à la position d'origine.
        """
        self._set_busy(True)
        try:
            if self.mode in (ControlMode.HARDWARE, ControlMode.HYBRID):
                if not self.motor_controller:
                    self._set_error("Erreur: contrôleur matériel non initialisé")
                    return False
                if not self.motor_controller.home_motors():
                    self._set_error("Erreur: homing GRBL échoué")
                    return False

            return self._move_to_angles_internal(0.0, 0.0, animate=animate, mark_busy=False)
        finally:
            self._set_busy(False)

    def get_current_position(self) -> Tuple[float, float]:
        return self.kinematics.forward_kinematics(self.current_theta1, self.current_theta2)

    def get_current_angles(self) -> Tuple[float, float]:
        return self.current_theta1, self.current_theta2

    def get_workspace_info(self) -> dict:
        limits = self.config.get_workspace_limits()
        x, y = self.get_current_position()
        limits["current_x"] = x
        limits["current_y"] = y
        limits["current_theta1"] = self.current_theta1
        limits["current_theta2"] = self.current_theta2
        return limits

    def emergency_stop(self):
        """Arrêt d'urgence."""
        print("ARRÊT D'URGENCE!")
        if self.motor_controller:
            self.motor_controller.emergency_stop()
        self._set_error("Arrêt d'urgence déclenché")

    def disconnect(self):
        """Déconnecte le matériel."""
        if self.grbl:
            self.grbl.disconnect()
            print("Matériel déconnecté")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


def interactive_demo():
    """Démonstration interactive en ligne de commande."""
    print("=== Contrôleur Robot 2DDL - Démonstration Interactive ===\n")

    try:
        from ..phase1_simulation.config import config
    except ImportError:
        from config import config

    print("Modes disponibles:")
    print("1. Simulation")
    print("2. Matériel (GRBL)")
    print("3. Hybride (Simulation + Matériel)")

    mode_choice = input("\nChoisir le mode (1-3): ").strip()
    if mode_choice == "1":
        mode = ControlMode.SIMULATION
        grbl_port = None
    elif mode_choice == "2":
        mode = ControlMode.HARDWARE
        grbl_port = input("Port série (ex: COM3): ").strip()
    elif mode_choice == "3":
        mode = ControlMode.HYBRID
        grbl_port = input("Port série (ex: COM3): ").strip()
    else:
        print("Choix invalide")
        return

    try:
        with RobotController(config, mode, grbl_port) as robot:
            print(f"\nContrôleur initialisé en mode {mode.value}")

            while True:
                print("\n--- Menu Principal ---")
                print("1. Déplacer vers angles")
                print("2. Déplacer vers position")
                print("3. Trajectoire linéaire")
                print("4. Position actuelle")
                print("5. Info espace de travail")
                print("6. Home")
                print("7. Trajectoire carrée")
                print("8. Trajectoire circulaire")
                print("9. Arrêt d'urgence")
                print("0. Quitter")

                choice = input("\nChoix: ").strip()

                if choice == "1":
                    theta1_deg = float(input("theta1 (degres): "))
                    theta2_deg = float(input("theta2 (degres): "))
                    robot.move_to_angles(np.radians(theta1_deg), np.radians(theta2_deg))
                elif choice == "2":
                    x = float(input("x (mm): "))
                    y = float(input("y (mm): "))
                    elbow = input("Coude haut? (o/n): ").lower() == "o"
                    robot.move_to_position(x, y, elbow)
                elif choice == "3":
                    x = float(input("x cible (mm): "))
                    y = float(input("y cible (mm): "))
                    n = int(input("Nombre de points (défaut 50): ") or "50")
                    trajectory = robot.plan_linear_trajectory(x, y, n)
                    if trajectory is not None:
                        robot.execute_trajectory(trajectory, trajectory_name="trajectoire linéaire")
                    else:
                        print("Impossible de planifier la trajectoire")
                elif choice == "4":
                    x, y = robot.get_current_position()
                    theta1, theta2 = robot.get_current_angles()
                    print(f"Position: x={x:.2f} mm, y={y:.2f} mm")
                    print(
                        f"Angles: theta1={np.degrees(theta1):.1f} deg, "
                        f"theta2={np.degrees(theta2):.1f} deg"
                    )
                elif choice == "5":
                    info = robot.get_workspace_info()
                    for key, value in info.items():
                        print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
                elif choice == "6":
                    robot.home()
                elif choice == "7":
                    trajectory = robot.plan_square_trajectory(250, 150, side_length=80)
                    if trajectory is not None:
                        robot.execute_trajectory(trajectory, trajectory_name="trajectoire carrée")
                elif choice == "8":
                    trajectory = robot.plan_circle_trajectory(230, 140, radius=35)
                    if trajectory is not None:
                        robot.execute_trajectory(trajectory, trajectory_name="trajectoire circulaire")
                elif choice == "9":
                    robot.emergency_stop()
                elif choice == "0":
                    break
                else:
                    print("Choix invalide")
    except Exception as exc:
        print(f"Erreur: {exc}")


def main():
    interactive_demo()


if __name__ == "__main__":
    main()
