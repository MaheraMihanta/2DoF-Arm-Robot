"""
Tests unitaires pour le module objects.
Teste les cubes colorés, les zones de dépôt et le gestionnaire d'objets.
"""

import sys
import os
import pytest
import numpy as np

# Ajouter le chemin vers phase1_simulation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1_simulation'))

from objects import ColoredCube, DropZone, ObjectManager
from config import RobotConfig


class TestColoredCube:
    """Tests pour la classe ColoredCube."""
    
    def test_cube_initialization(self):
        """Test de l'initialisation d'un cube."""
        cube = ColoredCube(250.0, 150.0, 'red', 20.0)
        
        assert cube.x == 250.0
        assert cube.y == 150.0
        assert cube.color == 'red'
        assert cube.size == 20.0
        assert not cube.is_grasped
    
    def test_get_center(self):
        """Test de récupération du centre du cube."""
        cube = ColoredCube(100.0, 200.0, 'blue')
        center = cube.get_center()
        
        assert center == (100.0, 200.0)
    
    def test_set_position(self):
        """Test de modification de la position."""
        cube = ColoredCube(100.0, 100.0, 'green')
        cube.set_position(200.0, 150.0)
        
        assert cube.x == 200.0
        assert cube.y == 150.0
    
    def test_is_at_position_within_tolerance(self):
        """Test de détection de position dans la tolérance."""
        cube = ColoredCube(250.0, 150.0, 'red')
        
        assert cube.is_at_position(252.0, 151.0, tolerance=5.0)
        assert cube.is_at_position(250.0, 150.0, tolerance=5.0)
    
    def test_is_at_position_outside_tolerance(self):
        """Test de détection de position hors tolérance."""
        cube = ColoredCube(250.0, 150.0, 'red')
        
        assert not cube.is_at_position(260.0, 160.0, tolerance=5.0)
    
    def test_grasp_and_release(self):
        """Test de saisie et libération."""
        cube = ColoredCube(100.0, 100.0, 'blue')
        
        assert not cube.is_grasped
        
        cube.grasp()
        assert cube.is_grasped
        
        cube.release()
        assert not cube.is_grasped
    
    def test_cube_str_representation(self):
        """Test de la représentation textuelle."""
        cube = ColoredCube(250.0, 150.0, 'red')
        str_repr = str(cube)
        
        assert 'Red' in str_repr or 'red' in str_repr
        assert '250' in str_repr
        assert '150' in str_repr
        assert 'free' in str_repr


class TestDropZone:
    """Tests pour la classe DropZone."""
    
    def test_zone_initialization(self):
        """Test de l'initialisation d'une zone."""
        zone = DropZone(280.0, 200.0, 'red', 40.0)
        
        assert zone.x == 280.0
        assert zone.y == 200.0
        assert zone.color == 'red'
        assert zone.size == 40.0
        assert len(zone.objects_in_zone) == 0
    
    def test_get_center(self):
        """Test de récupération du centre de la zone."""
        zone = DropZone(280.0, 200.0, 'blue')
        center = zone.get_center()
        
        assert center == (280.0, 200.0)
    
    def test_contains_point_inside(self):
        """Test de détection d'un point à l'intérieur."""
        zone = DropZone(280.0, 200.0, 'red', 40.0)
        
        assert zone.contains_point(280.0, 200.0)  # Centre
        assert zone.contains_point(290.0, 210.0)  # Proche du bord
        assert zone.contains_point(270.0, 190.0)  # Autre coin
    
    def test_contains_point_outside(self):
        """Test de détection d'un point à l'extérieur."""
        zone = DropZone(280.0, 200.0, 'red', 40.0)
        
        assert not zone.contains_point(320.0, 240.0)  # Loin
        assert not zone.contains_point(250.0, 150.0)  # Très loin
    
    def test_add_correct_color_object(self):
        """Test d'ajout d'un objet de la bonne couleur."""
        zone = DropZone(280.0, 200.0, 'red', 40.0)
        cube = ColoredCube(280.0, 200.0, 'red')
        
        success = zone.add_object(cube)
        assert success
        assert cube in zone.objects_in_zone
        assert len(zone.objects_in_zone) == 1
    
    def test_add_wrong_color_object(self):
        """Test d'ajout d'un objet de mauvaise couleur."""
        zone = DropZone(280.0, 200.0, 'red', 40.0)
        cube = ColoredCube(280.0, 200.0, 'blue')
        
        success = zone.add_object(cube)
        assert not success
        assert cube not in zone.objects_in_zone
        assert len(zone.objects_in_zone) == 0
    
    def test_is_correct_placement(self):
        """Test de vérification du placement correct."""
        zone = DropZone(280.0, 200.0, 'red', 40.0)
        
        # Cube correct dans la zone
        cube_correct = ColoredCube(280.0, 200.0, 'red')
        assert zone.is_correct_placement(cube_correct)
        
        # Cube correct hors zone
        cube_outside = ColoredCube(350.0, 250.0, 'red')
        assert not zone.is_correct_placement(cube_outside)
        
        # Cube incorrect dans la zone
        cube_wrong_color = ColoredCube(280.0, 200.0, 'blue')
        assert not zone.is_correct_placement(cube_wrong_color)


