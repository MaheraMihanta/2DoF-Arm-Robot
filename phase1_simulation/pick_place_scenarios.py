"""
Module de scénarios pick & place pour le bras robotique.
Implémente des scénarios de démonstration comme le tri d'objets par couleur.
"""

import time
from typing import List, Optional, Tuple, Dict
from enum import Enum
import numpy as np

try:
    from .config import RobotConfig
    from .kinematics import Kinematics
    from .gripper import Gripper
    from .objects import ObjectManager, ColoredCube, DropZone
except ImportError:
    from config import RobotConfig
    from kinematics import Kinematics
    from gripper import Gripper
    from objects import ObjectManager, ColoredCube, DropZone


class ScenarioState(Enum):
    """États possibles d'un scénario."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ColorSortingScenario:
    """
    Scénario de tri d'objets par couleur.
    
    Le bras robotique doit saisir des cubes colorés dispersés dans l'espace
    de travail et les placer dans les zones de dépôt correspondant à leur couleur.
    """
    
    def __init__(self, config: RobotConfig, kinematics: Kinematics, 
                 gripper: Gripper, object_manager: ObjectManager):
        """
        Initialise le scénario de tri.
        
        Args:
            config: Configuration du robot
            kinematics: Module de cinématique
            gripper: Pince du robot
            object_manager: Gestionnaire d'objets
        """
        self.config = config
        self.kinematics = kinematics
        self.gripper = gripper
        self.object_manager = object_manager
        
        self.state = ScenarioState.IDLE
        self.current_cube: Optional[ColoredCube] = None
        self.current_zone: Optional[DropZone] = None
        self.start_time = 0.0
        self.end_time = 0.0
        self.total_moves = 0
        self.successful_placements = 0
        self.failed_attempts = 0
        
        # Historique des actions
        self.action_log: List[str] = []
    
    def initialize(self, num_cubes: int = 4, colors: Optional[List[str]] = None):
        """
        Initialise le scénario avec des objets.
        
        Args:
            num_cubes: Nombre de cubes à créer
            colors: Liste des couleurs (générée aléatoirement si None)
        """
        self.state = ScenarioState.INITIALIZING
        self.action_log.clear()
        
        # Couleurs disponibles
        available_colors = ['red', 'blue', 'green', 'yellow']
        
        if colors is None:
            # Générer des couleurs aléatoires
            import random
            colors = [random.choice(available_colors) for _ in range(num_cubes)]
        
        # Créer les cubes
        self.object_manager.create_cubes(colors)
        
        # Créer les zones de dépôt pour toutes les couleurs présentes
        unique_colors = list(set(colors))
        self.object_manager.create_drop_zones(unique_colors)
        
        self.log_action(f"Scénario initialisé avec {num_cubes} cubes: {colors}")
        self.state = ScenarioState.IDLE
    
    def start(self):
        """Démarre le scénario."""
        if self.state != ScenarioState.IDLE:
            self.log_action("Erreur: Le scénario doit être en état IDLE pour démarrer")
            return False
        
        self.state = ScenarioState.RUNNING
        self.start_time = time.time()
        self.total_moves = 0
        self.successful_placements = 0
        self.failed_attempts = 0
        
        self.log_action("Scénario de tri démarré")
        return True
    
    def pause(self):
        """Met le scénario en pause."""
        if self.state == ScenarioState.RUNNING:
            self.state = ScenarioState.PAUSED
            self.log_action("Scénario mis en pause")
    
    def resume(self):
        """Reprend le scénario."""
        if self.state == ScenarioState.PAUSED:
            self.state = ScenarioState.RUNNING
            self.log_action("Scénario repris")
    
    def stop(self):
        """Arrête le scénario."""
        self.state = ScenarioState.IDLE
        self.end_time = time.time()
        self.log_action("Scénario arrêté")
    
    def get_next_cube_to_sort(self, current_position: Tuple[float, float]) -> Optional[ColoredCube]:
        """
        Trouve le prochain cube à trier (le plus proche non encore trié).
        
        Args:
            current_position: Position actuelle du robot (x, y)
            
        Returns:
            ColoredCube ou None si tous les cubes sont triés
        """
        # Trouver tous les cubes non triés
        unsorted_cubes = []
        for cube in self.object_manager.cubes:
            if cube.is_grasped:
                continue
            
            # Vérifier si le cube est déjà bien placé
            zone = self.object_manager.get_drop_zone(cube.color)
            if zone and zone.is_correct_placement(cube):
                continue
            
            unsorted_cubes.append(cube)
        
        if not unsorted_cubes:
            return None
        
        # Trouver le plus proche
        nearest = None
        min_distance = float('inf')
        
        for cube in unsorted_cubes:
            distance = np.hypot(cube.x - current_position[0], 
                              cube.y - current_position[1])
            if distance < min_distance:
                min_distance = distance
                nearest = cube
        
        return nearest
    
    def plan_pick_move(self, cube: ColoredCube) -> Optional[np.ndarray]:
        """
        Planifie une trajectoire pour saisir un cube.
        
        Args:
            cube: Cube à saisir
            
        Returns:
            np.ndarray: Trajectoire ou None
        """
        trajectory = self.kinematics.compute_pick_trajectory(
            cube.x,
            cube.y,
            approach_height=self.config.approach_height,
            elbow_up=True
        )
        
        if trajectory is None:
            self.log_action(f"Impossible de planifier la saisie du cube {cube.color} à ({cube.x:.1f}, {cube.y:.1f})")
        
        return trajectory
    
    def plan_place_move(self, zone: DropZone) -> Optional[np.ndarray]:
        """
        Planifie une trajectoire pour déposer dans une zone.
        
        Args:
            zone: Zone de dépôt
            
        Returns:
            np.ndarray: Trajectoire ou None
        """
        trajectory = self.kinematics.compute_place_trajectory(
            zone.x,
            zone.y,
            drop_height=self.config.approach_height,
            elbow_up=True
        )
        
        if trajectory is None:
            self.log_action(f"Impossible de planifier le dépôt dans la zone {zone.color} à ({zone.x:.1f}, {zone.y:.1f})")
        
        return trajectory
    
    def plan_complete_sort_move(self, cube: ColoredCube) -> Optional[Tuple[np.ndarray, DropZone]]:
        """
        Planifie une trajectoire complète pick & place pour un cube.
        
        Args:
            cube: Cube à trier
            
        Returns:
            tuple: (trajectoire, zone) ou None
        """
        # Trouver la zone de dépôt correspondante
        zone = self.object_manager.get_drop_zone(cube.color)
        if zone is None:
            self.log_action(f"Aucune zone de dépôt pour la couleur {cube.color}")
            return None
        
        # Planifier la trajectoire complète
        trajectory = self.kinematics.compute_pick_and_place_trajectory(
            pick_x=cube.x,
            pick_y=cube.y,
            place_x=zone.x,
            place_y=zone.y,
            approach_height=self.config.approach_height,
            drop_height=self.config.approach_height,
            elbow_up=True
        )
        
        if trajectory is None:
            self.log_action(f"Impossible de planifier le tri complet du cube {cube.color}")
            return None
        
        return trajectory, zone
    
    def execute_sort_step(self, current_position: Tuple[float, float]) -> Optional[Tuple[np.ndarray, str]]:
        """
        Exécute une étape du tri (saisir un cube et le placer).
        
        Args:
            current_position: Position actuelle du robot
            
        Returns:
            tuple: (trajectoire, description) ou None si le tri est terminé
        """
        if self.state != ScenarioState.RUNNING:
            return None
        
        # Trouver le prochain cube à trier
        cube = self.get_next_cube_to_sort(current_position)
        
        if cube is None:
            # Tri terminé
            self.state = ScenarioState.COMPLETED
            self.end_time = time.time()
            self.log_action("Tri terminé avec succès!")
            return None
        
        # Planifier le mouvement complet
        result = self.plan_complete_sort_move(cube)
        
        if result is None:
            self.failed_attempts += 1
            self.log_action(f"Échec de planification pour le cube {cube.color}")
            return None
        
        trajectory, zone = result
        self.current_cube = cube
        self.current_zone = zone
        self.total_moves += 1
        
        description = f"Tri du cube {cube.color} vers zone {zone.color}"
        self.log_action(description)
        
        return trajectory, description
    
    def on_cube_picked(self):
        """Appelé quand un cube est saisi."""
        if self.current_cube:
            self.current_cube.grasp()
            self.log_action(f"Cube {self.current_cube.color} saisi")
    
    def on_cube_placed(self):
        """Appelé quand un cube est déposé."""
        if self.current_cube and self.current_zone:
            # Placer le cube au centre de la zone
            self.current_cube.set_position(self.current_zone.x, self.current_zone.y)
            self.current_cube.release()
            
            # Vérifier si le placement est correct
            if self.current_zone.is_correct_placement(self.current_cube):
                self.successful_placements += 1
                self.log_action(f"Cube {self.current_cube.color} déposé correctement dans zone {self.current_zone.color}")
            else:
                self.log_action(f"Erreur: Cube {self.current_cube.color} mal placé")
            
            self.current_cube = None
            self.current_zone = None
    
    def get_progress(self) -> Dict[str, any]:
        """
        Retourne les informations de progression.
        
        Returns:
            dict: Statistiques du scénario
        """
        sorted_count, total = self.object_manager.get_sorting_progress()
        
        elapsed_time = 0.0
        if self.start_time > 0:
            if self.end_time > 0:
                elapsed_time = self.end_time - self.start_time
            else:
                elapsed_time = time.time() - self.start_time
        
        return {
            'state': self.state.value,
            'sorted_count': sorted_count,
            'total_count': total,
            'progress_percent': (sorted_count / total * 100) if total > 0 else 0,
            'total_moves': self.total_moves,
            'successful_placements': self.successful_placements,
            'failed_attempts': self.failed_attempts,
            'elapsed_time': elapsed_time,
            'current_cube_color': self.current_cube.color if self.current_cube else None,
            'is_complete': self.state == ScenarioState.COMPLETED
        }
    
    def log_action(self, message: str):
        """
        Enregistre une action dans l'historique.
        
        Args:
            message: Message à enregistrer
        """
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.action_log.append(log_entry)
        print(log_entry)
    
    def get_action_log(self) -> List[str]:
        """Retourne l'historique des actions."""
        return self.action_log.copy()
    
    def reset(self):
        """Réinitialise le scénario."""
        self.object_manager.reset()
        self.state = ScenarioState.IDLE
        self.current_cube = None
        self.current_zone = None
        self.start_time = 0.0
        self.end_time = 0.0
        self.total_moves = 0
        self.successful_placements = 0
        self.failed_attempts = 0
        self.action_log.clear()
        self.log_action("Scénario réinitialisé")


