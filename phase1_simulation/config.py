"""
Configuration du bras robotique 2DDL
Définit les paramètres physiques et de contrôle du bras
"""

import numpy as np


class RobotConfig:
    """Configuration du bras robotique 2 degrés de liberté"""
    
    def __init__(self):
        # Paramètres géométriques du bras (en mm)
        self.L1 = 200.0  # Longueur du premier segment (bras)
        self.L2 = 150.0  # Longueur du deuxième segment (avant-bras)
        
        # Limites angulaires (en radians)
        self.theta1_min = -np.pi      # -180°
        self.theta1_max = np.pi       # +180°
        self.theta2_min = -np.radians(150)  # -150°
        self.theta2_max = np.radians(150)   # +150°
        
        # Paramètres des moteurs pas à pas
        self.steps_per_revolution = 200  # Moteur standard (1.8° par pas)
        self.microsteps = 16             # Microstepping A4988
        self.gear_ratio_1 = 1.0          # Rapport de réduction moteur 1
        self.gear_ratio_2 = 1.0          # Rapport de réduction moteur 2
        
        # Calcul des pas par radian
        self.steps_per_rad_1 = (self.steps_per_revolution * self.microsteps * 
                                self.gear_ratio_1) / (2 * np.pi)
        self.steps_per_rad_2 = (self.steps_per_revolution * self.microsteps * 
                                self.gear_ratio_2) / (2 * np.pi)
        
        # Paramètres GRBL
        self.grbl_baudrate = 115200
        self.grbl_port = 'COM3'  # À adapter selon votre système
        
        # Vitesses maximales (en rad/s)
        self.max_angular_velocity_1 = np.pi / 2  # 90°/s
        self.max_angular_velocity_2 = np.pi / 2  # 90°/s
        
        # Accélérations maximales (en rad/s²)
        self.max_angular_acceleration_1 = np.pi  # 180°/s²
        self.max_angular_acceleration_2 = np.pi  # 180°/s²
        
        # Paramètres de simulation
        self.simulation_dt = 0.01  # Pas de temps (10ms)
        self.simulation_fps = 60   # Images par seconde
        self.min_animation_duration = 0.25
        self.max_animation_duration = 2.0
        
        # Couleurs pour la visualisation (RGB)
        self.color_base = (100, 100, 100)      # Gris
        self.color_link1 = (0, 120, 215)       # Bleu
        self.color_link2 = (255, 140, 0)       # Orange
        self.color_joint = (200, 0, 0)         # Rouge
        self.color_end_effector = (0, 200, 0)  # Vert
        self.color_trajectory = (150, 150, 255) # Bleu clair
        
        # Dimensions pour la visualisation (pixels)
        self.window_width = 800
        self.window_height = 600
        self.scale_factor = 0.7  # Facteur d'échelle mm -> pixels
        self.display_margin = 40
        
    def is_angle_valid(self, theta1, theta2):
        """
        Vérifie si les angles sont dans les limites autorisées
        
        Args:
            theta1: Angle de l'articulation 1 (radians)
            theta2: Angle de l'articulation 2 (radians)
            
        Returns:
            bool: True si les angles sont valides
        """
        return (self.theta1_min <= theta1 <= self.theta1_max and
                self.theta2_min <= theta2 <= self.theta2_max)
    
    def angles_to_steps(self, theta1, theta2):
        """
        Convertit les angles en nombre de pas moteur
        
        Args:
            theta1: Angle de l'articulation 1 (radians)
            theta2: Angle de l'articulation 2 (radians)
            
        Returns:
            tuple: (steps1, steps2) nombre de pas pour chaque moteur
        """
        steps1 = int(theta1 * self.steps_per_rad_1)
        steps2 = int(theta2 * self.steps_per_rad_2)
        return steps1, steps2
    
    def steps_to_angles(self, steps1, steps2):
        """
        Convertit le nombre de pas moteur en angles
        
        Args:
            steps1: Nombre de pas du moteur 1
            steps2: Nombre de pas du moteur 2
            
        Returns:
            tuple: (theta1, theta2) angles en radians
        """
        theta1 = steps1 / self.steps_per_rad_1
        theta2 = steps2 / self.steps_per_rad_2
        return theta1, theta2
    
    def get_workspace_limits(self):
        """
        Calcule les limites de l'espace de travail
        
        Returns:
            dict: Limites x et y de l'espace de travail
        """
        # Rayon maximum et minimum
        r_max = self.L1 + self.L2
        r_min = abs(self.L1 - self.L2)
        
        return {
            'x_min': -r_max,
            'x_max': r_max,
            'y_min': -r_max,
            'y_max': r_max,
            'r_max': r_max,
            'r_min': r_min
        }
    
    def get_scale_factor(self, width: float = None, height: float = None,
                         margin: float = None) -> float:
        """
        Calcule un facteur d'échelle qui garde tout l'espace de travail visible.
        
        Args:
            width: Largeur disponible en pixels
            height: Hauteur disponible en pixels
            margin: Marge en pixels
            
        Returns:
            float: Facteur d'échelle mm -> pixels
        """
        width = self.window_width if width is None else width
        height = self.window_height if height is None else height
        margin = self.display_margin if margin is None else margin
        
        r_max = self.L1 + self.L2
        usable_width = max(width - 2 * margin, 100)
        usable_height = max(height - 2 * margin, 100)
        
        scale_x = usable_width / (2 * r_max)
        scale_y = usable_height / (2 * r_max)
        
        return min(scale_x, scale_y, self.scale_factor)
    
    def __str__(self):
        """Représentation textuelle de la configuration"""
        return f"""Configuration du Bras Robotique 2DDL:
        Longueurs: L1={self.L1}mm, L2={self.L2}mm
        Limites theta1: [{np.degrees(self.theta1_min):.1f} deg, {np.degrees(self.theta1_max):.1f} deg]
        Limites theta2: [{np.degrees(self.theta2_min):.1f} deg, {np.degrees(self.theta2_max):.1f} deg]
        Pas/revolution: {self.steps_per_revolution} x {self.microsteps} microstepping
        Pas/radian: theta1={self.steps_per_rad_1:.1f}, theta2={self.steps_per_rad_2:.1f}
        """


# Instance globale de configuration
config = RobotConfig()


if __name__ == "__main__":
    # Test de la configuration
    print(config)
    print("\nEspace de travail:")
    workspace = config.get_workspace_limits()
    for key, value in workspace.items():
        print(f"  {key}: {value:.2f} mm")
    
    # Test de conversion angles -> pas
    theta1, theta2 = np.pi/4, np.pi/6
    steps1, steps2 = config.angles_to_steps(theta1, theta2)
    print(f"\nConversion angles -> pas:")
    print(f"  theta1={np.degrees(theta1):.1f} deg -> {steps1} pas")
    print(f"  theta2={np.degrees(theta2):.1f} deg -> {steps2} pas")
    
    # Test de conversion inverse
    theta1_back, theta2_back = config.steps_to_angles(steps1, steps2)
    print(f"\nConversion pas -> angles:")
    print(f"  {steps1} pas -> theta1={np.degrees(theta1_back):.1f} deg")
    print(f"  {steps2} pas -> theta2={np.degrees(theta2_back):.1f} deg")

# Made with Bob
