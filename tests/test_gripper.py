"""
Tests unitaires pour le module gripper.
Teste les fonctionnalités de la pince : ouverture, fermeture, saisie d'objets.
"""

import sys
import os
import pytest
import numpy as np

# Ajouter le chemin vers phase1_simulation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1_simulation'))

from gripper import Gripper, GripperState
from config import RobotConfig


class TestGripper:
    """Tests pour la classe Gripper."""
    
    @pytest.fixture
    def config(self):
        """Fixture pour la configuration."""
        return RobotConfig()
    
    @pytest.fixture
    def gripper(self, config):
        """Fixture pour créer une pince."""
        return Gripper(config)
    
    def test_gripper_initialization(self, gripper, config):
        """Test de l'initialisation de la pince."""
        assert gripper.state == GripperState.OPEN
        assert gripper.current_width == config.gripper_width_open
        assert gripper.held_object is None
        assert gripper.is_open()
        assert not gripper.is_closed()
    
    def test_gripper_close(self, gripper, config):
        """Test de la fermeture de la pince."""
        gripper.close()
        assert gripper.state == GripperState.CLOSING
        assert gripper.target_width == config.gripper_width_closed
        
        # Simuler l'animation complète
        gripper.update(config.gripper_speed)
        assert gripper.is_closed()
        assert gripper.current_width == config.gripper_width_closed
    
    def test_gripper_open(self, gripper, config):
        """Test de l'ouverture de la pince."""
        # Fermer d'abord
        gripper.close()
        gripper.update(config.gripper_speed)
        assert gripper.is_closed()
        
        # Puis ouvrir
        gripper.open()
        assert gripper.state == GripperState.OPENING
        
        # Simuler l'animation complète
        gripper.update(config.gripper_speed)
        assert gripper.is_open()
        assert gripper.current_width == config.gripper_width_open
    
    def test_gripper_animation(self, gripper, config):
        """Test de l'animation de la pince."""
        gripper.close()
        assert gripper.is_animating()
        
        # Animation partielle
        gripper.update(config.gripper_speed / 2)
        assert gripper.is_animating()
        assert config.gripper_width_closed < gripper.current_width < config.gripper_width_open
        
        # Animation complète
        gripper.update(config.gripper_speed / 2)
        assert not gripper.is_animating()
        assert gripper.is_closed()
    
    def test_can_grasp_within_tolerance(self, gripper, config):
        """Test de détection de saisie dans la tolérance."""
        gripper_pos = (250.0, 150.0)
        object_pos = (252.0, 151.0)  # À ~2.2mm
        
        assert gripper.can_grasp(object_pos, gripper_pos)
    
    def test_can_grasp_outside_tolerance(self, gripper, config):
        """Test de détection de saisie hors tolérance."""
        gripper_pos = (250.0, 150.0)
        object_pos = (260.0, 160.0)  # À ~14mm
        
        assert not gripper.can_grasp(object_pos, gripper_pos)
    
    def test_can_grasp_when_closed(self, gripper, config):
        """Test qu'on ne peut pas détecter de saisie si la pince est fermée."""
        gripper.close()
        gripper.update(config.gripper_speed)
        
        gripper_pos = (250.0, 150.0)
        object_pos = (251.0, 150.0)
        
        assert not gripper.can_grasp(object_pos, gripper_pos)
    
    def test_grasp_object(self, gripper, config):
        """Test de saisie d'un objet."""
        # Créer un objet mock
        class MockObject:
            def __init__(self):
                self.grasped = False
                self.color = "red"
            
            def grasp(self):
                self.grasped = True
            
            def release(self):
                self.grasped = False
        
        obj = MockObject()
        
        # Fermer la pince
        gripper.close()
        gripper.update(config.gripper_speed)
        
        # Saisir l'objet
        success = gripper.grasp_object(obj)
        assert success
        assert gripper.is_holding_object()
        assert gripper.held_object == obj
        assert obj.grasped
    
    def test_cannot_grasp_when_open(self, gripper):
        """Test qu'on ne peut pas saisir si la pince est ouverte."""
        class MockObject:
            def grasp(self):
                pass
        
        obj = MockObject()
        success = gripper.grasp_object(obj)
        assert not success
        assert not gripper.is_holding_object()
    
    def test_release_object(self, gripper, config):
        """Test de libération d'un objet."""
        class MockObject:
            def __init__(self):
                self.grasped = False
                self.color = "blue"
            
            def grasp(self):
                self.grasped = True
            
            def release(self):
                self.grasped = False
        
        obj = MockObject()
        
        # Saisir l'objet
        gripper.close()
        gripper.update(config.gripper_speed)
        gripper.grasp_object(obj)
        assert gripper.is_holding_object()
        
        # Libérer l'objet
        released = gripper.release_object()
        assert released == obj
        assert not gripper.is_holding_object()
        assert not obj.grasped
    
    def test_open_releases_object(self, gripper, config):
        """Test que l'ouverture libère automatiquement l'objet."""
        class MockObject:
            def __init__(self):
                self.grasped = False
                self.color = "green"
            
            def grasp(self):
                self.grasped = True
            
            def release(self):
                self.grasped = False
        
        obj = MockObject()
        
        # Saisir l'objet
        gripper.close()
        gripper.update(config.gripper_speed)
        gripper.grasp_object(obj)
        assert gripper.is_holding_object()
        
        # Ouvrir la pince
        gripper.open()
        assert not gripper.is_holding_object()
        assert not obj.grasped
    
    def test_get_jaw_positions(self, gripper, config):
        """Test du calcul des positions des mâchoires."""
        gripper_pos = (250.0, 150.0)
        gripper_angle = 0.0  # Horizontal
        
        jaw1, jaw2 = gripper.get_jaw_positions(gripper_pos, gripper_angle)
        
        # Les mâchoires doivent être symétriques par rapport au centre
        assert abs(jaw1[0] - gripper_pos[0]) == pytest.approx(abs(jaw2[0] - gripper_pos[0]))
        assert abs(jaw1[1] - gripper_pos[1]) == pytest.approx(abs(jaw2[1] - gripper_pos[1]))
        
        # Distance entre les mâchoires = largeur de la pince
        distance = np.hypot(jaw1[0] - jaw2[0], jaw1[1] - jaw2[1])
        assert distance == pytest.approx(gripper.current_width)
    
    def test_get_state_info(self, gripper):
        """Test de récupération des informations d'état."""
        info = gripper.get_state_info()
        
        assert 'state' in info
        assert 'width' in info
        assert 'is_holding' in info
        assert 'held_object' in info
        assert 'animation_progress' in info
        
        assert info['state'] == 'open'
        assert info['is_holding'] is False
        assert info['held_object'] is None
    
    def test_gripper_str_representation(self, gripper):
        """Test de la représentation textuelle."""
        str_repr = str(gripper)
        assert 'Gripper' in str_repr
        assert 'open' in str_repr


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, '-v'])

# Made with Bob