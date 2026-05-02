"""
Module de cinématique pour le bras robotique 2DDL
Implémente la cinématique directe et inverse
"""

import numpy as np
from typing import Iterable, Tuple, Optional

try:
    from .config import RobotConfig
except ImportError:
    from config import RobotConfig


class Kinematics:
    """Classe pour les calculs de cinématique directe et inverse"""
    
    def __init__(self, config: RobotConfig):
        """
        Initialise le module de cinématique
        
        Args:
            config: Configuration du robot
        """
        self.config = config
        self.L1 = config.L1
        self.L2 = config.L2
        
    def forward_kinematics(self, theta1: float, theta2: float) -> Tuple[float, float]:
        """
        Calcule la position cartésienne (x, y) de l'effecteur final
        à partir des angles articulaires
        
        Cinématique directe:
        x = L1*cos(θ1) + L2*cos(θ1 + θ2)
        y = L1*sin(θ1) + L2*sin(θ1 + θ2)
        
        Args:
            theta1: Angle de l'articulation 1 (radians)
            theta2: Angle de l'articulation 2 (radians)
            
        Returns:
            tuple: (x, y) position de l'effecteur final en mm
        """
        x = self.L1 * np.cos(theta1) + self.L2 * np.cos(theta1 + theta2)
        y = self.L1 * np.sin(theta1) + self.L2 * np.sin(theta1 + theta2)
        
        return x, y
    
    def inverse_kinematics(self, x: float, y: float, 
                          elbow_up: bool = True) -> Optional[Tuple[float, float]]:
        """
        Calcule les angles articulaires à partir de la position cartésienne
        
        Cinématique inverse (méthode géométrique):
        - Calcul de θ2 par la loi des cosinus
        - Calcul de θ1 par décomposition géométrique
        
        Args:
            x: Position x de l'effecteur final (mm)
            y: Position y de l'effecteur final (mm)
            elbow_up: True pour coude vers le haut, False pour coude vers le bas
            
        Returns:
            tuple: (theta1, theta2) angles en radians, ou None si position inaccessible
        """
        # Distance de l'origine à la cible
        r = np.sqrt(x**2 + y**2)
        
        # Vérifier si la position est atteignable
        if r > (self.L1 + self.L2) or r < abs(self.L1 - self.L2):
            return None
        
        # Calcul de θ2 par la loi des cosinus
        # cos(θ2) = (r² - L1² - L2²) / (2*L1*L2)
        cos_theta2 = (r**2 - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        
        # Vérifier que cos_theta2 est dans [-1, 1]
        if abs(cos_theta2) > 1.0:
            return None
        cos_theta2 = float(np.clip(cos_theta2, -1.0, 1.0))
        
        # Deux solutions possibles pour θ2
        if elbow_up:
            theta2 = np.arccos(cos_theta2)  # Solution coude vers le haut
        else:
            theta2 = -np.arccos(cos_theta2)  # Solution coude vers le bas
        
        # Calcul de θ1
        # θ1 = atan2(y, x) - atan2(L2*sin(θ2), L1 + L2*cos(θ2))
        k1 = self.L1 + self.L2 * np.cos(theta2)
        k2 = self.L2 * np.sin(theta2)
        theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)
        
        # Normaliser les angles dans [-π, π]
        theta1 = self._normalize_angle(theta1)
        theta2 = self._normalize_angle(theta2)
        
        # Vérifier les limites articulaires
        if not self.config.is_angle_valid(theta1, theta2):
            return None
        
        return theta1, theta2
    
    def inverse_kinematics_both_solutions(self, x: float, y: float) -> Tuple[Optional[Tuple[float, float]], 
                                                                               Optional[Tuple[float, float]]]:
        """
        Calcule les deux solutions possibles de la cinématique inverse
        
        Args:
            x: Position x de l'effecteur final (mm)
            y: Position y de l'effecteur final (mm)
            
        Returns:
            tuple: (solution_elbow_up, solution_elbow_down)
        """
        sol_up = self.inverse_kinematics(x, y, elbow_up=True)
        sol_down = self.inverse_kinematics(x, y, elbow_up=False)
        
        return sol_up, sol_down
    
    def jacobian(self, theta1: float, theta2: float) -> np.ndarray:
        """
        Calcule la matrice jacobienne du robot
        
        J = [[-L1*sin(θ1) - L2*sin(θ1+θ2), -L2*sin(θ1+θ2)],
             [ L1*cos(θ1) + L2*cos(θ1+θ2),  L2*cos(θ1+θ2)]]
        
        Args:
            theta1: Angle de l'articulation 1 (radians)
            theta2: Angle de l'articulation 2 (radians)
            
        Returns:
            np.ndarray: Matrice jacobienne 2x2
        """
        s1 = np.sin(theta1)
        c1 = np.cos(theta1)
        s12 = np.sin(theta1 + theta2)
        c12 = np.cos(theta1 + theta2)
        
        J = np.array([
            [-self.L1*s1 - self.L2*s12, -self.L2*s12],
            [ self.L1*c1 + self.L2*c12,  self.L2*c12]
        ])
        
        return J
    
    def get_joint_positions(self, theta1: float, theta2: float) -> dict:
        """
        Calcule les positions de toutes les articulations
        
        Args:
            theta1: Angle de l'articulation 1 (radians)
            theta2: Angle de l'articulation 2 (radians)
            
        Returns:
            dict: Positions de la base, articulation 1, articulation 2, et effecteur
        """
        # Base (origine)
        base = (0.0, 0.0)
        
        # Articulation 1 (extrémité du premier segment)
        joint1 = (self.L1 * np.cos(theta1), 
                  self.L1 * np.sin(theta1))
        
        # Effecteur final (extrémité du deuxième segment)
        end_effector = self.forward_kinematics(theta1, theta2)
        
        return {
            'base': base,
            'joint1': joint1,
            'end_effector': end_effector
        }
    
    def is_position_reachable(self, x: float, y: float) -> bool:
        """
        Vérifie si une position est atteignable par le robot
        
        Args:
            x: Position x (mm)
            y: Position y (mm)
            
        Returns:
            bool: True si la position est atteignable
        """
        r = np.sqrt(x**2 + y**2)
        return abs(self.L1 - self.L2) <= r <= (self.L1 + self.L2)
    
    def get_workspace_boundary(self, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Génère les points de la frontière de l'espace de travail
        
        Args:
            num_points: Nombre de points à générer
            
        Returns:
            tuple: (x_points, y_points) coordonnées des points de la frontière
        """
        angles = np.linspace(0, 2*np.pi, num_points)
        
        # Cercle extérieur (rayon maximum)
        r_max = self.L1 + self.L2
        x_outer = r_max * np.cos(angles)
        y_outer = r_max * np.sin(angles)
        
        # Cercle intérieur (rayon minimum)
        r_min = abs(self.L1 - self.L2)
        x_inner = r_min * np.cos(angles)
        y_inner = r_min * np.sin(angles)
        
        return (x_outer, y_outer), (x_inner, y_inner)
    
    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """
        Normalise un angle dans l'intervalle [-π, π]
        
        Args:
            angle: Angle en radians
            
        Returns:
            float: Angle normalisé
        """
        while angle > np.pi:
            angle -= 2 * np.pi
        while angle < -np.pi:
            angle += 2 * np.pi
        return angle
    
    def compute_trajectory(self, start_pos: Tuple[float, float], 
                          end_pos: Tuple[float, float],
                          num_points: int = 50,
                          elbow_up: bool = True) -> Optional[np.ndarray]:
        """
        Calcule une trajectoire linéaire dans l'espace cartésien
        
        Args:
            start_pos: Position de départ (x, y)
            end_pos: Position d'arrivée (x, y)
            num_points: Nombre de points de la trajectoire
            elbow_up: Configuration du coude
            
        Returns:
            np.ndarray: Tableau de shape (num_points, 4) contenant [x, y, theta1, theta2]
                       ou None si la trajectoire n'est pas réalisable
        """
        num_points = max(2, int(num_points))
        
        # Interpolation linéaire dans l'espace cartésien
        x_traj = np.linspace(start_pos[0], end_pos[0], num_points)
        y_traj = np.linspace(start_pos[1], end_pos[1], num_points)
        
        trajectory = []
        
        for x, y in zip(x_traj, y_traj):
            # Calculer la cinématique inverse pour chaque point
            result = self.inverse_kinematics(x, y, elbow_up)
            
            if result is None:
                return None  # Trajectoire non réalisable
            
            theta1, theta2 = result
            trajectory.append([x, y, theta1, theta2])
        
        return np.array(trajectory)
    
    def compute_polyline_trajectory(
        self,
        waypoints: Iterable[Tuple[float, float]],
        points_per_segment: int = 20,
        elbow_up: bool = True
    ) -> Optional[np.ndarray]:
        """
        Calcule une trajectoire passant par une suite de points.
        
        Args:
            waypoints: Suite de positions cartésiennes (x, y)
            points_per_segment: Nombre de points interpolés par segment
            elbow_up: Configuration du coude
            
        Returns:
            np.ndarray: Trajectoire complète [x, y, theta1, theta2] ou None
        """
        waypoints = list(waypoints)
        if len(waypoints) < 2:
            return None
        
        segments = []
        for index in range(len(waypoints) - 1):
            segment = self.compute_trajectory(
                waypoints[index],
                waypoints[index + 1],
                num_points=max(2, int(points_per_segment)),
                elbow_up=elbow_up
            )
            if segment is None:
                return None
            
            if segments:
                segment = segment[1:]
            segments.append(segment)
        
        return np.vstack(segments) if segments else None
    
    def compute_circular_trajectory(
        self,
        center: Tuple[float, float],
        radius: float,
        num_points: int = 72,
        elbow_up: bool = True,
        closed: bool = True
    ) -> Optional[np.ndarray]:
        """
        Calcule une trajectoire circulaire dans l'espace cartésien.
        
        Args:
            center: Centre du cercle (x, y)
            radius: Rayon du cercle
            num_points: Nombre de points sur le cercle
            elbow_up: Configuration du coude
            closed: Fermer la trajectoire sur le premier point
            
        Returns:
            np.ndarray: Trajectoire [x, y, theta1, theta2] ou None
        """
        num_points = max(8, int(num_points))
        stop = 2 * np.pi if closed else 2 * np.pi * (num_points - 1) / num_points
        angles = np.linspace(0.0, stop, num_points, endpoint=closed)
        
        trajectory = []
        for angle in angles:
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            result = self.inverse_kinematics(x, y, elbow_up)
            if result is None:
                return None
            theta1, theta2 = result
            trajectory.append([x, y, theta1, theta2])
        
        return np.array(trajectory)
    
    def compute_pick_trajectory(
        self,
        target_x: float,
        target_y: float,
        approach_height: float = 50.0,
        elbow_up: bool = True,
        num_points_per_phase: int = 15
    ) -> Optional[np.ndarray]:
        """
        Calcule une trajectoire de saisie (pick) avec approche verticale.
        
        La trajectoire se compose de 3 phases:
        1. Approche: déplacement vers la position au-dessus de l'objet
        2. Descente: descente verticale vers l'objet
        3. Remontée: remontée verticale après saisie
        
        Args:
            target_x: Position X de l'objet en mm
            target_y: Position Y de l'objet en mm
            approach_height: Hauteur d'approche au-dessus de l'objet en mm
            elbow_up: Configuration du coude
            num_points_per_phase: Nombre de points par phase
            
        Returns:
            np.ndarray: Trajectoire complète [x, y, theta1, theta2] ou None
        """
        # Position d'approche (au-dessus de l'objet)
        approach_x = target_x
        approach_y = target_y + approach_height
        
        # Vérifier que toutes les positions sont atteignables
        if not self.is_position_reachable(approach_x, approach_y):
            return None
        if not self.is_position_reachable(target_x, target_y):
            return None
        
        # Phase 1: Approche (position actuelle -> au-dessus de l'objet)
        # Note: La position actuelle sera gérée par le contrôleur
        # Ici on génère juste la descente et remontée
        
        # Phase 2: Descente verticale
        descent = self.compute_trajectory(
            (approach_x, approach_y),
            (target_x, target_y),
            num_points=num_points_per_phase,
            elbow_up=elbow_up
        )
        
        if descent is None:
            return None
        
        # Phase 3: Remontée verticale (après saisie)
        ascent = self.compute_trajectory(
            (target_x, target_y),
            (approach_x, approach_y),
            num_points=num_points_per_phase,
            elbow_up=elbow_up
        )
        
        if ascent is None:
            return None
        
        # Combiner descente et remontée
        return np.vstack([descent, ascent[1:]])  # Éviter la duplication du point de saisie
    
    def compute_place_trajectory(
        self,
        target_x: float,
        target_y: float,
        drop_height: float = 30.0,
        elbow_up: bool = True,
        num_points_per_phase: int = 15
    ) -> Optional[np.ndarray]:
        """
        Calcule une trajectoire de dépôt (place) avec approche verticale.
        
        La trajectoire se compose de 3 phases:
        1. Approche: déplacement vers la position au-dessus de la zone
        2. Descente: descente verticale vers la zone de dépôt
        3. Remontée: remontée verticale après dépôt
        
        Args:
            target_x: Position X de la zone de dépôt en mm
            target_y: Position Y de la zone de dépôt en mm
            drop_height: Hauteur au-dessus de la zone pour le dépôt en mm
            elbow_up: Configuration du coude
            num_points_per_phase: Nombre de points par phase
            
        Returns:
            np.ndarray: Trajectoire complète [x, y, theta1, theta2] ou None
        """
        # Position d'approche (au-dessus de la zone)
        approach_x = target_x
        approach_y = target_y + drop_height
        
        # Position de dépôt (légèrement au-dessus de la zone)
        drop_x = target_x
        drop_y = target_y + self.config.drop_height
        
        # Vérifier que toutes les positions sont atteignables
        if not self.is_position_reachable(approach_x, approach_y):
            return None
        if not self.is_position_reachable(drop_x, drop_y):
            return None
        
        # Phase 1: Descente vers position de dépôt
        descent = self.compute_trajectory(
            (approach_x, approach_y),
            (drop_x, drop_y),
            num_points=num_points_per_phase,
            elbow_up=elbow_up
        )
        
        if descent is None:
            return None
        
        # Phase 2: Remontée après dépôt
        ascent = self.compute_trajectory(
            (drop_x, drop_y),
            (approach_x, approach_y),
            num_points=num_points_per_phase,
            elbow_up=elbow_up
        )
        
        if ascent is None:
            return None
        
        # Combiner descente et remontée
        return np.vstack([descent, ascent[1:]])  # Éviter la duplication du point de dépôt
    
    def compute_pick_and_place_trajectory(
        self,
        pick_x: float,
        pick_y: float,
        place_x: float,
        place_y: float,
        approach_height: float = 50.0,
        drop_height: float = 30.0,
        elbow_up: bool = True,
        num_points_transfer: int = 30
    ) -> Optional[np.ndarray]:
        """
        Calcule une trajectoire complète pick & place.
        
        Séquence complète:
        1. Descente vers l'objet
        2. Remontée avec l'objet
        3. Transfert vers la zone de dépôt
        4. Descente vers la zone
        5. Remontée après dépôt
        
        Args:
            pick_x: Position X de l'objet à saisir
            pick_y: Position Y de l'objet à saisir
            place_x: Position X de la zone de dépôt
            place_y: Position Y de la zone de dépôt
            approach_height: Hauteur d'approche pour la saisie
            drop_height: Hauteur d'approche pour le dépôt
            elbow_up: Configuration du coude
            num_points_transfer: Nombre de points pour le transfert
            
        Returns:
            np.ndarray: Trajectoire complète ou None
        """
        # Trajectoire de saisie
        pick_traj = self.compute_pick_trajectory(
            pick_x, pick_y,
            approach_height=approach_height,
            elbow_up=elbow_up
        )
        
        if pick_traj is None:
            return None
        
        # Position après saisie (en haut)
        pick_up_x = pick_x
        pick_up_y = pick_y + approach_height
        
        # Position avant dépôt (en haut)
        place_up_x = place_x
        place_up_y = place_y + drop_height
        
        # Trajectoire de transfert (en hauteur)
        transfer_traj = self.compute_trajectory(
            (pick_up_x, pick_up_y),
            (place_up_x, place_up_y),
            num_points=num_points_transfer,
            elbow_up=elbow_up
        )
        
        if transfer_traj is None:
            return None
        
        # Trajectoire de dépôt
        place_traj = self.compute_place_trajectory(
            place_x, place_y,
            drop_height=drop_height,
            elbow_up=elbow_up
        )
        
        if place_traj is None:
            return None
        
        # Combiner toutes les phases
        # pick_traj se termine en haut, transfer commence en haut
        # transfer se termine en haut, place commence en haut
        return np.vstack([
            pick_traj,
            transfer_traj[1:],  # Éviter duplication
            place_traj[1:]      # Éviter duplication
        ])


if __name__ == "__main__":
    # Tests du module de cinématique
    try:
        from .config import config
    except ImportError:
        from config import config
    
    kin = Kinematics(config)
    
    print("=== Test de la Cinématique ===\n")
    
    # Test 1: Cinématique directe
    print("1. Cinématique Directe:")
    theta1, theta2 = np.pi/4, np.pi/6
    x, y = kin.forward_kinematics(theta1, theta2)
    print(f"   theta1={np.degrees(theta1):.1f} deg, theta2={np.degrees(theta2):.1f} deg")
    print(f"   Position: x={x:.2f}mm, y={y:.2f}mm\n")
    
    # Test 2: Cinématique inverse
    print("2. Cinématique Inverse:")
    target_x, target_y = 250.0, 150.0
    result = kin.inverse_kinematics(target_x, target_y, elbow_up=True)
    if result:
        theta1_calc, theta2_calc = result
        print(f"   Position cible: x={target_x:.2f}mm, y={target_y:.2f}mm")
        print(
            f"   theta1={np.degrees(theta1_calc):.1f} deg, "
            f"theta2={np.degrees(theta2_calc):.1f} deg"
        )
        
        # Vérification
        x_check, y_check = kin.forward_kinematics(theta1_calc, theta2_calc)
        error = np.sqrt((x_check - target_x)**2 + (y_check - target_y)**2)
        print(f"   Vérification: x={x_check:.2f}mm, y={y_check:.2f}mm")
        print(f"   Erreur: {error:.4f}mm\n")
    else:
        print(f"   Position {target_x}, {target_y} non atteignable!\n")
    
    # Test 3: Deux solutions
    print("3. Deux Solutions de la Cinématique Inverse:")
    sol_up, sol_down = kin.inverse_kinematics_both_solutions(target_x, target_y)
    if sol_up:
        print(
            f"   Coude vers le haut: theta1={np.degrees(sol_up[0]):.1f} deg, "
            f"theta2={np.degrees(sol_up[1]):.1f} deg"
        )
    if sol_down:
        print(
            f"   Coude vers le bas: theta1={np.degrees(sol_down[0]):.1f} deg, "
            f"theta2={np.degrees(sol_down[1]):.1f} deg"
        )
    print()
    
    # Test 4: Jacobienne
    print("4. Matrice Jacobienne:")
    J = kin.jacobian(theta1, theta2)
    print(f"   A theta1={np.degrees(theta1):.1f} deg, theta2={np.degrees(theta2):.1f} deg:")
    print(f"   J = \n{J}\n")
    
    # Test 5: Espace de travail
    print("5. Espace de Travail:")
    print(f"   Rayon max: {config.L1 + config.L2:.2f}mm")
    print(f"   Rayon min: {abs(config.L1 - config.L2):.2f}mm")
    print(f"   Position (100, 100) atteignable: {kin.is_position_reachable(100, 100)}")
    print(f"   Position (500, 500) atteignable: {kin.is_position_reachable(500, 500)}")

# Made with Bob