if __name__ == "__main__":
    # Test simple du module de scénarios
    print("=== Test du Module Pick & Place Scenarios ===\n")
    
    from config import RobotConfig
    
    config = RobotConfig()
    kinematics = Kinematics(config)
    gripper = Gripper(config)
    object_manager = ObjectManager(config)
    
    # Créer un scénario
    scenario = ColorSortingScenario(config, kinematics, gripper, object_manager)
    
    print("Test d'initialisation:")
    scenario.initialize(num_cubes=3, colors=['red', 'blue', 'green'])
    print(f"  État: {scenario.state.value}")
    print(f"  Cubes: {len(object_manager.cubes)}")
    print(f"  Zones: {len(object_manager.drop_zones)}")
    print()
    
    print("Test de démarrage:")
    scenario.start()
    print(f"  État: {scenario.state.value}")
    print()
    
    print("Test de progression:")
    progress = scenario.get_progress()
    for key, value in progress.items():
        print(f"  {key}: {value}")
    print()
    
    print("Test de recherche du prochain cube:")
    current_pos = (225.0, 125.0)
    next_cube = scenario.get_next_cube_to_sort(current_pos)
    if next_cube:
        print(f"  Prochain cube: {next_cube}")
        
        # Test de planification
        print("\nTest de planification de trajectoire:")
        result = scenario.plan_complete_sort_move(next_cube)
        if result:
            trajectory, zone = result
            print(f"  Trajectoire planifiée: {len(trajectory)} points")
            print(f"  Zone cible: {zone.color} à ({zone.x}, {zone.y})")
        else:
            print("  Échec de planification")
    
    print("\nHistorique des actions:")
    for log_entry in scenario.get_action_log():
        print(f"  {log_entry}")
    
    print("\nTests du module scenarios terminés")

# Made with Bob