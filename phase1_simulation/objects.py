"""
Module de gestion des objets manipulables par le bras robotique.
Implémente des cubes colorés et un gestionnaire d'objets pour les scénarios pick & place.
"""

import random
from typing import List, Optional, Tuple, Dict
import numpy as np

try:
    import pygame
except ImportError:
    pygame = None


class ColoredCube:
    """
    Cube coloré manipulable par le bras robotique.
    
    Représente un objet simple avec position, couleur et état (libre/saisi).
    """
    
    def __init__(self, x: float, y: float, color: str, size: float = 20.0):
        """
        Initialise un cube coloré.
        
        Args:
            x: Position X en mm
            y: Position Y en mm
            color: Couleur du cube ('red', 'blue', 'green', 'yellow')
            size: Taille du cube en mm
        """
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.is_grasped = False
        self.id = id(self)  # Identifiant unique
        
    def get_center(self) -> Tuple[float, float]:
        """Retourne la position du centre du cube."""
        return (self.x, self.y)
    
    def set_position(self, x: float, y: float):
        """Définit la position du cube."""
        self.x = x
        self.y = y
    
    def is_at_position(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        """
        Vérifie si le cube est à une position donnée.
        
        Args:
            x: Position X cible en mm
            y: Position Y cible en mm
            tolerance: Tolérance en mm
            
        Returns:
            bool: True si le cube est à la position
        """
        distance = np.hypot(self.x - x, self.y - y)
        return distance <= tolerance
    
    def grasp(self):
        """Marque le cube comme saisi."""
        self.is_grasped = True
    
    def release(self):
        """Marque le cube comme libéré."""
        self.is_grasped = False
    
    def draw(self, screen, origin_x: int, origin_y: int, scale: float, 
             color_map: Dict[str, Tuple[int, int, int]]):
        """
        Dessine le cube sur l'écran Pygame.
        
        Args:
            screen: Surface Pygame
            origin_x: Origine X de l'écran en pixels
            origin_y: Origine Y de l'écran en pixels
            scale: Facteur d'échelle mm -> pixels
            color_map: Dictionnaire des couleurs RGB
        """
        if pygame is None:
            return
        
        # Convertir position monde -> écran
        screen_x = int(origin_x + self.x * scale)
        screen_y = int(origin_y - self.y * scale)
        screen_size = int(self.size * scale)
        
        # Couleur du cube
        color = color_map.get(self.color, (128, 128, 128))
        
        # Dessiner le cube
        rect = pygame.Rect(
            screen_x - screen_size // 2,
            screen_y - screen_size // 2,
            screen_size,
            screen_size
        )
        pygame.draw.rect(screen, color, rect)
        
        # Bordure plus épaisse si saisi
        border_width = 3 if self.is_grasped else 1
        pygame.draw.rect(screen, (0, 0, 0), rect, border_width)
        
        # Indicateur visuel si saisi
        if self.is_grasped:
            # Petite croix au centre
            cross_size = screen_size // 4
            pygame.draw.line(
                screen, (255, 255, 255),
                (screen_x - cross_size, screen_y),
                (screen_x + cross_size, screen_y),
                2
            )
            pygame.draw.line(
                screen, (255, 255, 255),
                (screen_x, screen_y - cross_size),
                (screen_x, screen_y + cross_size),
                2
            )
    
    def __str__(self):
        """Représentation textuelle du cube."""
        status = "grasped" if self.is_grasped else "free"
        return f"{self.color.capitalize()} cube at ({self.x:.1f}, {self.y:.1f}) [{status}]"


class DropZone:
    """
    Zone de dépôt pour les objets triés.
    
    Représente une zone rectangulaire où les objets d'une certaine couleur
    doivent être déposés.
    """
    
    def __init__(self, x: float, y: float, color: str, size: float = 40.0):
        """
        Initialise une zone de dépôt.
        
        Args:
            x: Position X du centre en mm
            y: Position Y du centre en mm
            color: Couleur associée à la zone
            size: Taille de la zone en mm
        """
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.objects_in_zone: List[ColoredCube] = []
    
    def get_center(self) -> Tuple[float, float]:
        """Retourne la position du centre de la zone."""
        return (self.x, self.y)
    
    def contains_point(self, x: float, y: float) -> bool:
        """
        Vérifie si un point est dans la zone.
        
        Args:
            x: Position X en mm
            y: Position Y en mm
            
        Returns:
            bool: True si le point est dans la zone
        """
        half_size = self.size / 2.0
        return (abs(x - self.x) <= half_size and 
                abs(y - self.y) <= half_size)
    
    def add_object(self, obj: ColoredCube) -> bool:
        """
        Ajoute un objet à la zone.
        
        Args:
            obj: Objet à ajouter
            
        Returns:
            bool: True si l'objet est de la bonne couleur
        """
        if obj.color == self.color:
            if obj not in self.objects_in_zone:
                self.objects_in_zone.append(obj)
            return True
        return False
    
    def is_correct_placement(self, obj: ColoredCube) -> bool:
        """Vérifie si un objet est correctement placé dans cette zone."""
        return (obj.color == self.color and 
                self.contains_point(obj.x, obj.y))
    
    def draw(self, screen, origin_x: int, origin_y: int, scale: float,
             color_map: Dict[str, Tuple[int, int, int]]):
        """
        Dessine la zone de dépôt sur l'écran Pygame.
        
        Args:
            screen: Surface Pygame
            origin_x: Origine X de l'écran en pixels
            origin_y: Origine Y de l'écran en pixels
            scale: Facteur d'échelle mm -> pixels
            color_map: Dictionnaire des couleurs RGB
        """
        if pygame is None:
            return
        
        # Convertir position monde -> écran
        screen_x = int(origin_x + self.x * scale)
        screen_y = int(origin_y - self.y * scale)
        screen_size = int(self.size * scale)
        
        # Couleur de la zone (plus transparente)
        color = color_map.get(self.color, (128, 128, 128))
        light_color = tuple(min(c + 100, 255) for c in color)
        
        # Dessiner le rectangle de la zone
        rect = pygame.Rect(
            screen_x - screen_size // 2,
            screen_y - screen_size // 2,
            screen_size,
            screen_size
        )
        pygame.draw.rect(screen, light_color, rect)
        pygame.draw.rect(screen, color, rect, 2)
        
        # Afficher le nombre d'objets dans la zone
        if pygame.font:
            font = pygame.font.Font(None, 20)
            text = font.render(str(len(self.objects_in_zone)), True, (0, 0, 0))
            text_rect = text.get_rect(center=(screen_x, screen_y))
            screen.blit(text, text_rect)


class ObjectManager:
    """
    Gestionnaire des objets et zones de dépôt pour les scénarios pick & place.
    
    Gère la création, le placement et le suivi des objets et zones.
    """
    
    def __init__(self, config):
        """
        Initialise le gestionnaire d'objets.
        
        Args:
            config: Configuration du robot (RobotConfig)
        """
        self.config = config
        self.cubes: List[ColoredCube] = []
        self.drop_zones: List[DropZone] = []
        self.score = 0
        self.total_objects = 0
        
    def create_cubes(self, colors: List[str], positions: Optional[List[Tuple[float, float]]] = None):
        """
        Crée des cubes colorés.
        
        Args:
            colors: Liste des couleurs des cubes
            positions: Positions optionnelles (générées aléatoirement si None)
        """
        self.cubes.clear()
        self.total_objects = len(colors)
        
        if positions is None:
            # Générer des positions aléatoires dans l'espace de travail
            positions = self._generate_random_positions(len(colors))
        
        for i, color in enumerate(colors):
            x, y = positions[i]
            cube = ColoredCube(x, y, color, self.config.cube_size)
            self.cubes.append(cube)
    
    def create_drop_zones(self, colors: List[str], positions: Optional[Dict[str, Tuple[float, float]]] = None):
        """
        Crée des zones de dépôt.
        
        Args:
            colors: Liste des couleurs des zones
            positions: Positions optionnelles (utilise config.drop_zones si None)
        """
        self.drop_zones.clear()
        
        if positions is None:
            positions = self.config.drop_zones
        
        for color in colors:
            if color in positions:
                x, y = positions[color]
                zone = DropZone(x, y, color, self.config.cube_size * 2)
                self.drop_zones.append(zone)
    
    def _generate_random_positions(self, count: int) -> List[Tuple[float, float]]:
        """
        Génère des positions aléatoires dans l'espace de travail atteignable.
        
        Args:
            count: Nombre de positions à générer
            
        Returns:
            list: Liste de positions (x, y)
        """
        positions = []
        
        # Zone de génération sûre (zone centrale atteignable)
        # Basée sur L1=200mm, L2=150mm
        # Rayon max = 350mm, rayon min = 50mm
        # On génère dans une zone sûre : rayon 100-300mm
        
        for _ in range(count):
            attempts = 0
            max_attempts = 50
            
            while attempts < max_attempts:
                # Générer position en coordonnées polaires pour garantir l'atteignabilité
                radius = random.uniform(100, 280)  # Entre 100 et 280mm du centre
                angle = random.uniform(-np.pi/2, np.pi/2)  # Devant le robot
                
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                
                # Vérifier que la position est atteignable (distance du centre)
                distance = np.hypot(x, y)
                r_max = self.config.L1 + self.config.L2
                r_min = abs(self.config.L1 - self.config.L2)
                
                if not (r_min + 20 < distance < r_max - 20):
                    attempts += 1
                    continue
                
                # Vérifier qu'elle n'est pas trop proche des autres objets
                min_distance = self.config.cube_size * 2.5
                too_close = False
                for px, py in positions:
                    if np.hypot(x - px, y - py) < min_distance:
                        too_close = True
                        break
                
                if too_close:
                    attempts += 1
                    continue
                
                # Vérifier qu'elle n'est pas dans une zone de dépôt
                in_drop_zone = False
                for zone_pos in self.config.drop_zones.values():
                    zx, zy = zone_pos
                    if np.hypot(x - zx, y - zy) < 50:  # 50mm de marge
                        in_drop_zone = True
                        break
                
                if in_drop_zone:
                    attempts += 1
                    continue
                
                # Position valide trouvée
                positions.append((x, y))
                break
            
            # Si on n'a pas trouvé de position après max_attempts, utiliser une position par défaut
            if len(positions) < len(positions) + 1:
                # Position de secours dans la zone centrale
                default_x = 150 + (len(positions) * 30)
                default_y = 100
                positions.append((default_x, default_y))
        
        return positions
    
    def get_cube_at_position(self, x: float, y: float, tolerance: float = None) -> Optional[ColoredCube]:
        """
        Trouve le cube à une position donnée.
        
        Args:
            x: Position X en mm
            y: Position Y en mm
            tolerance: Tolérance en mm (utilise grasp_tolerance si None)
            
        Returns:
            ColoredCube ou None
        """
        if tolerance is None:
            tolerance = self.config.grasp_tolerance
        
        for cube in self.cubes:
            if not cube.is_grasped and cube.is_at_position(x, y, tolerance):
                return cube
        return None
    
    def get_nearest_cube(self, x: float, y: float, color: Optional[str] = None) -> Optional[ColoredCube]:
        """
        Trouve le cube le plus proche d'une position.
        
        Args:
            x: Position X en mm
            y: Position Y en mm
            color: Filtrer par couleur (optionnel)
            
        Returns:
            ColoredCube ou None
        """
        nearest = None
        min_distance = float('inf')
        
        for cube in self.cubes:
            if cube.is_grasped:
                continue
            if color is not None and cube.color != color:
                continue
            
            distance = np.hypot(cube.x - x, cube.y - y)
            if distance < min_distance:
                min_distance = distance
                nearest = cube
        
        return nearest
    
    def get_drop_zone(self, color: str) -> Optional[DropZone]:
        """
        Trouve la zone de dépôt pour une couleur.
        
        Args:
            color: Couleur recherchée
            
        Returns:
            DropZone ou None
        """
        for zone in self.drop_zones:
            if zone.color == color:
                return zone
        return None
    
    def update_score(self):
        """Met à jour le score en fonction des objets correctement placés."""
        self.score = 0
        for zone in self.drop_zones:
            zone.objects_in_zone.clear()
            for cube in self.cubes:
                if zone.is_correct_placement(cube):
                    zone.add_object(cube)
                    self.score += 1
    
    def is_sorting_complete(self) -> bool:
        """Vérifie si tous les objets sont correctement triés."""
        self.update_score()
        return self.score == self.total_objects
    
    def get_sorting_progress(self) -> Tuple[int, int]:
        """
        Retourne la progression du tri.
        
        Returns:
            tuple: (objets_triés, total_objets)
        """
        self.update_score()
        return (self.score, self.total_objects)
    
    def draw(self, screen, origin_x: int, origin_y: int, scale: float):
        """
        Dessine tous les objets et zones sur l'écran.
        
        Args:
            screen: Surface Pygame
            origin_x: Origine X de l'écran en pixels
            origin_y: Origine Y de l'écran en pixels
            scale: Facteur d'échelle mm -> pixels
        """
        if pygame is None:
            return
        
        # Dessiner d'abord les zones de dépôt
        for zone in self.drop_zones:
            zone.draw(screen, origin_x, origin_y, scale, self.config.cube_colors)
        
        # Puis les cubes
        for cube in self.cubes:
            cube.draw(screen, origin_x, origin_y, scale, self.config.cube_colors)
    
    def reset(self):
        """Réinitialise tous les objets."""
        colors = [cube.color for cube in self.cubes]
        self.create_cubes(colors)
        self.score = 0


if __name__ == "__main__":
    # Test simple du module objects
    print("=== Test du Module Objects ===\n")
    
    # Créer une configuration minimale pour les tests
    class MockConfig:
        cube_size = 20.0
        grasp_tolerance = 5.0
        drop_zones = {
            'red': (280, 200),
            'blue': (280, 100),
            'green': (180, 200)
        }
        cube_colors = {
            'red': (255, 50, 50),
            'blue': (50, 100, 255),
            'green': (50, 200, 50)
        }
        
        def get_workspace_limits(self):
            return {'x_min': 50, 'x_max': 350, 'y_min': 50, 'y_max': 350}
    
    config = MockConfig()
    
    # Test ColoredCube
    print("Test ColoredCube:")
    cube = ColoredCube(250, 150, 'red', 20)
    print(f"  {cube}")
    print(f"  Centre: {cube.get_center()}")
    print(f"  À position (250, 150): {cube.is_at_position(250, 150, 5)}")
    print(f"  À position (260, 160): {cube.is_at_position(260, 160, 5)}")
    print()
    
    # Test ObjectManager
    print("Test ObjectManager:")
    manager = ObjectManager(config)
    
    colors = ['red', 'blue', 'green']
    positions = [(220, 130), (240, 140), (260, 150)]
    manager.create_cubes(colors, positions)
    manager.create_drop_zones(colors)
    
    print(f"  Cubes créés: {len(manager.cubes)}")
    print(f"  Zones créées: {len(manager.drop_zones)}")
    
    for cube in manager.cubes:
        print(f"    {cube}")
    print()
    
    # Test recherche
    print("Test recherche de cube:")
    nearest = manager.get_nearest_cube(230, 135)
    if nearest:
        print(f"  Cube le plus proche de (230, 135): {nearest}")
    
    nearest_red = manager.get_nearest_cube(230, 135, 'red')
    if nearest_red:
        print(f"  Cube rouge le plus proche: {nearest_red}")
    print()
    
    # Test zone de dépôt
    print("Test zone de dépôt:")
    red_zone = manager.get_drop_zone('red')
    if red_zone:
        print(f"  Zone rouge: centre={red_zone.get_center()}")
        print(f"  Contient (280, 200): {red_zone.contains_point(280, 200)}")
        print(f"  Contient (250, 150): {red_zone.contains_point(250, 150)}")
    print()
    
    # Test score
    print("Test score:")
    print(f"  Score initial: {manager.score}/{manager.total_objects}")
    
    # Déplacer un cube dans sa zone
    manager.cubes[0].set_position(280, 200)  # Cube rouge dans zone rouge
    manager.update_score()
    print(f"  Après placement correct: {manager.score}/{manager.total_objects}")
    print(f"  Tri complet: {manager.is_sorting_complete()}")
    
    print("\n✅ Tests du module objects terminés")

# Made with Bob