class TestObjectManager:
    """Tests pour la classe ObjectManager."""
    
    @pytest.fixture
    def config(self):
        """Fixture pour la configuration."""
        return RobotConfig()
    
    @pytest.fixture
    def manager(self, config):
        """Fixture pour créer un gestionnaire."""
        return ObjectManager(config)
    
    def test_manager_initialization(self, manager):
        """Test de l'initialisation du gestionnaire."""
        assert len(manager.cubes) == 0
        assert len(manager.drop_zones) == 0
        assert manager.score == 0
        assert manager.total_objects == 0
    
    def test_create_cubes_with_positions(self, manager):
        """Test de création de cubes avec positions spécifiées."""
        colors = ['red', 'blue', 'green']
        positions = [(220.0, 130.0), (240.0, 140.0), (260.0, 150.0)]
        
        manager.create_cubes(colors, positions)
        
        assert len(manager.cubes) == 3
        assert manager.total_objects == 3
        assert manager.cubes[0].color == 'red'
        assert manager.cubes[0].x == 220.0
        assert manager.cubes[0].y == 130.0
    
    def test_create_cubes_random_positions(self, manager):
        """Test de création de cubes avec positions aléatoires."""
        colors = ['red', 'blue', 'green', 'yellow']
        
        manager.create_cubes(colors)
        
        assert len(manager.cubes) == 4
        assert manager.total_objects == 4
        
        # Vérifier que les positions sont dans l'espace de travail
        for cube in manager.cubes:
            assert 180 <= cube.x <= 280
            assert 80 <= cube.y <= 180
    
    def test_create_drop_zones(self, manager, config):
        """Test de création des zones de dépôt."""
        colors = ['red', 'blue', 'green']
        
        manager.create_drop_zones(colors)
        
        assert len(manager.drop_zones) == 3
        
        # Vérifier que les zones utilisent les positions de config
        red_zone = manager.get_drop_zone('red')
        assert red_zone is not None
        assert red_zone.x == config.drop_zones['red'][0]
        assert red_zone.y == config.drop_zones['red'][1]
    
    def test_get_cube_at_position(self, manager):
        """Test de recherche de cube à une position."""
        colors = ['red', 'blue']
        positions = [(220.0, 130.0), (260.0, 150.0)]
        manager.create_cubes(colors, positions)
        
        # Trouver le cube rouge
        cube = manager.get_cube_at_position(222.0, 131.0, tolerance=5.0)
        assert cube is not None
        assert cube.color == 'red'
        
        # Position sans cube
        cube = manager.get_cube_at_position(300.0, 200.0, tolerance=5.0)
        assert cube is None
    
    def test_get_cube_at_position_ignores_grasped(self, manager):
        """Test que les cubes saisis sont ignorés."""
        colors = ['red']
        positions = [(220.0, 130.0)]
        manager.create_cubes(colors, positions)
        
        # Saisir le cube
        manager.cubes[0].grasp()
        
        # Ne devrait pas le trouver
        cube = manager.get_cube_at_position(220.0, 130.0, tolerance=5.0)
        assert cube is None
    
    def test_get_nearest_cube(self, manager):
        """Test de recherche du cube le plus proche."""
        colors = ['red', 'blue', 'green']
        positions = [(220.0, 130.0), (240.0, 140.0), (260.0, 150.0)]
        manager.create_cubes(colors, positions)
        
        # Le plus proche de (230, 135) devrait être le bleu
        nearest = manager.get_nearest_cube(230.0, 135.0)
        assert nearest is not None
        assert nearest.color == 'blue'
    
    def test_get_nearest_cube_by_color(self, manager):
        """Test de recherche du cube le plus proche d'une couleur."""
        colors = ['red', 'blue', 'red']
        positions = [(220.0, 130.0), (240.0, 140.0), (260.0, 150.0)]
        manager.create_cubes(colors, positions)
        
        # Le cube rouge le plus proche de (250, 145)
        nearest = manager.get_nearest_cube(250.0, 145.0, color='red')
        assert nearest is not None
        assert nearest.color == 'red'
        assert nearest.x == 260.0  # Le deuxième cube rouge
    
    def test_get_drop_zone(self, manager):
        """Test de recherche de zone de dépôt."""
        colors = ['red', 'blue']
        manager.create_drop_zones(colors)
        
        red_zone = manager.get_drop_zone('red')
        assert red_zone is not None
        assert red_zone.color == 'red'
        
        yellow_zone = manager.get_drop_zone('yellow')
        assert yellow_zone is None  # Pas créée
    
    def test_update_score(self, manager, config):
        """Test de mise à jour du score."""
        colors = ['red', 'blue']
        positions = [(280.0, 200.0), (240.0, 140.0)]
        manager.create_cubes(colors, positions)
        manager.create_drop_zones(colors)
        
        # Score initial
        manager.update_score()
        assert manager.score == 1  # Seul le cube rouge est bien placé
        
        # Déplacer le cube bleu dans sa zone
        manager.cubes[1].set_position(280.0, 100.0)
        manager.update_score()
        assert manager.score == 2
    
    def test_is_sorting_complete(self, manager, config):
        """Test de vérification du tri complet."""
        colors = ['red', 'blue']
        positions = [(220.0, 130.0), (240.0, 140.0)]
        manager.create_cubes(colors, positions)
        manager.create_drop_zones(colors)
        
        # Tri incomplet
        assert not manager.is_sorting_complete()
        
        # Placer tous les cubes correctement
        manager.cubes[0].set_position(280.0, 200.0)  # Rouge
        manager.cubes[1].set_position(280.0, 100.0)  # Bleu
        
        assert manager.is_sorting_complete()
    
    def test_get_sorting_progress(self, manager, config):
        """Test de récupération de la progression."""
        colors = ['red', 'blue', 'green']
        positions = [(280.0, 200.0), (240.0, 140.0), (260.0, 150.0)]
        manager.create_cubes(colors, positions)
        manager.create_drop_zones(colors)
        
        sorted_count, total = manager.get_sorting_progress()
        assert sorted_count == 1  # Seul le rouge est bien placé
        assert total == 3
    
    def test_reset(self, manager):
        """Test de réinitialisation."""
        colors = ['red', 'blue']
        positions = [(220.0, 130.0), (240.0, 140.0)]
        manager.create_cubes(colors, positions)
        
        # Modifier les cubes
        manager.cubes[0].grasp()
        manager.cubes[1].set_position(300.0, 200.0)
        manager.score = 2
        
        # Réinitialiser
        manager.reset()
        
        assert len(manager.cubes) == 2
        assert manager.score == 0
        assert not manager.cubes[0].is_grasped
        # Les positions devraient être régénérées


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, '-v'])

# Made with Bob