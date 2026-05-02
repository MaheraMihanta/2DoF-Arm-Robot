"""
Module de contrôle des moteurs pas à pas via GRBL
Convertit les angles articulaires en commandes G-code
"""

import numpy as np
from typing import Tuple, Optional

try:
    from ..phase1_simulation.config import RobotConfig
    from .grbl_interface import GRBLInterface
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "phase1_simulation"))
    from config import RobotConfig
    from grbl_interface import GRBLInterface


class MotorController:
    """Contrôleur pour les moteurs pas à pas via GRBL"""
    
    def __init__(self, config: RobotConfig, grbl: GRBLInterface):
        """
        Initialise le contrôleur de moteurs
        
        Args:
            config: Configuration du robot
            grbl: Interface GRBL connectée
        """
        self.config = config
        self.grbl = grbl
        
        # Position actuelle des moteurs (en pas)
        self.current_steps_1 = 0
        self.current_steps_2 = 0
        
        # Position actuelle des angles (en radians)
        self.current_theta1 = 0.0
        self.current_theta2 = 0.0
        
        # Vitesse par défaut (mm/min pour GRBL, converti en rad/s pour notre usage)
        self.default_feed_rate = 1000  # mm/min
        
    def angles_to_gcode_position(self, theta1: float, theta2: float) -> Tuple[float, float]:
        """
        Convertit les angles articulaires en positions G-code (X, Y)
        
        Pour GRBL, on mappe:
        - Axe X -> Moteur 1 (θ1)
        - Axe Y -> Moteur 2 (θ2)
        
        La position en mm est calculée à partir des pas moteur
        
        Args:
            theta1: Angle articulation 1 (radians)
            theta2: Angle articulation 2 (radians)
            
        Returns:
            tuple: (x_position, y_position) en mm pour GRBL
        """
        # Convertir les angles en pas
        steps1, steps2 = self.config.angles_to_steps(theta1, theta2)
        
        # Convertir les pas en position linéaire (mm)
        # On utilise une conversion arbitraire: 1 pas = 0.01 mm
        # Cela peut être ajusté selon votre configuration mécanique
        steps_to_mm = 0.01
        
        x_pos = steps1 * steps_to_mm
        y_pos = steps2 * steps_to_mm
        
        return x_pos, y_pos
    
    def gcode_position_to_angles(self, x_pos: float, y_pos: float) -> Tuple[float, float]:
        """
        Convertit une position G-code en angles articulaires
        
        Args:
            x_pos: Position X en mm
            y_pos: Position Y en mm
            
        Returns:
            tuple: (theta1, theta2) en radians
        """
        # Conversion inverse
        steps_to_mm = 0.01
        
        steps1 = int(x_pos / steps_to_mm)
        steps2 = int(y_pos / steps_to_mm)
        
        theta1, theta2 = self.config.steps_to_angles(steps1, steps2)
        
        return theta1, theta2
    
    def move_to_angles(self, theta1: float, theta2: float, 
                       feed_rate: Optional[float] = None) -> bool:
        """
        Déplace les moteurs vers les angles spécifiés
        
        Args:
            theta1: Angle cible articulation 1 (radians)
            theta2: Angle cible articulation 2 (radians)
            feed_rate: Vitesse d'avance (mm/min), None pour valeur par défaut
            
        Returns:
            bool: True si le mouvement est réussi
        """
        # Vérifier les limites
        if not self.config.is_angle_valid(theta1, theta2):
            print(
                f"Erreur: angles hors limites - "
                f"theta1={np.degrees(theta1):.1f} deg, "
                f"theta2={np.degrees(theta2):.1f} deg"
            )
            return False
        
        # Convertir en position G-code
        x_pos, y_pos = self.angles_to_gcode_position(theta1, theta2)
        
        # Utiliser la vitesse par défaut si non spécifiée
        if feed_rate is None:
            feed_rate = self.default_feed_rate
        
        # Envoyer la commande de mouvement
        print(
            f"Déplacement vers theta1={np.degrees(theta1):.1f} deg, "
            f"theta2={np.degrees(theta2):.1f} deg"
        )
        print(f"  Position G-code: X={x_pos:.3f}, Y={y_pos:.3f}")
        
        success = self.grbl.move_absolute(x=x_pos, y=y_pos, feed_rate=feed_rate)
        
        if success:
            # Mettre à jour la position actuelle
            self.current_theta1 = theta1
            self.current_theta2 = theta2
            self.current_steps_1, self.current_steps_2 = self.config.angles_to_steps(theta1, theta2)
            print("Mouvement envoyé avec succès")
        else:
            print("Échec de l'envoi du mouvement")
        
        return success
    
    def move_incremental(self, delta_theta1: float, delta_theta2: float,
                        feed_rate: Optional[float] = None) -> bool:
        """
        Déplace les moteurs de manière incrémentale
        
        Args:
            delta_theta1: Variation d'angle articulation 1 (radians)
            delta_theta2: Variation d'angle articulation 2 (radians)
            feed_rate: Vitesse d'avance (mm/min)
            
        Returns:
            bool: True si le mouvement est réussi
        """
        new_theta1 = self.current_theta1 + delta_theta1
        new_theta2 = self.current_theta2 + delta_theta2
        
        return self.move_to_angles(new_theta1, new_theta2, feed_rate)
    
    def home_motors(self) -> bool:
        """
        Effectue le homing des moteurs
        
        Returns:
            bool: True si le homing est réussi
        """
        print("Homing des moteurs...")
        success = self.grbl.home()
        
        if success:
            # Réinitialiser les positions
            self.current_theta1 = 0.0
            self.current_theta2 = 0.0
            self.current_steps_1 = 0
            self.current_steps_2 = 0
            print("Homing terminé - Position réinitialisée")
        
        return success
    
    def set_current_position_as_zero(self) -> bool:
        """
        Définit la position actuelle comme origine
        
        Returns:
            bool: True si réussi
        """
        success = self.grbl.set_work_zero()
        
        if success:
            self.current_theta1 = 0.0
            self.current_theta2 = 0.0
            self.current_steps_1 = 0
            self.current_steps_2 = 0
            print("Position actuelle définie comme origine")
        
        return success
    
    def get_current_angles(self) -> Tuple[float, float]:
        """
        Retourne les angles actuels
        
        Returns:
            tuple: (theta1, theta2) en radians
        """
        return self.current_theta1, self.current_theta2
    
    def get_current_steps(self) -> Tuple[int, int]:
        """
        Retourne le nombre de pas actuels
        
        Returns:
            tuple: (steps1, steps2)
        """
        return self.current_steps_1, self.current_steps_2
    
    def execute_trajectory(self, trajectory: np.ndarray, 
                          feed_rate: Optional[float] = None) -> bool:
        """
        Exécute une trajectoire complète
        
        Args:
            trajectory: Tableau numpy de shape (n, 4) contenant [x, y, theta1, theta2]
            feed_rate: Vitesse d'avance (mm/min)
            
        Returns:
            bool: True si toute la trajectoire est exécutée avec succès
        """
        print(f"Exécution d'une trajectoire de {len(trajectory)} points...")
        
        for i, point in enumerate(trajectory):
            x, y, theta1, theta2 = point
            
            print(
                f"Point {i+1}/{len(trajectory)}: "
                f"theta1={np.degrees(theta1):.1f} deg, "
                f"theta2={np.degrees(theta2):.1f} deg"
            )
            
            success = self.move_to_angles(theta1, theta2, feed_rate)
            
            if not success:
                print(f"Échec à l'exécution du point {i+1}")
                return False
            
            # Attendre que le mouvement soit terminé
            # (Dans une vraie application, il faudrait vérifier le statut GRBL)
            import time
            time.sleep(0.1)
        
        print("Trajectoire complète exécutée")
        return True
    
    def emergency_stop(self):
        """Arrêt d'urgence - envoie un soft reset à GRBL"""
        print("ARRÊT D'URGENCE!")
        self.grbl.soft_reset()
    
    def configure_grbl_for_robot(self) -> bool:
        """
        Configure les paramètres GRBL pour le robot
        
        Returns:
            bool: True si la configuration est réussie
        """
        print("Configuration de GRBL pour le robot...")
        
        # Paramètres recommandés pour moteurs pas à pas
        settings = {
            # $0 - Step pulse time (microseconds)
            0: 10,
            
            # $1 - Step idle delay (milliseconds)
            1: 25,
            
            # $2 - Step pulse invert (mask)
            2: 0,
            
            # $3 - Step direction invert (mask)
            3: 0,
            
            # $4 - Invert step enable pin
            4: 0,
            
            # $5 - Invert limit pins
            5: 0,
            
            # $10 - Status report options (mask)
            10: 1,
            
            # $11 - Junction deviation (mm)
            11: 0.010,
            
            # $12 - Arc tolerance (mm)
            12: 0.002,
            
            # $20 - Soft limits enable
            20: 0,
            
            # $21 - Hard limits enable
            21: 0,
            
            # $22 - Homing cycle enable
            22: 0,
            
            # $100 - X axis steps/mm
            100: 100.0,  # À ajuster selon votre configuration
            
            # $101 - Y axis steps/mm
            101: 100.0,  # À ajuster selon votre configuration
            
            # $110 - X axis max rate (mm/min)
            110: 2000.0,
            
            # $111 - Y axis max rate (mm/min)
            111: 2000.0,
            
            # $120 - X axis acceleration (mm/sec^2)
            120: 500.0,
            
            # $121 - Y axis acceleration (mm/sec^2)
            121: 500.0,
        }
        
        success = True
        for param, value in settings.items():
            if not self.grbl.set_setting(param, value):
                print(f"Échec de configuration du paramètre ${param}")
                success = False
        
        if success:
            print("Configuration GRBL terminée")
        
        return success


