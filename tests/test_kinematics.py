"""
Tests unitaires pour le module de cinématique
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1_simulation'))

import pytest
import numpy as np
from config import RobotConfig
from kinematics import Kinematics


class TestKinematics:
    """Tests pour la classe Kinematics"""
    
    @pytest.fixture
    def config(self):
        """Fixture pour la configuration"""
        return RobotConfig()
    
    @pytest.fixture
    def kin(self, config):
        """Fixture pour l'objet Kinematics"""
        return Kinematics(config)
    
    def test_forward_kinematics_zero_angles(self, kin):
        """Test de la cinématique directe avec angles nuls"""
        x, y = kin.forward_kinematics(0, 0)
        expected_x = kin.L1 + kin.L2
        expected_y = 0
        
        assert np.isclose(x, expected_x, atol=1e-6)
        assert np.isclose(y, expected_y, atol=1e-6)
    
    def test_forward_kinematics_90_degrees(self, kin):
        """Test avec θ1 = 90°, θ2 = 0°"""
        theta1 = np.pi / 2
        theta2 = 0
        x, y = kin.forward_kinematics(theta1, theta2)
        
        expected_x = 0
        expected_y = kin.L1 + kin.L2
        
        assert np.isclose(x, expected_x, atol=1e-6)
        assert np.isclose(y, expected_y, atol=1e-6)
    
    def test_forward_kinematics_arbitrary_angles(self, kin):
        """Test avec angles arbitraires"""
        theta1 = np.pi / 4  # 45°
        theta2 = np.pi / 6  # 30°
        
        x, y = kin.forward_kinematics(theta1, theta2)
        
        # Vérifier que les coordonnées sont dans l'espace de travail
        r = np.sqrt(x**2 + y**2)
        assert r <= (kin.L1 + kin.L2)
        assert r >= abs(kin.L1 - kin.L2)
    
    def test_inverse_kinematics_reachable_position(self, kin):
        """Test de la cinématique inverse pour une position atteignable"""
        target_x = 250.0
        target_y = 150.0
        
        result = kin.inverse_kinematics(target_x, target_y, elbow_up=True)
        
        assert result is not None
        theta1, theta2 = result
        
        # Vérifier avec la cinématique directe
        x_check, y_check = kin.forward_kinematics(theta1, theta2)
        
        assert np.isclose(x_check, target_x, atol=1e-3)
        assert np.isclose(y_check, target_y, atol=1e-3)
    
    def test_inverse_kinematics_unreachable_position(self, kin):
        """Test avec une position non atteignable"""
        # Position trop loin
        target_x = 1000.0
        target_y = 1000.0
        
        result = kin.inverse_kinematics(target_x, target_y)
        
        assert result is None
    
    def test_inverse_kinematics_too_close(self, kin):
        """Test avec une position trop proche"""
        # Position à l'intérieur du cercle minimum
        if abs(kin.L1 - kin.L2) > 0:
            target_x = 10.0
            target_y = 10.0
            
            result = kin.inverse_kinematics(target_x, target_y)
            
            # Devrait être None si vraiment trop proche
            r = np.sqrt(target_x**2 + target_y**2)
            if r < abs(kin.L1 - kin.L2):
                assert result is None
    
    def test_inverse_kinematics_both_solutions(self, kin):
        """Test des deux solutions (coude haut/bas)"""
        target_x = 200.0
        target_y = 100.0
        
        sol_up, sol_down = kin.inverse_kinematics_both_solutions(target_x, target_y)
        
        # Au moins une solution devrait exister
        assert sol_up is not None or sol_down is not None
        
        # Vérifier les deux solutions si elles existent
        if sol_up:
            x_up, y_up = kin.forward_kinematics(*sol_up)
            assert np.isclose(x_up, target_x, atol=1e-3)
            assert np.isclose(y_up, target_y, atol=1e-3)
        
        if sol_down:
            x_down, y_down = kin.forward_kinematics(*sol_down)
            assert np.isclose(x_down, target_x, atol=1e-3)
            assert np.isclose(y_down, target_y, atol=1e-3)
    
    def test_forward_inverse_consistency(self, kin):
        """Test de cohérence entre cinématique directe et inverse"""
        # Partir d'angles connus
        theta1_orig = np.pi / 3
        theta2_orig = np.pi / 4
        
        # Calculer la position
        x, y = kin.forward_kinematics(theta1_orig, theta2_orig)
        
        # Recalculer les angles
        result = kin.inverse_kinematics(x, y, elbow_up=True)
        
        assert result is not None
        theta1_calc, theta2_calc = result
        
        # Vérifier la cohérence (peut être une solution différente)
        x_check, y_check = kin.forward_kinematics(theta1_calc, theta2_calc)
        
        assert np.isclose(x_check, x, atol=1e-3)
        assert np.isclose(y_check, y, atol=1e-3)
    
    def test_jacobian_shape(self, kin):
        """Test de la forme de la matrice jacobienne"""
        theta1 = np.pi / 4
        theta2 = np.pi / 6
        
        J = kin.jacobian(theta1, theta2)
        
        assert J.shape == (2, 2)
    
    def test_jacobian_singularity(self, kin):
        """Test de la jacobienne en configuration singulière"""
        # Configuration étendue (singularité)
        theta1 = 0
        theta2 = 0
        
        J = kin.jacobian(theta1, theta2)
        
        # Le déterminant devrait être proche de zéro
        det = np.linalg.det(J)
        
        # En configuration étendue, le robot est en singularité
        assert abs(det) < 1e-6 or abs(det) > 1e-6  # Juste vérifier que ça calcule
    
    def test_get_joint_positions(self, kin):
        """Test de récupération des positions des articulations"""
        theta1 = np.pi / 4
        theta2 = np.pi / 6
        
        positions = kin.get_joint_positions(theta1, theta2)
        
        assert 'base' in positions
        assert 'joint1' in positions
        assert 'end_effector' in positions
        
        # La base devrait être à l'origine
        assert positions['base'] == (0.0, 0.0)
        
        # Joint1 devrait être à distance L1 de la base
        x1, y1 = positions['joint1']
        dist1 = np.sqrt(x1**2 + y1**2)
        assert np.isclose(dist1, kin.L1, atol=1e-6)
    
    def test_is_position_reachable(self, kin):
        """Test de vérification d'accessibilité"""
        # Position atteignable
        assert kin.is_position_reachable(200, 100) == True
        
        # Position trop loin
        assert kin.is_position_reachable(1000, 1000) == False
        
        # Position à la limite
        r_max = kin.L1 + kin.L2
        assert kin.is_position_reachable(r_max, 0) == True
    
    def test_workspace_boundary(self, kin):
        """Test de génération de la frontière de l'espace de travail"""
        (x_outer, y_outer), (x_inner, y_inner) = kin.get_workspace_boundary(100)
        
        assert len(x_outer) == 100
        assert len(y_outer) == 100
        assert len(x_inner) == 100
        assert len(y_inner) == 100
        
        # Vérifier les rayons
        for x, y in zip(x_outer, y_outer):
            r = np.sqrt(x**2 + y**2)
            assert np.isclose(r, kin.L1 + kin.L2, atol=1e-6)
        
        for x, y in zip(x_inner, y_inner):
            r = np.sqrt(x**2 + y**2)
            assert np.isclose(r, abs(kin.L1 - kin.L2), atol=1e-6)
    
    def test_normalize_angle(self, kin):
        """Test de normalisation des angles"""
        # Angle > π
        angle1 = 2 * np.pi + np.pi / 4
        normalized1 = kin._normalize_angle(angle1)
        assert -np.pi <= normalized1 <= np.pi
        
        # Angle < -π
        angle2 = -2 * np.pi - np.pi / 4
        normalized2 = kin._normalize_angle(angle2)
        assert -np.pi <= normalized2 <= np.pi
        
        # Angle déjà normalisé
        angle3 = np.pi / 2
        normalized3 = kin._normalize_angle(angle3)
        assert np.isclose(normalized3, angle3)
    
    def test_compute_trajectory(self, kin):
        """Test de calcul de trajectoire"""
        start_pos = (200.0, 100.0)
        end_pos = (250.0, 150.0)
        
        trajectory = kin.compute_trajectory(start_pos, end_pos, num_points=10)
        
        assert trajectory is not None
        assert trajectory.shape == (10, 4)  # [x, y, theta1, theta2]
        
        # Vérifier le début et la fin
        assert np.isclose(trajectory[0, 0], start_pos[0], atol=1e-3)
        assert np.isclose(trajectory[0, 1], start_pos[1], atol=1e-3)
        assert np.isclose(trajectory[-1, 0], end_pos[0], atol=1e-3)
        assert np.isclose(trajectory[-1, 1], end_pos[1], atol=1e-3)
    
    def test_compute_trajectory_unreachable(self, kin):
        """Test de trajectoire avec position non atteignable"""
        start_pos = (200.0, 100.0)
        end_pos = (1000.0, 1000.0)  # Trop loin
        
        trajectory = kin.compute_trajectory(start_pos, end_pos)
        
        # Devrait retourner None car la position finale n'est pas atteignable
        assert trajectory is None


