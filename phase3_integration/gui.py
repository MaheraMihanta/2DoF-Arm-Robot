"""
Interface graphique pour le contrôle du bras robotique.
Ajoute une visualisation animée directement dans la fenêtre Tkinter.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional

import numpy as np

try:
    from ..phase1_simulation.config import RobotConfig
    from ..phase1_simulation.gripper import Gripper
    from ..phase1_simulation.objects import ObjectManager
    from ..phase1_simulation.pick_place_scenarios import ColorSortingScenario, ScenarioState
    from .robot_controller import ControlMode, RobotController
except ImportError:
    CURRENT_DIR = os.path.dirname(__file__)
    sys.path.insert(0, os.path.join(CURRENT_DIR, "..", "phase1_simulation"))
    sys.path.insert(0, CURRENT_DIR)

    from config import RobotConfig
    from gripper import Gripper
    from objects import ObjectManager
    from pick_place_scenarios import ColorSortingScenario, ScenarioState
    from robot_controller import ControlMode, RobotController


class RobotGUI:
    """Interface graphique complète pour le robot 2DDL."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Contrôle Bras Robotique 2DDL")
        self.root.geometry("1280x780")
        self.root.minsize(1120, 720)

        self.config = RobotConfig()
        self.robot: Optional[RobotController] = None
        self.is_connected = False

        self.mode_var = tk.StringVar(value="simulation")
        self.port_var = tk.StringVar(value=self.config.grbl_port)
        self.theta1_var = tk.DoubleVar(value=0.0)
        self.theta2_var = tk.DoubleVar(value=0.0)
        self.x_var = tk.DoubleVar(value=250.0)
        self.y_var = tk.DoubleVar(value=150.0)
        self.elbow_var = tk.BooleanVar(value=True)
        self.feed_rate_var = tk.DoubleVar(value=1000.0)

        self.traj_x_var = tk.DoubleVar(value=250.0)
        self.traj_y_var = tk.DoubleVar(value=180.0)
        self.traj_points_var = tk.IntVar(value=40)

        self.shape_center_x_var = tk.DoubleVar(value=240.0)
        self.shape_center_y_var = tk.DoubleVar(value=150.0)
        self.square_side_var = tk.DoubleVar(value=80.0)
        self.circle_radius_var = tk.DoubleVar(value=35.0)
        self.zigzag_width_var = tk.DoubleVar(value=120.0)
        self.zigzag_height_var = tk.DoubleVar(value=90.0)
        self.zigzag_passes_var = tk.IntVar(value=6)

        # Variables pour Pick & Place
        self.pp_num_cubes_var = tk.IntVar(value=6)
        self.pp_scenario: Optional[ColorSortingScenario] = None
        self.pp_gripper: Optional[Gripper] = None
        self.pp_object_manager: Optional[ObjectManager] = None
        self.pp_state_var = tk.StringVar(value="Non initialisé")
        self.pp_score_var = tk.StringVar(value="Score: 0/0")
        self.pp_progress_var = tk.StringVar(value="Progression: 0%")

        self.status_text_var = tk.StringVar(value="Non connecté")
        self.motion_text_var = tk.StringVar(value="Repos")
        self.live_mode_var = tk.StringVar(value="Mode: simulation")
        self.live_position_var = tk.StringVar(value="X: 0.0 mm | Y: 0.0 mm")
        self.live_angles_var = tk.StringVar(value="θ1: 0.0° | θ2: 0.0°")

        self.planned_trajectory = None
        self.planned_trajectory_name = ""
        self.live_snapshot = None
        self._pending_snapshot = None
        self._snapshot_job_scheduled = False

        self.canvas_width = 560
        self.canvas_height = 560

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        self.create_widgets()
        self.draw_live_view()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left_panel = ttk.Frame(main_pane)
        right_panel = ttk.Frame(main_pane)
        main_pane.add(left_panel, weight=3)
        main_pane.add(right_panel, weight=2)

        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(notebook)
        trajectory_frame = ttk.Frame(notebook)
        pick_place_frame = ttk.Frame(notebook)
        config_frame = ttk.Frame(notebook)
        console_frame = ttk.Frame(notebook)

        notebook.add(control_frame, text="Contrôle")
        notebook.add(trajectory_frame, text="Trajectoires")
        notebook.add(pick_place_frame, text="Pick & Place")
        notebook.add(config_frame, text="Configuration")
        notebook.add(console_frame, text="Console")

        self.create_control_tab(control_frame)
        self.create_trajectory_tab(trajectory_frame)
        self.create_pick_place_tab(pick_place_frame)
        self.create_config_tab(config_frame)
        self.create_console_tab(console_frame)
        self.create_live_panel(right_panel)

        status_bar = ttk.Label(self.root, textvariable=self.status_text_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_control_tab(self, parent):
        conn_frame = ttk.LabelFrame(parent, text="Connexion", padding=10)
        conn_frame.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(conn_frame, text="Mode").grid(row=0, column=0, sticky=tk.W)
        ttk.Combobox(
            conn_frame,
            textvariable=self.mode_var,
            values=["simulation", "hardware", "hybrid"],
            state="readonly",
            width=14,
        ).grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(conn_frame, text="Port").grid(row=0, column=2, sticky=tk.W, padx=(18, 0))
        ttk.Entry(conn_frame, textvariable=self.port_var, width=12).grid(row=0, column=3, padx=6)

        self.connect_btn = ttk.Button(conn_frame, text="Connecter", command=self.connect)
        self.connect_btn.grid(row=0, column=4, padx=6)
        self.disconnect_btn = ttk.Button(
            conn_frame,
            text="Déconnecter",
            command=self.disconnect,
            state=tk.DISABLED,
        )
        self.disconnect_btn.grid(row=0, column=5, padx=6)

        angles_frame = ttk.LabelFrame(parent, text="Déplacement articulaire", padding=10)
        angles_frame.pack(fill=tk.X, padx=6, pady=6)
        angles_frame.columnconfigure(1, weight=1)

        ttk.Label(angles_frame, text="θ1 (degrés)").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(
            angles_frame,
            from_=-180,
            to=180,
            variable=self.theta1_var,
            orient=tk.HORIZONTAL,
            length=320,
        ).grid(row=0, column=1, padx=6, sticky=tk.EW)
        ttk.Entry(angles_frame, textvariable=self.theta1_var, width=10).grid(row=0, column=2, padx=6)

        ttk.Label(angles_frame, text="θ2 (degrés)").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(
            angles_frame,
            from_=-150,
            to=150,
            variable=self.theta2_var,
            orient=tk.HORIZONTAL,
            length=320,
        ).grid(row=1, column=1, padx=6, sticky=tk.EW)
        ttk.Entry(angles_frame, textvariable=self.theta2_var, width=10).grid(row=1, column=2, padx=6)

        ttk.Button(angles_frame, text="Déplacer", command=self.move_to_angles).grid(
            row=2,
            column=1,
            pady=(10, 0),
        )

        position_frame = ttk.LabelFrame(parent, text="Déplacement cartésien", padding=10)
        position_frame.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(position_frame, text="X (mm)").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(position_frame, textvariable=self.x_var, width=14).grid(row=0, column=1, padx=6)

        ttk.Label(position_frame, text="Y (mm)").grid(row=0, column=2, sticky=tk.W, padx=(18, 0))
        ttk.Entry(position_frame, textvariable=self.y_var, width=14).grid(row=0, column=3, padx=6)

        ttk.Checkbutton(
            position_frame,
            text="Coude vers le haut",
            variable=self.elbow_var,
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        ttk.Button(position_frame, text="Déplacer", command=self.move_to_position).grid(
            row=1,
            column=2,
            columnspan=2,
            pady=(8, 0),
        )

        motion_frame = ttk.LabelFrame(parent, text="Mouvement", padding=10)
        motion_frame.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(motion_frame, text="Vitesse d'avance (mm/min)").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(motion_frame, textvariable=self.feed_rate_var, width=14).grid(row=0, column=1, padx=6)

        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=6, pady=6)

        ttk.Button(action_frame, text="Home", command=self.home).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="Arrêt d'urgence", command=self.emergency_stop).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="Effacer trace", command=self.clear_visual_history).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="Rafraîchir", command=self.update_display).pack(side=tk.LEFT, padx=3)

        state_frame = ttk.LabelFrame(parent, text="État courant", padding=10)
        state_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.state_text = scrolledtext.ScrolledText(state_frame, height=14, width=74)
        self.state_text.pack(fill=tk.BOTH, expand=True)

    def create_trajectory_tab(self, parent):
        linear_frame = ttk.LabelFrame(parent, text="Trajectoire linéaire", padding=10)
        linear_frame.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(linear_frame, text="X cible (mm)").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(linear_frame, textvariable=self.traj_x_var, width=14).grid(row=0, column=1, padx=6)
        ttk.Label(linear_frame, text="Y cible (mm)").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(linear_frame, textvariable=self.traj_y_var, width=14).grid(row=0, column=3, padx=6)
        ttk.Label(linear_frame, text="Points").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(linear_frame, textvariable=self.traj_points_var, width=14).grid(row=1, column=1, padx=6, pady=(8, 0))

        ttk.Button(linear_frame, text="Planifier", command=self.plan_linear_trajectory).grid(
            row=1,
            column=2,
            padx=6,
            pady=(8, 0),
        )
        ttk.Button(linear_frame, text="Exécuter", command=self.execute_planned_trajectory).grid(
            row=1,
            column=3,
            padx=6,
            pady=(8, 0),
        )

        preset_frame = ttk.LabelFrame(parent, text="Trajectoires démonstratives", padding=10)
        preset_frame.pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(preset_frame, text="Centre X (mm)").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(preset_frame, textvariable=self.shape_center_x_var, width=12).grid(row=0, column=1, padx=6)
        ttk.Label(preset_frame, text="Centre Y (mm)").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(preset_frame, textvariable=self.shape_center_y_var, width=12).grid(row=0, column=3, padx=6)

        ttk.Label(preset_frame, text="Carré côté").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(preset_frame, textvariable=self.square_side_var, width=12).grid(row=1, column=1, padx=6, pady=(8, 0))
        ttk.Button(preset_frame, text="Carré", command=self.execute_square_trajectory).grid(
            row=1,
            column=2,
            padx=6,
            pady=(8, 0),
        )

        ttk.Label(preset_frame, text="Rayon cercle").grid(row=2, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(preset_frame, textvariable=self.circle_radius_var, width=12).grid(row=2, column=1, padx=6, pady=(8, 0))
        ttk.Button(preset_frame, text="Cercle", command=self.execute_circle_trajectory).grid(
            row=2,
            column=2,
            padx=6,
            pady=(8, 0),
        )

        ttk.Label(preset_frame, text="Zigzag largeur").grid(row=3, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(preset_frame, textvariable=self.zigzag_width_var, width=12).grid(row=3, column=1, padx=6, pady=(8, 0))
        ttk.Label(preset_frame, text="Hauteur").grid(row=3, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Entry(preset_frame, textvariable=self.zigzag_height_var, width=12).grid(row=3, column=3, padx=6, pady=(8, 0))
        ttk.Label(preset_frame, text="Passes").grid(row=4, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(preset_frame, textvariable=self.zigzag_passes_var, width=12).grid(row=4, column=1, padx=6, pady=(8, 0))
        ttk.Button(preset_frame, text="Zigzag", command=self.execute_zigzag_trajectory).grid(
            row=4,
            column=2,
            padx=6,
            pady=(8, 0),
        )

        info_frame = ttk.LabelFrame(parent, text="Prévisualisation et détails", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.trajectory_info = scrolledtext.ScrolledText(info_frame, height=18, width=74)
        self.trajectory_info.pack(fill=tk.BOTH, expand=True)

    def create_pick_place_tab(self, parent):
        """Crée l'onglet de démonstration Pick & Place."""
        
        # Frame de configuration
        config_frame = ttk.LabelFrame(parent, text="Configuration du scénario", padding=10)
        config_frame.pack(fill=tk.X, padx=6, pady=6)
        
        ttk.Label(config_frame, text="Nombre de cubes:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(config_frame, from_=2, to=12, textvariable=self.pp_num_cubes_var, width=10).grid(
            row=0, column=1, padx=6
        )
        
        ttk.Button(config_frame, text="Initialiser Scénario", command=self.pp_initialize_scenario).grid(
            row=0, column=2, padx=6
        )
        
        # Frame de contrôle
        control_frame = ttk.LabelFrame(parent, text="Contrôle du tri", padding=10)
        control_frame.pack(fill=tk.X, padx=6, pady=6)
        
        self.pp_start_btn = ttk.Button(
            control_frame, text="Démarrer Tri Automatique",
            command=self.pp_start_sorting, state=tk.DISABLED
        )
        self.pp_start_btn.grid(row=0, column=0, padx=6, pady=4)
        
        self.pp_pause_btn = ttk.Button(
            control_frame, text="Pause",
            command=self.pp_pause_sorting, state=tk.DISABLED
        )
        self.pp_pause_btn.grid(row=0, column=1, padx=6, pady=4)
        
        self.pp_reset_btn = ttk.Button(
            control_frame, text="Réinitialiser",
            command=self.pp_reset_scenario, state=tk.DISABLED
        )
        self.pp_reset_btn.grid(row=0, column=2, padx=6, pady=4)
        
        # Frame d'état
        status_frame = ttk.LabelFrame(parent, text="État du scénario", padding=10)
        status_frame.pack(fill=tk.X, padx=6, pady=6)
        
        ttk.Label(status_frame, textvariable=self.pp_state_var, font=("", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(status_frame, textvariable=self.pp_score_var).pack(anchor=tk.W, pady=2)
        ttk.Label(status_frame, textvariable=self.pp_progress_var).pack(anchor=tk.W, pady=2)
        
        # Frame d'historique des actions
        history_frame = ttk.LabelFrame(parent, text="Historique des actions", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        self.pp_history_text = scrolledtext.ScrolledText(history_frame, height=15, width=74)
        self.pp_history_text.pack(fill=tk.BOTH, expand=True)
        
        # Frame de visualisation des objets
        viz_frame = ttk.LabelFrame(parent, text="Visualisation des objets", padding=10)
        viz_frame.pack(fill=tk.X, padx=6, pady=6)
        
        self.pp_viz_canvas = tk.Canvas(
            viz_frame, width=680, height=120, bg="#f5f5f5",
            highlightthickness=1, highlightbackground="#bcc5d4"
        )
        self.pp_viz_canvas.pack(fill=tk.X)

    def create_config_tab(self, parent):
        info = (
            f"Longueur segment 1 (L1): {self.config.L1} mm\n"
            f"Longueur segment 2 (L2): {self.config.L2} mm\n\n"
            f"Limites θ1: [{np.degrees(self.config.theta1_min):.0f}°, {np.degrees(self.config.theta1_max):.0f}°]\n"
            f"Limites θ2: [{np.degrees(self.config.theta2_min):.0f}°, {np.degrees(self.config.theta2_max):.0f}°]\n\n"
            f"Pas par révolution: {self.config.steps_per_revolution}\n"
            f"Microstepping: {self.config.microsteps}\n"
            f"Pas par radian θ1: {self.config.steps_per_rad_1:.2f}\n"
            f"Pas par radian θ2: {self.config.steps_per_rad_2:.2f}\n\n"
            f"Espace de travail max: {self.config.L1 + self.config.L2:.1f} mm\n"
            f"Espace de travail min: {abs(self.config.L1 - self.config.L2):.1f} mm\n"
            f"Vitesse max θ1: {np.degrees(self.config.max_angular_velocity_1):.1f} °/s\n"
            f"Vitesse max θ2: {np.degrees(self.config.max_angular_velocity_2):.1f} °/s\n"
        )

        label = ttk.Label(parent, text=info, justify=tk.LEFT, padding=12)
        label.pack(anchor=tk.NW)

    def create_console_tab(self, parent):
        self.console_text = scrolledtext.ScrolledText(parent, height=30, width=80)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        redirector = ConsoleRedirector(self.console_text, self.original_stdout)
        sys.stdout = redirector
        sys.stderr = ConsoleRedirector(self.console_text, self.original_stderr)

    def create_live_panel(self, parent):
        live_frame = ttk.LabelFrame(parent, text="Visualisation temps réel", padding=10)
        live_frame.pack(fill=tk.BOTH, expand=True)

        status_row = ttk.Frame(live_frame)
        status_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(status_row, textvariable=self.live_mode_var).pack(side=tk.LEFT)
        ttk.Label(status_row, textvariable=self.motion_text_var).pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(
            live_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#fbfbfd",
            highlightthickness=1,
            highlightbackground="#bcc5d4",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        footer = ttk.Frame(live_frame)
        footer.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(footer, textvariable=self.live_position_var).pack(side=tk.LEFT)
        ttk.Label(footer, textvariable=self.live_angles_var).pack(side=tk.RIGHT)

    def connect(self):
        if self.is_connected:
            return

        try:
            mode = ControlMode(self.mode_var.get())
            port = None if mode == ControlMode.SIMULATION else self.port_var.get().strip()

            self.robot = RobotController(self.config, mode, port)
            self.robot.add_state_listener(self._handle_robot_state)

            self.is_connected = True
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.status_text_var.set(f"Connecté - mode {mode.value}")
            self.live_mode_var.set(f"Mode: {mode.value}")

            self.log(f"Connecté en mode {mode.value}")
            self.update_display()
        except Exception as exc:
            messagebox.showerror("Erreur de connexion", str(exc))
            self.log(f"Erreur de connexion: {exc}")

    def disconnect(self):
        if self.robot:
            try:
                self.robot.remove_state_listener(self._handle_robot_state)
            except Exception:
                pass
            self.robot.disconnect()
            self.robot = None

        self.is_connected = False
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.status_text_var.set("Non connecté")
        self.live_mode_var.set("Mode: simulation")
        self.motion_text_var.set("Repos")
        self.live_snapshot = None
        self.draw_live_view()
        self.log("Déconnecté")

    def _handle_robot_state(self, snapshot):
        self._pending_snapshot = snapshot
        if not self._snapshot_job_scheduled:
            self._snapshot_job_scheduled = True
            self.root.after(0, self._flush_pending_snapshot)

    def _flush_pending_snapshot(self):
        self._snapshot_job_scheduled = False
        snapshot = self._pending_snapshot
        self._pending_snapshot = None
        if snapshot is None:
            return

        self.live_snapshot = snapshot
        self.apply_snapshot(snapshot)

    def apply_snapshot(self, snapshot):
        theta1_deg = np.degrees(snapshot["theta1"])
        theta2_deg = np.degrees(snapshot["theta2"])

        self.theta1_var.set(round(theta1_deg, 2))
        self.theta2_var.set(round(theta2_deg, 2))
        self.x_var.set(round(snapshot["x"], 2))
        self.y_var.set(round(snapshot["y"], 2))

        busy_text = "En mouvement" if snapshot["is_busy"] else "Repos"
        if snapshot["trajectory_name"]:
            busy_text = (
                f"{busy_text} - {snapshot['trajectory_name']} "
                f"({snapshot['trajectory_index']}/{snapshot['trajectory_size']})"
            )
        self.motion_text_var.set(busy_text)
        self.live_mode_var.set(f"Mode: {snapshot['mode']}")
        self.live_position_var.set(f"X: {snapshot['x']:.1f} mm | Y: {snapshot['y']:.1f} mm")
        self.live_angles_var.set(f"θ1: {theta1_deg:.1f}° | θ2: {theta2_deg:.1f}°")

        if snapshot["last_error"]:
            self.status_text_var.set(snapshot["last_error"])
        else:
            self.status_text_var.set(f"Connecté - mode {snapshot['mode']}")

        self.render_state_text(snapshot)
        self.draw_live_view()

    def render_state_text(self, snapshot=None):
        if snapshot is None:
            if not self.robot:
                return
            snapshot = self.robot.get_state_snapshot()

        self.state_text.delete(1.0, tk.END)
        info = (
            "État actuel du robot\n\n"
            f"Mode: {snapshot['mode']}\n"
            f"Position: X={snapshot['x']:.2f} mm | Y={snapshot['y']:.2f} mm\n"
            f"Angles: θ1={np.degrees(snapshot['theta1']):.2f}° | θ2={np.degrees(snapshot['theta2']):.2f}°\n"
            f"Cible: X={snapshot['target_x']:.2f} mm | Y={snapshot['target_y']:.2f} mm\n"
            f"Trace mémorisée: {len(snapshot['history'])} points\n"
            f"GRBL connecté: {'Oui' if snapshot['grbl_connected'] else 'Non'}\n"
        )
        if snapshot["trajectory_name"]:
            info += (
                f"Trajectoire active: {snapshot['trajectory_name']} "
                f"({snapshot['trajectory_index']}/{snapshot['trajectory_size']})\n"
            )
        if snapshot["last_error"]:
            info += f"\nDernière erreur: {snapshot['last_error']}\n"

        self.state_text.insert(tk.END, info)

    def ensure_connected(self) -> bool:
        if not self.is_connected or not self.robot:
            messagebox.showwarning("Non connecté", "Veuillez d'abord vous connecter")
            return False
        return True

    def run_robot_task(self, description: str, task, success_message: Optional[str] = None):
        if not self.ensure_connected():
            return

        if self.robot and self.robot.is_busy:
            messagebox.showinfo("Robot occupé", "Un mouvement est déjà en cours.")
            return

        self.motion_text_var.set(f"{description}...")
        self.log(f"{description}...")

        def worker():
            success = False
            error_message = None
            try:
                success = bool(task())
            except Exception as exc:
                error_message = str(exc)

            def finalize():
                if error_message:
                    self.motion_text_var.set("Erreur")
                    self.status_text_var.set(error_message)
                    self.log(f"Erreur: {error_message}")
                    messagebox.showerror("Erreur", error_message)
                    return

                self.update_display()
                if success:
                    if success_message:
                        self.log(success_message)
                else:
                    self.motion_text_var.set("Échec")
                    if self.robot and self.robot.last_error:
                        self.status_text_var.set(self.robot.last_error)
                    messagebox.showerror("Erreur", "Le mouvement demandé n'a pas abouti.")

            self.root.after(0, finalize)

        threading.Thread(target=worker, daemon=True).start()

    def move_to_angles(self):
        theta1 = np.radians(self.theta1_var.get())
        theta2 = np.radians(self.theta2_var.get())
        feed_rate = self.feed_rate_var.get()

        self.run_robot_task(
            "Déplacement articulaire",
            lambda: self.robot.move_to_angles(theta1, theta2, feed_rate),
            success_message=(
                f"Position atteinte: θ1={np.degrees(theta1):.1f}°, "
                f"θ2={np.degrees(theta2):.1f}°"
            ),
        )

    def move_to_position(self):
        x = self.x_var.get()
        y = self.y_var.get()
        elbow_up = self.elbow_var.get()
        feed_rate = self.feed_rate_var.get()

        self.run_robot_task(
            "Déplacement cartésien",
            lambda: self.robot.move_to_position(x, y, elbow_up, feed_rate),
            success_message=f"Position atteinte: X={x:.1f} mm, Y={y:.1f} mm",
        )

    def home(self):
        self.run_robot_task("Retour à l'origine", lambda: self.robot.home(), success_message="Home terminé")

    def emergency_stop(self):
        if not self.ensure_connected():
            return
        self.robot.emergency_stop()
        self.motion_text_var.set("Arrêt d'urgence")
        self.log("Arrêt d'urgence envoyé")
        self.update_display()

    def clear_visual_history(self):
        if not self.ensure_connected():
            return
        self.robot.clear_position_history()
        self.draw_live_view()
        self.log("Trace graphique effacée")

    def plan_linear_trajectory(self):
        if not self.ensure_connected():
            return

        x = self.traj_x_var.get()
        y = self.traj_y_var.get()
        n = self.traj_points_var.get()
        trajectory = self.robot.plan_linear_trajectory(x, y, n, self.elbow_var.get())
        if trajectory is None:
            messagebox.showerror("Erreur", "Impossible de planifier cette trajectoire")
            return

        self.set_planned_trajectory(trajectory, "trajectoire linéaire")
        self.log(f"Trajectoire linéaire planifiée vers ({x:.1f}, {y:.1f})")

    def set_planned_trajectory(self, trajectory, name: str):
        self.planned_trajectory = trajectory
        self.planned_trajectory_name = name
        self.render_trajectory_info(trajectory, name)
        self.draw_live_view()

    def render_trajectory_info(self, trajectory, name: str):
        self.trajectory_info.delete(1.0, tk.END)
        if trajectory is None or len(trajectory) == 0:
            self.trajectory_info.insert(tk.END, "Aucune trajectoire planifiée.")
            return

        xs = trajectory[:, 0]
        ys = trajectory[:, 1]
        self.trajectory_info.insert(tk.END, f"{name}\n\n")
        self.trajectory_info.insert(tk.END, f"Points: {len(trajectory)}\n")
        self.trajectory_info.insert(
            tk.END,
            f"Départ: ({trajectory[0, 0]:.1f}, {trajectory[0, 1]:.1f}) mm\n",
        )
        self.trajectory_info.insert(
            tk.END,
            f"Arrivée: ({trajectory[-1, 0]:.1f}, {trajectory[-1, 1]:.1f}) mm\n",
        )
        self.trajectory_info.insert(
            tk.END,
            f"Emprise: X[{xs.min():.1f}, {xs.max():.1f}] | Y[{ys.min():.1f}, {ys.max():.1f}]\n\n",
        )

        preview_count = min(12, len(trajectory))
        for index in range(preview_count):
            point = trajectory[index]
            self.trajectory_info.insert(
                tk.END,
                (
                    f"{index + 1:02d}: X={point[0]:7.1f}  Y={point[1]:7.1f}  "
                    f"θ1={np.degrees(point[2]):7.2f}°  θ2={np.degrees(point[3]):7.2f}°\n"
                ),
            )

        if len(trajectory) > preview_count:
            self.trajectory_info.insert(tk.END, "...\n")

    def execute_planned_trajectory(self):
        if self.planned_trajectory is None:
            messagebox.showwarning("Aucune trajectoire", "Veuillez d'abord planifier une trajectoire.")
            return

        feed_rate = self.feed_rate_var.get()
        name = self.planned_trajectory_name or "trajectoire planifiée"
        self.run_robot_task(
            "Exécution de la trajectoire",
            lambda: self.robot.execute_trajectory(self.planned_trajectory, feed_rate, trajectory_name=name),
            success_message=f"{name.capitalize()} exécutée",
        )

    def execute_square_trajectory(self):
        if not self.ensure_connected():
            return

        trajectory = self.robot.plan_square_trajectory(
            self.shape_center_x_var.get(),
            self.shape_center_y_var.get(),
            side_length=self.square_side_var.get(),
            elbow_up=self.elbow_var.get(),
        )
        if trajectory is None:
            messagebox.showerror("Erreur", "Carré non réalisable dans l'espace de travail.")
            return

        self.set_planned_trajectory(trajectory, "trajectoire carrée")
        self.execute_planned_trajectory()

    def execute_circle_trajectory(self):
        if not self.ensure_connected():
            return

        trajectory = self.robot.plan_circle_trajectory(
            self.shape_center_x_var.get(),
            self.shape_center_y_var.get(),
            radius=self.circle_radius_var.get(),
            elbow_up=self.elbow_var.get(),
        )
        if trajectory is None:
            messagebox.showerror("Erreur", "Cercle non réalisable dans l'espace de travail.")
            return

        self.set_planned_trajectory(trajectory, "trajectoire circulaire")
        self.execute_planned_trajectory()

    def execute_zigzag_trajectory(self):
        if not self.ensure_connected():
            return

        origin_x = self.shape_center_x_var.get() - self.zigzag_width_var.get() / 2.0
        origin_y = self.shape_center_y_var.get() - self.zigzag_height_var.get() / 2.0
        trajectory = self.robot.plan_zigzag_trajectory(
            origin_x,
            origin_y,
            width=self.zigzag_width_var.get(),
            height=self.zigzag_height_var.get(),
            passes=self.zigzag_passes_var.get(),
            elbow_up=self.elbow_var.get(),
        )
        if trajectory is None:
            messagebox.showerror("Erreur", "Zigzag non réalisable dans l'espace de travail.")
            return

        self.set_planned_trajectory(trajectory, "trajectoire zigzag")
        self.execute_planned_trajectory()

    def update_display(self):
        if not self.robot:
            self.state_text.delete(1.0, tk.END)
            return
        snapshot = self.robot.get_state_snapshot()
        self.live_snapshot = snapshot
        self.apply_snapshot(snapshot)

    def get_canvas_scale(self) -> float:
        return self.config.get_scale_factor(self.canvas_width, self.canvas_height, margin=45)

    def world_to_canvas(self, x: float, y: float):
        scale = self.get_canvas_scale()
        cx = self.canvas_width / 2 + x * scale
        cy = self.canvas_height / 2 - y * scale
        return cx, cy

    def canvas_to_world(self, cx: float, cy: float):
        scale = self.get_canvas_scale()
        x = (cx - self.canvas_width / 2) / scale
        y = (self.canvas_height / 2 - cy) / scale
        return x, y

    def draw_live_view(self):
        self.canvas.delete("all")

        scale = self.get_canvas_scale()
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        r_max = (self.config.L1 + self.config.L2) * scale
        r_min = abs(self.config.L1 - self.config.L2) * scale

        self.draw_grid(scale)
        self.canvas.create_oval(
            center_x - r_max,
            center_y - r_max,
            center_x + r_max,
            center_y + r_max,
            outline="#d4def0",
            width=2,
        )
        if r_min > 1:
            self.canvas.create_oval(
                center_x - r_min,
                center_y - r_min,
                center_x + r_min,
                center_y + r_min,
                outline="#f1d8c9",
                width=2,
            )

        self.canvas.create_line(0, center_y, self.canvas_width, center_y, fill="#c2c7d0", width=1)
        self.canvas.create_line(center_x, 0, center_x, self.canvas_height, fill="#c2c7d0", width=1)

        # Dessiner les zones de dépôt et cubes si le scénario Pick & Place est actif
        if self.pp_object_manager:
            self.draw_drop_zones()
            self.draw_cubes()

        if self.planned_trajectory is not None:
            self.draw_polyline(self.planned_trajectory[:, :2], color="#c792ea", width=2, dash=(4, 3))

        if self.live_snapshot and self.live_snapshot["history"]:
            history = np.array(self.live_snapshot["history"])
            self.draw_polyline(history, color="#5d89ff", width=2)

        if self.live_snapshot:
            target = (self.live_snapshot["target_x"], self.live_snapshot["target_y"])
            self.draw_target(target, color="#15a34a")
            theta1 = self.live_snapshot["theta1"]
            theta2 = self.live_snapshot["theta2"]
            self.draw_robot(theta1, theta2)
            # Dessiner la pince après le robot
            if self.pp_gripper:
                self.draw_gripper(theta1, theta2)
        else:
            self.draw_robot(0.0, 0.0)
            if self.pp_gripper:
                self.draw_gripper(0.0, 0.0)

    def draw_grid(self, scale: float):
        spacing_mm = 50
        spacing_px = spacing_mm * scale
        if spacing_px < 15:
            return

        x = self.canvas_width / 2
        while x < self.canvas_width:
            self.canvas.create_line(x, 0, x, self.canvas_height, fill="#edf0f5")
            self.canvas.create_line(self.canvas_width - x, 0, self.canvas_width - x, self.canvas_height, fill="#edf0f5")
            x += spacing_px

        y = self.canvas_height / 2
        while y < self.canvas_height:
            self.canvas.create_line(0, y, self.canvas_width, y, fill="#edf0f5")
            self.canvas.create_line(0, self.canvas_height - y, self.canvas_width, self.canvas_height - y, fill="#edf0f5")
            y += spacing_px

    def draw_polyline(self, points, color: str, width: int = 2, dash=None):
        if len(points) < 2:
            return

        coords = []
        for x, y in points:
            cx, cy = self.world_to_canvas(float(x), float(y))
            coords.extend([cx, cy])

        self.canvas.create_line(*coords, fill=color, width=width, smooth=False, dash=dash)

    def draw_target(self, target, color: str):
        x, y = target
        cx, cy = self.world_to_canvas(x, y)
        size = 10
        self.canvas.create_line(cx - size, cy, cx + size, cy, fill=color, width=2)
        self.canvas.create_line(cx, cy - size, cx, cy + size, fill=color, width=2)
        self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, outline=color, width=2)

    def draw_robot(self, theta1: float, theta2: float):
        positions = self.robot.kinematics.get_joint_positions(theta1, theta2) if self.robot else {
            "base": (0.0, 0.0),
            "joint1": (self.config.L1, 0.0),
            "end_effector": (self.config.L1 + self.config.L2, 0.0),
        }

        base = self.world_to_canvas(*positions["base"])
        joint1 = self.world_to_canvas(*positions["joint1"])
        end_effector = self.world_to_canvas(*positions["end_effector"])

    
    def draw_drop_zones(self):
        """Dessine les zones de dépôt sur le canvas principal."""
        if not self.pp_object_manager:
            return
        
        color_map = {
            'red': '#ef4444',
            'blue': '#3b82f6',
            'green': '#22c55e',
            'yellow': '#eab308'
        }
        
        for zone in self.pp_object_manager.drop_zones:
            cx, cy = self.world_to_canvas(zone.x, zone.y)
            scale = self.get_canvas_scale()
            zone_size = int(zone.size * scale)
            
            # Rectangle de la zone avec couleur claire et transparence
            light_color = color_map.get(zone.color, '#cccccc')
            self.canvas.create_rectangle(
                cx - zone_size // 2, cy - zone_size // 2,
                cx + zone_size // 2, cy + zone_size // 2,
                fill=light_color, outline=light_color, width=2,
                stipple='gray50'  # Motif hachuré
            )
    
    def draw_cubes(self):
        """Dessine les cubes sur le canvas principal."""
        if not self.pp_object_manager:
            return
        
        color_map = {
            'red': '#ef4444',
            'blue': '#3b82f6',
            'green': '#22c55e',
            'yellow': '#eab308'
        }
        
        scale = self.get_canvas_scale()
        
        for cube in self.pp_object_manager.cubes:
            cx, cy = self.world_to_canvas(cube.x, cube.y)
            cube_size = int(cube.size * scale)
            
            # Rectangle du cube
            self.canvas.create_rectangle(
                cx - cube_size // 2, cy - cube_size // 2,
                cx + cube_size // 2, cy + cube_size // 2,
                fill=color_map.get(cube.color, '#cccccc'),
                outline='#000000', width=3 if cube.is_grasped else 1
            )
            
            # Indicateur si le cube est saisi
            if cube.is_grasped:
                cross_size = cube_size // 3
                self.canvas.create_line(
                    cx - cross_size, cy, cx + cross_size, cy,
                    fill='white', width=2
                )
                self.canvas.create_line(
                    cx, cy - cross_size, cx, cy + cross_size,
                    fill='white', width=2
                )
    
    def draw_gripper(self, theta1: float, theta2: float):
        """Dessine la pince sur le canvas principal."""
        if not self.pp_gripper:
            return
        
        # Obtenir les positions des articulations
        if self.robot:
            positions = self.robot.kinematics.get_joint_positions(theta1, theta2)
        else:
            # Position par défaut
            positions = {
                "base": (0.0, 0.0),
                "joint1": (self.config.L1 * np.cos(theta1), self.config.L1 * np.sin(theta1)),
                "end_effector": (
                    self.config.L1 * np.cos(theta1) + self.config.L2 * np.cos(theta1 + theta2),
                    self.config.L1 * np.sin(theta1) + self.config.L2 * np.sin(theta1 + theta2)
                )
            }
        
        end_x, end_y = positions['end_effector']
        joint1_x, joint1_y = positions['joint1']
        
        # Calculer l'angle de l'effecteur
        angle = np.arctan2(end_y - joint1_y, end_x - joint1_x)
        
        # Position de la pince (prolongement de l'effecteur)
        gripper_x = end_x + self.config.gripper_length * np.cos(angle)
        gripper_y = end_y + self.config.gripper_length * np.sin(angle)
        
        # Convertir en coordonnées canvas
        end_canvas = self.world_to_canvas(end_x, end_y)
        gripper_canvas = self.world_to_canvas(gripper_x, gripper_y)
        
        # Dessiner le bras de la pince
        self.canvas.create_line(
            *end_canvas, *gripper_canvas,
            fill='#666666', width=4
        )
        
        # Calculer les positions des mâchoires
        half_width = self.pp_gripper.current_width / 2.0
        perpendicular_angle = angle + np.pi / 2
        
        jaw1_x = gripper_x + half_width * np.cos(perpendicular_angle)
        jaw1_y = gripper_y + half_width * np.sin(perpendicular_angle)
        jaw2_x = gripper_x - half_width * np.cos(perpendicular_angle)
        jaw2_y = gripper_y - half_width * np.sin(perpendicular_angle)
        
        jaw1_canvas = self.world_to_canvas(jaw1_x, jaw1_y)
        jaw2_canvas = self.world_to_canvas(jaw2_x, jaw2_y)
        
        # Couleur selon l'état de la pince
        if self.pp_gripper.is_closed():
            jaw_color = '#c82020'  # Rouge fermé
        elif self.pp_gripper.is_open():
            jaw_color = '#20c820'  # Vert ouvert
        else:
            jaw_color = '#ffa500'  # Orange en mouvement
        
        # Dessiner les mâchoires
        self.canvas.create_line(
            *gripper_canvas, *jaw1_canvas,
            fill=jaw_color, width=6
        )
        self.canvas.create_line(
            *gripper_canvas, *jaw2_canvas,
            fill=jaw_color, width=6
        )
        
        # Articulation de la pince
        self.canvas.create_oval(
            gripper_canvas[0] - 8, gripper_canvas[1] - 8,
            gripper_canvas[0] + 8, gripper_canvas[1] + 8,
            fill='#333333', outline='#000000', width=2
        )

    def on_canvas_click(self, event):
        if not self.ensure_connected():
            return

        x, y = self.canvas_to_world(event.x, event.y)
        self.x_var.set(round(x, 2))
        self.y_var.set(round(y, 2))
        self.move_to_position()

    def log(self, message: str):
        print(message)
    # ========== Méthodes Pick & Place ==========
    
    def pp_initialize_scenario(self):
        """Initialise le scénario de tri par couleur."""
        if not self.ensure_connected():
            return
        
        try:
            num_cubes = self.pp_num_cubes_var.get()
            
            # Créer les instances nécessaires
            self.pp_gripper = Gripper(self.config)
            self.pp_object_manager = ObjectManager(self.config)
            self.pp_scenario = ColorSortingScenario(
                self.config,
                self.robot.kinematics,
                self.pp_gripper,
                self.pp_object_manager
            )
            
            # Initialiser le scénario
            self.pp_scenario.initialize(num_cubes=num_cubes)
            
            # Mettre à jour l'interface
            self.pp_state_var.set(f"État: {self.pp_scenario.state.value}")
            self.pp_update_display()
            
            # Activer les boutons
            self.pp_start_btn.config(state=tk.NORMAL)
            self.pp_reset_btn.config(state=tk.NORMAL)
            
            self.log(f"Scénario Pick & Place initialisé avec {num_cubes} cubes")
            self.pp_log_action(f"Scénario initialisé avec {num_cubes} cubes")
            
        except Exception as exc:
            messagebox.showerror("Erreur d'initialisation", str(exc))
            self.log(f"Erreur d'initialisation Pick & Place: {exc}")
    
    def pp_start_sorting(self):
        """Démarre ou reprend le tri automatique."""
        if not self.pp_scenario:
            messagebox.showwarning("Scénario non initialisé", "Veuillez d'abord initialiser le scénario")
            return
        
        if self.pp_scenario.state == ScenarioState.IDLE:
            self.pp_scenario.start()
            self.pp_start_btn.config(text="Reprendre")
            self.pp_pause_btn.config(state=tk.NORMAL)
            self.log("Tri automatique démarré")
            self.pp_log_action("Tri automatique démarré")
            self.pp_execute_next_step()
            
        elif self.pp_scenario.state == ScenarioState.PAUSED:
            self.pp_scenario.resume()
            self.pp_start_btn.config(text="Reprendre")
            self.pp_pause_btn.config(state=tk.NORMAL)
            self.log("Tri automatique repris")
            self.pp_log_action("Tri automatique repris")
            self.pp_execute_next_step()
    
    def pp_pause_sorting(self):
        """Met en pause le tri automatique."""
        if self.pp_scenario and self.pp_scenario.state == ScenarioState.RUNNING:
            self.pp_scenario.pause()
            self.pp_state_var.set(f"État: {self.pp_scenario.state.value}")
            self.pp_pause_btn.config(state=tk.DISABLED)
            self.log("Tri automatique en pause")
            self.pp_log_action("Tri automatique en pause")
    
    def pp_reset_scenario(self):
        """Réinitialise le scénario."""
        if self.pp_scenario:
            self.pp_scenario.stop()
            self.pp_scenario = None
            self.pp_gripper = None
            self.pp_object_manager = None
            
            self.pp_state_var.set("Non initialisé")
            self.pp_score_var.set("Score: 0/0")
            self.pp_progress_var.set("Progression: 0%")
            
            self.pp_start_btn.config(state=tk.DISABLED, text="Démarrer Tri Automatique")
            self.pp_pause_btn.config(state=tk.DISABLED)
            self.pp_reset_btn.config(state=tk.DISABLED)
            
            self.pp_history_text.delete(1.0, tk.END)
            self.pp_viz_canvas.delete("all")
            
            self.log("Scénario Pick & Place réinitialisé")
    
    def pp_execute_next_step(self):
        """Exécute la prochaine étape du tri."""
        if not self.pp_scenario or self.pp_scenario.state != ScenarioState.RUNNING:
            return
        
        try:
            # Obtenir la position actuelle du robot
            if self.robot:
                x, y = self.robot.kinematics.forward_kinematics(
                    self.robot.current_theta1,
                    self.robot.current_theta2
                )
                current_pos = (x, y)
            else:
                current_pos = (0.0, 0.0)
            
            # Obtenir le prochain cube à trier
            next_cube = self.pp_scenario.get_next_cube_to_sort(current_pos)
            
            if next_cube is None:
                # Tri terminé
                self.pp_scenario.state = ScenarioState.COMPLETED
                self.pp_state_var.set(f"État: {self.pp_scenario.state.value}")
                self.pp_start_btn.config(state=tk.DISABLED)
                self.pp_pause_btn.config(state=tk.DISABLED)
                
                progress = self.pp_scenario.get_progress()
                self.log(f"Tri terminé! Score: {progress['sorted_count']}/{progress['total_count']}")
                self.pp_log_action(f"✓ Tri terminé! Score final: {progress['sorted_count']}/{progress['total_count']}")
                messagebox.showinfo("Tri terminé",
                    f"Tri terminé avec succès!\n\n"
                    f"Score: {progress['sorted_count']}/{progress['total_count']}\n"
                    f"Mouvements: {progress['total_moves']}\n"
                    f"Temps: {progress['elapsed_time']:.1f}s")
                return
            
            # Planifier la trajectoire pick & place
            result = self.pp_scenario.plan_complete_sort_move(next_cube)
            
            if result is None:
                self.log(f"Impossible de planifier le mouvement pour le cube {next_cube.color}")
                self.pp_log_action(f"✗ Échec: cube {next_cube.color} inaccessible")
                # Passer au cube suivant
                self.root.after(500, self.pp_execute_next_step)
                return
            
            trajectory, drop_zone = result
            
            # Exécuter la trajectoire
            self.pp_log_action(f"→ Saisie du cube {next_cube.color} à ({next_cube.x:.0f}, {next_cube.y:.0f})")
            
            def execute_trajectory():
                success = self.robot.execute_trajectory(
                    trajectory,
                    self.feed_rate_var.get(),
                    trajectory_name=f"Pick & Place {next_cube.color}"
                )
                
                if success:
                    # Marquer le cube comme trié
                    next_cube.set_position(drop_zone.x, drop_zone.y)
                    
                    # Les callbacks sont déjà appelés par le scénario
                    # on_cube_picked() et on_cube_placed() ne prennent pas de paramètres
                    self.pp_scenario.on_cube_placed()
                    
                    self.root.after(0, lambda: self.pp_log_action(
                        f"✓ Cube {next_cube.color} déposé dans la zone {next_cube.color}"
                    ))
                    self.root.after(0, self.pp_update_display)
                    
                    # Continuer avec le prochain cube
                    self.root.after(500, self.pp_execute_next_step)
                else:
                    self.root.after(0, lambda: self.pp_log_action(
                        f"✗ Échec du placement du cube {next_cube.color}"
                    ))
                    self.root.after(500, self.pp_execute_next_step)
            
            threading.Thread(target=execute_trajectory, daemon=True).start()
            
        except Exception as exc:
            self.log(f"Erreur lors de l'exécution: {exc}")
            self.pp_log_action(f"✗ Erreur: {exc}")
            messagebox.showerror("Erreur", str(exc))
    
    def pp_update_display(self):
        """Met à jour l'affichage du scénario Pick & Place."""
        if not self.pp_scenario:
            return
        
        progress = self.pp_scenario.get_progress()
        
        self.pp_state_var.set(f"État: {self.pp_scenario.state.value}")
        self.pp_score_var.set(
            f"Score: {progress['sorted_count']}/{progress['total_count']} "
            f"(Succès: {progress['successful_placements']}, Échecs: {progress['failed_attempts']})"
        )
        self.pp_progress_var.set(
            f"Progression: {progress['progress_percent']:.0f}% - "
            f"Mouvements: {progress['total_moves']} - "
            f"Temps: {progress['elapsed_time']:.1f}s"
        )
        
        # Dessiner la visualisation des objets
        self.pp_draw_objects_visualization()
    
    def pp_draw_objects_visualization(self):
        """Dessine une visualisation 2D complète avec le bras, les cubes et les zones."""
        if not self.pp_object_manager:
            return
        
        self.pp_viz_canvas.delete("all")
        
        # Dimensions du canvas
        canvas_width = 680
        canvas_height = 120
        
        # Calculer l'échelle pour adapter l'espace de travail au canvas
        # L'espace de travail du robot est environ 700mm de large (de -350 à +350)
        workspace_width = 700  # mm
        workspace_height = 400  # mm
        scale = min(canvas_width / workspace_width, canvas_height / workspace_height) * 0.8
        
        # Centre du canvas
        origin_x = canvas_width // 2
        origin_y = canvas_height // 2
        
        def world_to_canvas(x, y):
            """Convertit coordonnées monde (mm) en coordonnées canvas (pixels)."""
            cx = int(origin_x + x * scale)
            cy = int(origin_y - y * scale)
            return cx, cy
        
        # Définir les couleurs
        color_map = {
            'red': '#ef4444',
            'blue': '#3b82f6',
            'green': '#22c55e',
            'yellow': '#eab308'
        }
        
        # Dessiner l'espace de travail (cercles min/max)
        r_max = int((self.config.L1 + self.config.L2) * scale)
        r_min = int(abs(self.config.L1 - self.config.L2) * scale)
        
        self.pp_viz_canvas.create_oval(
            origin_x - r_max, origin_y - r_max,
            origin_x + r_max, origin_y + r_max,
            outline='#d4def0', width=1
        )
        if r_min > 1:
            self.pp_viz_canvas.create_oval(
                origin_x - r_min, origin_y - r_min,
                origin_x + r_min, origin_y + r_min,
                outline='#f1d8c9', width=1
            )
        
        # Dessiner les axes
        self.pp_viz_canvas.create_line(
            0, origin_y, canvas_width, origin_y,
            fill='#e0e0e0', width=1
        )
        self.pp_viz_canvas.create_line(
            origin_x, 0, origin_x, canvas_height,
            fill='#e0e0e0', width=1
        )
        
        # Dessiner les zones de dépôt
        for zone in self.pp_object_manager.drop_zones:
            cx, cy = world_to_canvas(zone.x, zone.y)
            zone_size = int(zone.size * scale)
            
            # Rectangle de la zone avec couleur claire
            light_color = color_map.get(zone.color, '#cccccc')
            self.pp_viz_canvas.create_rectangle(
                cx - zone_size // 2, cy - zone_size // 2,
                cx + zone_size // 2, cy + zone_size // 2,
                fill=light_color, outline=light_color, width=2,
                stipple='gray50'  # Motif hachuré pour différencier des cubes
            )
        
        # Dessiner les cubes
        for cube in self.pp_object_manager.cubes:
            cx, cy = world_to_canvas(cube.x, cube.y)
            cube_size = int(cube.size * scale)
            
            # Rectangle du cube
            self.pp_viz_canvas.create_rectangle(
                cx - cube_size // 2, cy - cube_size // 2,
                cx + cube_size // 2, cy + cube_size // 2,
                fill=color_map.get(cube.color, '#cccccc'),
                outline='#000000', width=2 if cube.is_grasped else 1
            )
            
            # Indicateur si le cube est saisi
            if cube.is_grasped:
                cross_size = cube_size // 3
                self.pp_viz_canvas.create_line(
                    cx - cross_size, cy, cx + cross_size, cy,
                    fill='white', width=2
                )
                self.pp_viz_canvas.create_line(
                    cx, cy - cross_size, cx, cy + cross_size,
                    fill='white', width=2
                )
        
        # Dessiner le bras robotique
        if self.robot:
            theta1 = self.robot.current_theta1
            theta2 = self.robot.current_theta2
            positions = self.robot.kinematics.get_joint_positions(theta1, theta2)
        else:
            # Position par défaut si pas de robot connecté
            theta1, theta2 = 0.0, 0.0
            positions = {
                "base": (0.0, 0.0),
                "joint1": (self.config.L1 * np.cos(theta1), self.config.L1 * np.sin(theta1)),
                "end_effector": (
                    self.config.L1 * np.cos(theta1) + self.config.L2 * np.cos(theta1 + theta2),
                    self.config.L1 * np.sin(theta1) + self.config.L2 * np.sin(theta1 + theta2)
                )
            }
        
        base = world_to_canvas(*positions["base"])
        joint1 = world_to_canvas(*positions["joint1"])
        end_effector = world_to_canvas(*positions["end_effector"])
        
        # Dessiner les segments du bras
        self.pp_viz_canvas.create_line(
            *base, *joint1,
            fill='#0a6fff', width=4, capstyle=tk.ROUND
        )
        self.pp_viz_canvas.create_line(
            *joint1, *end_effector,
            fill='#ff8c2b', width=4, capstyle=tk.ROUND
        )
        
        # Dessiner les articulations
        self.pp_viz_canvas.create_oval(
            base[0] - 6, base[1] - 6, base[0] + 6, base[1] + 6,
            fill='#737373', outline='#2b2b2b'
        )
        self.pp_viz_canvas.create_oval(
            joint1[0] - 5, joint1[1] - 5, joint1[0] + 5, joint1[1] + 5,
            fill='#ce2d2d', outline='#5f1111'
        )
        self.pp_viz_canvas.create_oval(
            end_effector[0] - 5, end_effector[1] - 5,
            end_effector[0] + 5, end_effector[1] + 5,
            fill='#16a34a', outline='#0f5e2d'
        )
        
        # Dessiner la pince
        if self.pp_gripper:
            # Calculer la position et l'angle de la pince
            end_x, end_y = positions['end_effector']
            joint1_x, joint1_y = positions['joint1']
            angle = np.arctan2(end_y - joint1_y, end_x - joint1_x)
            
            # Position de la pince (prolongement de l'effecteur)
            gripper_x = end_x + self.config.gripper_length * np.cos(angle)
            gripper_y = end_y + self.config.gripper_length * np.sin(angle)
            gripper_pos = world_to_canvas(gripper_x, gripper_y)
            
            # Dessiner le bras de la pince
            self.pp_viz_canvas.create_line(
                *end_effector, *gripper_pos,
                fill='#666666', width=2
            )
            
            # Calculer les positions des mâchoires
            half_width = self.pp_gripper.current_width / 2.0
            perpendicular_angle = angle + np.pi / 2
            
            jaw1_x = gripper_x + half_width * np.cos(perpendicular_angle)
            jaw1_y = gripper_y + half_width * np.sin(perpendicular_angle)
            jaw2_x = gripper_x - half_width * np.cos(perpendicular_angle)
            jaw2_y = gripper_y - half_width * np.sin(perpendicular_angle)
            
            jaw1_pos = world_to_canvas(jaw1_x, jaw1_y)
            jaw2_pos = world_to_canvas(jaw2_x, jaw2_y)
            
            # Couleur selon l'état de la pince
            if self.pp_gripper.is_closed():
                jaw_color = '#c82020'  # Rouge fermé
            elif self.pp_gripper.is_open():
                jaw_color = '#20c820'  # Vert ouvert
            else:
                jaw_color = '#ffa500'  # Orange en mouvement
            
            # Dessiner les mâchoires
            self.pp_viz_canvas.create_line(
                *gripper_pos, *jaw1_pos,
                fill=jaw_color, width=3
            )
            self.pp_viz_canvas.create_line(
                *gripper_pos, *jaw2_pos,
                fill=jaw_color, width=3
            )
            
            # Articulation de la pince
            self.pp_viz_canvas.create_oval(
                gripper_pos[0] - 4, gripper_pos[1] - 4,
                gripper_pos[0] + 4, gripper_pos[1] + 4,
                fill='#333333', outline='#000000'
            )
    
    def pp_log_action(self, message: str):
        """Ajoute un message dans l'historique des actions."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.pp_history_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.pp_history_text.see(tk.END)


    def on_close(self):
        self.disconnect()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.root.destroy()


class ConsoleRedirector:
    """Redirige stdout/stderr vers un widget Text."""

    def __init__(self, text_widget, fallback_stream):
        self.text_widget = text_widget
        self.fallback_stream = fallback_stream

    def write(self, message):
        if not message:
            return
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        if self.fallback_stream:
            self.fallback_stream.write(message)

    def flush(self):
        if self.fallback_stream:
            self.fallback_stream.flush()


def main():
    root = tk.Tk()
    app = RobotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