def main():
    """Fonction de test du contrôleur de moteurs"""
    print("=== Test Contrôleur de Moteurs ===\n")
    
    # Importer la configuration
    try:
        from ..phase1_simulation.config import config
    except ImportError:
        from config import config
    
    # Demander le port série
    port = input("Port série (ex: COM3): ").strip()
    if not port:
        port = "COM3"
    
    # Créer l'interface GRBL
    grbl = GRBLInterface(port=port)
    
    if not grbl.connect():
        print("Impossible de se connecter à GRBL")
        return
    
    try:
        # Créer le contrôleur
        controller = MotorController(config, grbl)
        
        # Menu de test
        while True:
            print("\n--- Menu Test Moteurs ---")
            print("1. Homing")
            print("2. Définir origine")
            print("3. Déplacer vers angles")
            print("4. Déplacement incrémental")
            print("5. Position actuelle")
            print("6. Configurer GRBL")
            print("7. Test trajectoire")
            print("0. Quitter")
            
            choice = input("\nChoix: ").strip()
            
            if choice == '1':
                controller.home_motors()
            
            elif choice == '2':
                controller.set_current_position_as_zero()
            
            elif choice == '3':
                theta1_deg = float(input("theta1 (degres): "))
                theta2_deg = float(input("theta2 (degres): "))
                theta1 = np.radians(theta1_deg)
                theta2 = np.radians(theta2_deg)
                controller.move_to_angles(theta1, theta2)
            
            elif choice == '4':
                delta1_deg = float(input("delta theta1 (degres): "))
                delta2_deg = float(input("delta theta2 (degres): "))
                delta1 = np.radians(delta1_deg)
                delta2 = np.radians(delta2_deg)
                controller.move_incremental(delta1, delta2)
            
            elif choice == '5':
                theta1, theta2 = controller.get_current_angles()
                steps1, steps2 = controller.get_current_steps()
                print(
                    f"Angles: theta1={np.degrees(theta1):.1f} deg, "
                    f"theta2={np.degrees(theta2):.1f} deg"
                )
                print(f"Pas: {steps1}, {steps2}")
            
            elif choice == '6':
                controller.configure_grbl_for_robot()
            
            elif choice == '7':
                # Test simple: mouvement en carré
                print("Test trajectoire carrée...")
                angles_sequence = [
                    (0, 0),
                    (np.pi/6, 0),
                    (np.pi/6, np.pi/6),
                    (0, np.pi/6),
                    (0, 0)
                ]
                
                for theta1, theta2 in angles_sequence:
                    controller.move_to_angles(theta1, theta2)
                    import time
                    time.sleep(1)
            
            elif choice == '0':
                break
    
    finally:
        grbl.disconnect()


if __name__ == "__main__":
    main()

# Made with Bob
