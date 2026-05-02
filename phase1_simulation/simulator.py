"""
Simulateur visuel du bras robotique 2DDL
Utilise Pygame pour la visualisation interactive
"""

import pygame
import numpy as np
from typing import List, Tuple, Optional

try:
    from .config import RobotConfig, config
    from .kinematics import Kinematics
except ImportError:
    from config import RobotConfig, config
    from kinematics import Kinematics


class RobotSimulator:
    """Simulateur visuel interactif du bras robotique"""
    
    def __init__(self, config: RobotConfig):
        """
        Initialise le simulateur
        
        Args:
            config: Configuration du robot
        """
        self.config = config
        self.kinematics = Kinematics(config)
        
        # Initialisation de Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.window_width, config.window_height)
        )
        pygame.display.set_caption("Simulateur Bras Robotique 2DDL")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # État du robot
        self.theta1 = 0.0
        self.theta2 = 0.0
        self.target_x = None
        self.target_y = None
        
        # Historique de trajectoire
        self.trajectory_history: List[Tuple[float, float]] = []
        self.max_history = 200
        
        # Mode d'interaction
        self.control_mode = "position"  # "angles" ou "position"
        self.elbow_up = True
        
        # Vitesse de contrôle manuel
        self.angle_step = np.radians(2)  # 2° par appui

        # Animation de mouvement
        self.animating = False
        self.animation_start_theta1 = 0.0
        self.animation_start_theta2 = 0.0
        self.animation_target_theta1 = 0.0
        self.animation_target_theta2 = 0.0
        self.animation_duration = 0.0
        self.animation_elapsed = 0.0
        
        # Couleurs
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.LIGHT_GRAY = (240, 240, 240)
        self.GRID_COLOR = (220, 220, 220)
        
        # Centre de l'écran (origine du robot)
        self.origin_x = config.window_width // 2
        self.origin_y = config.window_height // 2
        
        # État de l'interface
        self.show_workspace = True
        self.show_grid = True
        self.show_info = True
        
    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """
        Convertit les coordonnées monde (mm) en coordonnées écran (pixels)
        
        Args:
            x, y: Coordonnées en mm
            
        Returns:
            tuple: Coordonnées écran (pixels)
        """
        scale = self.config.get_scale_factor()
        screen_x = int(self.origin_x + x * scale)
        screen_y = int(self.origin_y - y * scale)  # Y inversé
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convertit les coordonnées écran (pixels) en coordonnées monde (mm)
        
        Args:
            screen_x, screen_y: Coordonnées écran
            
        Returns:
            tuple: Coordonnées monde (mm)
        """
        scale = self.config.get_scale_factor()
        x = (screen_x - self.origin_x) / scale
        y = (self.origin_y - screen_y) / scale
        return x, y
    
    def draw_grid(self):
        """Dessine une grille de référence"""
        if not self.show_grid:
            return
        
        grid_spacing = 50  # mm
        screen_spacing = int(grid_spacing * self.config.get_scale_factor())
        
        # Lignes verticales
        for x in range(0, self.config.window_width, screen_spacing):
            pygame.draw.line(self.screen, self.GRID_COLOR, 
                           (x, 0), (x, self.config.window_height), 1)
        
        # Lignes horizontales
        for y in range(0, self.config.window_height, screen_spacing):
            pygame.draw.line(self.screen, self.GRID_COLOR,
                           (0, y), (self.config.window_width, y), 1)
        
        # Axes principaux
        pygame.draw.line(self.screen, self.GRAY,
                        (self.origin_x, 0), 
                        (self.origin_x, self.config.window_height), 2)
        pygame.draw.line(self.screen, self.GRAY,
                        (0, self.origin_y), 
                        (self.config.window_width, self.origin_y), 2)
    
    def draw_workspace(self):
        """Dessine l'espace de travail du robot"""
        if not self.show_workspace:
            return
        
        # Cercle extérieur (portée maximale)
        r_max = int((self.config.L1 + self.config.L2) * self.config.get_scale_factor())
        pygame.draw.circle(self.screen, (200, 220, 255), 
                          (self.origin_x, self.origin_y), r_max, 2)
        
        # Cercle intérieur (portée minimale)
        r_min = int(abs(self.config.L1 - self.config.L2) * self.config.get_scale_factor())
        if r_min > 0:
            pygame.draw.circle(self.screen, (255, 220, 200),
                             (self.origin_x, self.origin_y), r_min, 2)
    
    def draw_robot(self):
        """Dessine le bras robotique"""
        # Obtenir les positions des articulations
        positions = self.kinematics.get_joint_positions(self.theta1, self.theta2)
        
        base = self.world_to_screen(*positions['base'])
        joint1 = self.world_to_screen(*positions['joint1'])
        end_effector = self.world_to_screen(*positions['end_effector'])
        
        # Dessiner la base
        pygame.draw.circle(self.screen, self.config.color_base, base, 15)
        pygame.draw.circle(self.screen, self.BLACK, base, 15, 2)
        
        # Dessiner le premier segment (L1)
        pygame.draw.line(self.screen, self.config.color_link1, 
                        base, joint1, 8)
        
        # Dessiner le deuxième segment (L2)
        pygame.draw.line(self.screen, self.config.color_link2,
                        joint1, end_effector, 8)
        
        # Dessiner l'articulation 1
        pygame.draw.circle(self.screen, self.config.color_joint, joint1, 10)
        pygame.draw.circle(self.screen, self.BLACK, joint1, 10, 2)
        
        # Dessiner l'effecteur final
        pygame.draw.circle(self.screen, self.config.color_end_effector, 
                          end_effector, 12)
        pygame.draw.circle(self.screen, self.BLACK, end_effector, 12, 2)
        
        self.append_trajectory_point(positions['end_effector'])

    def append_trajectory_point(self, point: Tuple[float, float]):
        """Ajoute un point à l'historique si le mouvement a réellement progressé."""
        if self.trajectory_history:
            last_x, last_y = self.trajectory_history[-1]
            if np.hypot(point[0] - last_x, point[1] - last_y) < 0.5:
                return

        self.trajectory_history.append(point)
        if len(self.trajectory_history) > self.max_history:
            self.trajectory_history.pop(0)
    
    def draw_trajectory(self):
        """Dessine l'historique de la trajectoire"""
        if len(self.trajectory_history) < 2:
            return
        
        points = [self.world_to_screen(x, y) for x, y in self.trajectory_history]
        
        for i in range(len(points) - 1):
            intensity = 90 + int(165 * (i + 1) / len(points))
            color = (80, 110, min(intensity, 255))
            pygame.draw.line(self.screen, color, points[i], points[i + 1], 2)
    
    def draw_target(self):
        """Dessine la position cible si définie"""
        if self.target_x is not None and self.target_y is not None:
            target_screen = self.world_to_screen(self.target_x, self.target_y)
            
            # Vérifier si la cible est atteignable
            reachable = self.kinematics.is_position_reachable(
                self.target_x, self.target_y
            )
            
            color = (0, 255, 0) if reachable else (255, 0, 0)
            
            # Dessiner une croix
            size = 15
            pygame.draw.line(self.screen, color,
                           (target_screen[0] - size, target_screen[1]),
                           (target_screen[0] + size, target_screen[1]), 3)
            pygame.draw.line(self.screen, color,
                           (target_screen[0], target_screen[1] - size),
                           (target_screen[0], target_screen[1] + size), 3)
            pygame.draw.circle(self.screen, color, target_screen, 8, 2)
    
    def draw_info(self):
        """Dessine les informations à l'écran"""
        if not self.show_info:
            return
        
        # Panneau d'information
        info_rect = pygame.Rect(10, 10, 300, 280)
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, info_rect)
        pygame.draw.rect(self.screen, self.BLACK, info_rect, 2)
        
        y_offset = 25
        line_height = 22
        
        # Titre
        title = self.font.render("Bras Robotique 2DDL", True, self.BLACK)
        self.screen.blit(title, (20, y_offset))
        y_offset += line_height + 10
        
        # Angles actuels
        info_lines = [
            f"θ1: {np.degrees(self.theta1):6.1f}°",
            f"θ2: {np.degrees(self.theta2):6.1f}°",
            "",
        ]
        
        # Position actuelle
        x, y = self.kinematics.forward_kinematics(self.theta1, self.theta2)
        info_lines.extend([
            f"Position:",
            f"  x: {x:6.1f} mm",
            f"  y: {y:6.1f} mm",
            "",
        ])
        
        # Mode de contrôle
        mode_text = "Angles" if self.control_mode == "angles" else "Position"
        info_lines.append(f"Mode: {mode_text}")
        
        if self.control_mode == "position":
            elbow_text = "Haut" if self.elbow_up else "Bas"
            info_lines.append(f"Coude: {elbow_text}")
        
        # Afficher les lignes
        for line in info_lines:
            text = self.small_font.render(line, True, self.BLACK)
            self.screen.blit(text, (20, y_offset))
            y_offset += line_height
        
        # Commandes
        y_offset += 10
        commands_title = self.small_font.render("Commandes:", True, self.BLACK)
        self.screen.blit(commands_title, (20, y_offset))
        y_offset += line_height
        
        commands = [
            "Flèches: Contrôle angles",
            "Clic: Définir cible",
            "M: Changer mode",
            "E: Changer coude",
            "R: Réinitialiser",
            "G: Grille On/Off",
            "W: Workspace On/Off",
            "ESC: Quitter"
        ]
        
        for cmd in commands:
            text = self.small_font.render(cmd, True, self.BLACK)
            self.screen.blit(text, (20, y_offset))
            y_offset += 18

    def start_animation(self, theta1: float, theta2: float):
        """Prépare une animation articulaire lissée."""
        delta1 = abs(theta1 - self.theta1)
        delta2 = abs(theta2 - self.theta2)

        speed1 = max(self.config.max_angular_velocity_1, 1e-6)
        speed2 = max(self.config.max_angular_velocity_2, 1e-6)
        duration = max(
            delta1 / speed1,
            delta2 / speed2,
            self.config.min_animation_duration,
        )

        self.animation_start_theta1 = self.theta1
        self.animation_start_theta2 = self.theta2
        self.animation_target_theta1 = theta1
        self.animation_target_theta2 = theta2
        self.animation_duration = min(duration, self.config.max_animation_duration)
        self.animation_elapsed = 0.0
        self.animating = True

    def update_animation(self, dt: float):
        """Met à jour l'animation active."""
        if not self.animating:
            return

        self.animation_elapsed += dt
        progress = min(self.animation_elapsed / max(self.animation_duration, 1e-6), 1.0)
        eased = 0.5 - 0.5 * np.cos(np.pi * progress)

        self.theta1 = self.animation_start_theta1 + (
            self.animation_target_theta1 - self.animation_start_theta1
        ) * eased
        self.theta2 = self.animation_start_theta2 + (
            self.animation_target_theta2 - self.animation_start_theta2
        ) * eased

        end_effector = self.kinematics.forward_kinematics(self.theta1, self.theta2)
        self.append_trajectory_point(end_effector)

        if progress >= 1.0:
            self.theta1 = self.animation_target_theta1
            self.theta2 = self.animation_target_theta2
            self.animating = False

    def set_target_position(self, x: float, y: float):
        """Définit une nouvelle cible cartésienne et lance l'animation si possible."""
        self.target_x = x
        self.target_y = y

        result = self.kinematics.inverse_kinematics(x, y, self.elbow_up)
        if result:
            self.start_animation(*result)
    
    def handle_input(self):
        """Gère les entrées utilisateur"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                elif event.key == pygame.K_m:
                    # Changer de mode
                    self.control_mode = "position" if self.control_mode == "angles" else "angles"
                
                elif event.key == pygame.K_e:
                    # Changer configuration du coude
                    self.elbow_up = not self.elbow_up
                
                elif event.key == pygame.K_r:
                    # Réinitialiser
                    self.theta1 = 0.0
                    self.theta2 = 0.0
                    self.animating = False
                    self.target_x = None
                    self.target_y = None
                    self.trajectory_history.clear()
                
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                
                elif event.key == pygame.K_w:
                    self.show_workspace = not self.show_workspace
                
                elif event.key == pygame.K_i:
                    self.show_info = not self.show_info
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    # Définir une nouvelle cible
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    target_x, target_y = self.screen_to_world(mouse_x, mouse_y)
                    self.set_target_position(target_x, target_y)
        
        # Contrôle continu par les touches
        keys = pygame.key.get_pressed()
        
        if self.control_mode == "angles":
            if keys[pygame.K_LEFT]:
                self.animating = False
                self.theta1 += self.angle_step
            if keys[pygame.K_RIGHT]:
                self.animating = False
                self.theta1 -= self.angle_step
            if keys[pygame.K_UP]:
                self.animating = False
                self.theta2 += self.angle_step
            if keys[pygame.K_DOWN]:
                self.animating = False
                self.theta2 -= self.angle_step
            
            # Limiter les angles
            self.theta1 = np.clip(self.theta1, 
                                 self.config.theta1_min, 
                                 self.config.theta1_max)
            self.theta2 = np.clip(self.theta2,
                                 self.config.theta2_min,
                                 self.config.theta2_max)
        
        return True
    
    def run(self):
        """Boucle principale du simulateur"""
        running = True
        
        while running:
            dt = self.clock.tick(self.config.simulation_fps) / 1000.0
            
            # Gestion des événements
            running = self.handle_input()
            self.update_animation(dt)
            
            # Effacer l'écran
            self.screen.fill(self.WHITE)
            
            # Dessiner les éléments
            self.draw_grid()
            self.draw_workspace()
            self.draw_trajectory()
            self.draw_target()
            self.draw_robot()
            self.draw_info()
            
            # Mettre à jour l'affichage
            pygame.display.flip()
        
        pygame.quit()


def main():
    """Point d'entrée principal"""
    print("=== Simulateur Bras Robotique 2DDL ===")
    print(f"Configuration: L1={config.L1}mm, L2={config.L2}mm")
    print("\nDémarrage du simulateur...")
    
    simulator = RobotSimulator(config)
    simulator.run()
    
    print("Simulateur fermé.")


if __name__ == "__main__":
    main()

# Made with Bob