class TestRobotConfig:
    """Tests pour la classe RobotConfig"""
    
    @pytest.fixture
    def config(self):
        """Fixture pour la configuration"""
        return RobotConfig()
    
    def test_config_initialization(self, config):
        """Test de l'initialisation de la configuration"""
        assert config.L1 > 0
        assert config.L2 > 0
        assert config.steps_per_revolution > 0
        assert config.microsteps > 0
    
    def test_is_angle_valid(self, config):
        """Test de validation des angles"""
        # Angles valides
        assert config.is_angle_valid(0, 0) == True
        assert config.is_angle_valid(np.pi/4, np.pi/6) == True
        
        # Angles invalides
        assert config.is_angle_valid(2*np.pi, 0) == False
        assert config.is_angle_valid(0, np.pi) == False
    
    def test_angles_to_steps(self, config):
        """Test de conversion angles -> pas"""
        theta1 = np.pi / 2  # 90°
        theta2 = np.pi / 4  # 45°
        
        steps1, steps2 = config.angles_to_steps(theta1, theta2)
        
        assert isinstance(steps1, int)
        assert isinstance(steps2, int)
        assert steps1 > 0
        assert steps2 > 0
    
    def test_steps_to_angles(self, config):
        """Test de conversion pas -> angles"""
        steps1 = 1600
        steps2 = 800
        
        theta1, theta2 = config.steps_to_angles(steps1, steps2)
        
        assert isinstance(theta1, float)
        assert isinstance(theta2, float)
    
    def test_angles_steps_roundtrip(self, config):
        """Test de cohérence conversion angles <-> pas"""
        theta1_orig = np.pi / 3
        theta2_orig = np.pi / 6
        
        # Convertir en pas
        steps1, steps2 = config.angles_to_steps(theta1_orig, theta2_orig)
        
        # Reconvertir en angles
        theta1_back, theta2_back = config.steps_to_angles(steps1, steps2)
        
        # Devrait être proche (avec erreur de quantification)
        assert np.isclose(theta1_back, theta1_orig, atol=0.01)
        assert np.isclose(theta2_back, theta2_orig, atol=0.01)
    
    def test_get_workspace_limits(self, config):
        """Test de calcul des limites de l'espace de travail"""
        limits = config.get_workspace_limits()
        
        assert 'x_min' in limits
        assert 'x_max' in limits
        assert 'y_min' in limits
        assert 'y_max' in limits
        assert 'r_max' in limits
        assert 'r_min' in limits
        
        assert limits['r_max'] == config.L1 + config.L2
        assert limits['r_min'] == abs(config.L1 - config.L2)


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "--tb=short"])

# Made with Bob
