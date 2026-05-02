"""
Module de gestion de la pince (gripper) du bras robotique.
Implémente une pince simple avec deux états : ouvert/fermé.
"""

from enum import Enum
from typing import Optional, Tuple
import numpy as np


class GripperState(Enum):
    """États possibles de la pince."""
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"


class Gripper:
    """
    Pince simple pour le bras robotique 2DDL.
    
    La pince peut s'ouvrir et se fermer pour saisir des objets.
    Elle est attachée à l'effecteur final du bras.
    """
    
    def __init__(self, config):
        """
        Initialise la pince.
        
        Args:
            config: Configuration du robot (RobotConfig)
        """
        self.config = config
        self.state = GripperState.OPEN
        self.current_width = config.gripper_width_open
        self.held_object = None
        
        # Animation de l'ouverture/fermeture
        self.animation_progress = 0.0
        self.animation_duration = config.gripper_speed
        self.target_width = config.gripper_width_open
        
    def open(self):
        """Ouvre la pince."""
        if self.state != GripperState.OPEN:
            self.state = GripperState.OPENING
            self.target_width = self.config.gripper_width_open
            self.animation_progress = 0.0
            # Libérer l'objet si on en tenait un
            if self.held_object is not None:
                self.held_object.release()
                self.held_object = None
    
    def close(self):
        """Ferme la pince."""
        if self.state != GripperState.CLOSED:
            self.state = GripperState.CLOSING
            self.target_width = self.config.gripper_width_closed
            self.animation_progress = 0.0
    
    def update(self, dt: float):
        """
        Met à jour l'état de la pince (animation).
        
        Args:
            dt: Pas de temps en secondes
        """
        if self.state in (GripperState.OPENING, GripperState.CLOSING):
            self.animation_progress += dt / self.animation_duration
            
            if self.animation_progress >= 1.0:
                # Animation terminée
                self.animation_progress = 1.0
                self.current_width = self.target_width
                
                if self.state == GripperState.OPENING:
                    self.state = GripperState.OPEN
                else:
                    self.state = GripperState.CLOSED
            else:
                # Interpolation linéaire
                start_width = (self.config.gripper_width_closed 
                             if self.state == GripperState.OPENING 
                             else self.config.gripper_width_open)
                self.current_width = start_width + (
                    self.target_width - start_width
                ) * self.animation_progress
    
    def is_open(self) -> bool:
        """Vérifie si la pince est ouverte."""
        return self.state == GripperState.OPEN
    
    def is_closed(self) -> bool:
        """Vérifie si la pince est fermée."""
        return self.state == GripperState.CLOSED
    
    def is_animating(self) -> bool:
        """Vérifie si la pince est en cours d'animation."""
        return self.state in (GripperState.OPENING, GripperState.CLOSING)
    
    def is_holding_object(self) -> bool:
        """Vérifie si la pince tient un objet."""
        return self.held_object is not None
    
    def can_grasp(self, object_position: Tuple[float, float], 
                  gripper_position: Tuple[float, float]) -> bool:
        """
        Vérifie si un objet peut être saisi.
        
        Args:
            object_position: Position (x, y) de l'objet en mm
            gripper_position: Position (x, y) de la pince en mm
            
        Returns:
            bool: True si l'objet peut être saisi
        """
        if not self.is_open():
            return False
        
        # Calculer la distance entre la pince et l'objet
        distance = np.hypot(
            object_position[0] - gripper_position[0],
            object_position[1] - gripper_position[1]
        )
        
        # L'objet doit être à portée de la pince
        return distance <= self.config.grasp_tolerance
    
    def grasp_object(self, obj):
        """
        Saisit un objet.
        
        Args:
            obj: Objet à saisir (ColoredCube)
            
        Returns:
            bool: True si la saisie a réussi
        """
        if self.is_closed() and not self.is_holding_object():
            self.held_object = obj
            obj.grasp()
            return True
        return False
    
    def release_object(self):
        """
        Libère l'objet tenu.
        
        Returns:
            object: L'objet libéré, ou None
        """
        if self.held_object is not None:
            obj = self.held_object
            obj.release()
            self.held_object = None
            return obj
        return None
    
    def get_jaw_positions(self, gripper_position: Tuple[float, float], 
                         gripper_angle: float) -> Tuple[Tuple[float, float], 
                                                        Tuple[float, float]]:
        """
        Calcule les positions des mâchoires de la pince.
        
        Args:
            gripper_position: Position (x, y) de la pince en mm
            gripper_angle: Angle de la pince en radians
            
        Returns:
            tuple: ((x1, y1), (x2, y2)) positions des deux mâchoires
        """
        half_width = self.current_width / 2.0
        
        # Vecteur perpendiculaire à l'angle de la pince
        perp_x = -np.sin(gripper_angle)
        perp_y = np.cos(gripper_angle)
        
        # Positions des mâchoires
        jaw1 = (
            gripper_position[0] + perp_x * half_width,
            gripper_position[1] + perp_y * half_width
        )
        jaw2 = (
            gripper_position[0] - perp_x * half_width,
            gripper_position[1] - perp_y * half_width
        )
        
        return jaw1, jaw2
    
    def get_state_info(self) -> dict:
        """
        Retourne les informations d'état de la pince.
        
        Returns:
            dict: Informations sur l'état de la pince
        """
        return {
            'state': self.state.value,
            'width': self.current_width,
            'is_holding': self.is_holding_object(),
            'held_object': self.held_object.color if self.held_object else None,
            'animation_progress': self.animation_progress
        }
    
    def __str__(self):
        """Représentation textuelle de la pince."""
        status = f"Gripper [{self.state.value}]"
        if self.is_holding_object():
            status += f" holding {self.held_object.color} cube"
        return status


if __name__ == "__main__":
    # Test simple du module gripper
    print("=== Test du Module Gripper ===\n")
    
    # Créer une configuration minimale pour les tests
    class MockConfig:
        gripper_width_open = 80.0
        gripper_width_closed = 30.0
        gripper_speed = 0.3
        grasp_tolerance = 5.0
    
    config = MockConfig()
    gripper = Gripper(config)
    
    print(f"État initial: {gripper}")
    print(f"Largeur: {gripper.current_width:.1f}mm")
    print(f"Est ouverte: {gripper.is_open()}")
    print()
    
    # Test fermeture
    print("Fermeture de la pince...")
    gripper.close()
    print(f"État: {gripper.state.value}")
    
    # Simuler l'animation
    for i in range(4):
        gripper.update(0.1)
        print(f"  t={i*0.1:.1f}s: largeur={gripper.current_width:.1f}mm")
    
    print(f"État final: {gripper}")
    print(f"Est fermée: {gripper.is_closed()}")
    print()
    
    # Test ouverture
    print("Ouverture de la pince...")
    gripper.open()
    for i in range(4):
        gripper.update(0.1)
    print(f"État final: {gripper}")
    print()
    
    # Test de saisie
    print("Test de détection de saisie:")
    gripper_pos = (250.0, 150.0)
    object_pos_near = (252.0, 151.0)
    object_pos_far = (270.0, 160.0)
    
    print(f"Objet proche ({object_pos_near}): {gripper.can_grasp(object_pos_near, gripper_pos)}")
    print(f"Objet loin ({object_pos_far}): {gripper.can_grasp(object_pos_far, gripper_pos)}")
    
    print("\n✅ Tests du module gripper terminés")

# Made with Bob