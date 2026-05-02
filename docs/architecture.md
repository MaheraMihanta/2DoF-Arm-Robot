# Architecture du Projet - Bras Robotique 2DDL

## Vue d'Ensemble

Ce document décrit l'architecture logicielle du système de contrôle du bras robotique 2DDL.

## Structure des Modules

```
SIMULATION/
│
├── phase1_simulation/          # Phase 1: Modélisation et Simulation
│   ├── config.py              # Configuration du robot
│   ├── kinematics.py          # Cinématique directe et inverse
│   └── simulator.py           # Simulateur visuel (Pygame)
│
├── phase2_hardware/           # Phase 2: Contrôle Matériel
│   ├── grbl_interface.py      # Communication série avec GRBL
│   ├── motor_control.py       # Contrôle des moteurs
│   └── a4988_config.py        # Configuration drivers A4988
│
├── phase3_integration/        # Phase 3: Intégration
│   ├── robot_controller.py    # Contrôleur principal
│   └── gui.py                 # Interface graphique (Tkinter)
│
├── tests/                     # Tests unitaires
│   └── test_kinematics.py     # Tests de la cinématique
│
├── docs/                      # Documentation
│   ├── guide_utilisation.md   # Guide utilisateur
│   ├── theorie_cinematique.md # Théorie mathématique
│   └── architecture.md        # Ce document
│
├── README.md                  # Documentation principale
├── QUICKSTART.md             # Démarrage rapide
└── requirements.txt          # Dépendances Python
```

## Diagramme de Classes

### Phase 1: Simulation

```
┌─────────────────────────────────────────────────────────────┐
│                        RobotConfig                          │
├─────────────────────────────────────────────────────────────┤
│ + L1: float                    # Longueur segment 1         │
│ + L2: float                    # Longueur segment 2         │
│ + steps_per_revolution: int    # Pas par tour               │
│ + microsteps: int              # Microstepping              │
│ + theta1_min/max: float        # Limites angulaires         │
│ + theta2_min/max: float                                     │
├─────────────────────────────────────────────────────────────┤
│ + is_angle_valid()             # Vérifier limites           │
│ + angles_to_steps()            # Convertir angles → pas     │
│ + steps_to_angles()            # Convertir pas → angles     │
│ + get_workspace_limits()       # Limites espace travail     │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ utilise
                            │
┌─────────────────────────────────────────────────────────────┐
│                        Kinematics                           │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - L1: float                                                 │
│ - L2: float                                                 │
├─────────────────────────────────────────────────────────────┤
│ + forward_kinematics()         # (θ1,θ2) → (x,y)           │
│ + inverse_kinematics()         # (x,y) → (θ1,θ2)           │
│ + jacobian()                   # Matrice jacobienne         │
│ + get_joint_positions()        # Positions articulations    │
│ + is_position_reachable()      # Vérifier atteignabilité    │
│ + compute_trajectory()         # Planifier trajectoire      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ utilise
                            │
┌─────────────────────────────────────────────────────────────┐
│                      RobotSimulator                         │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - kinematics: Kinematics                                    │
│ - screen: pygame.Surface                                    │
│ - theta1, theta2: float        # État actuel                │
├─────────────────────────────────────────────────────────────┤
│ + draw_robot()                 # Dessiner le bras           │
│ + draw_workspace()             # Dessiner espace travail    │
│ + handle_input()               # Gérer entrées utilisateur  │
│ + run()                        # Boucle principale          │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Matériel

```
┌─────────────────────────────────────────────────────────────┐
│                      GRBLInterface                          │
├─────────────────────────────────────────────────────────────┤
│ - port: str                    # Port série                 │
│ - baudrate: int                # Vitesse communication      │
│ - serial_connection: Serial    # Connexion série            │
│ - is_connected: bool                                        │
├─────────────────────────────────────────────────────────────┤
│ + connect()                    # Établir connexion          │
│ + disconnect()                 # Fermer connexion           │
│ + send_command()               # Envoyer G-code             │
│ + get_status()                 # Lire statut GRBL           │
│ + home()                       # Homing                     │
│ + move_absolute()              # Déplacement absolu         │
│ + jog()                        # Déplacement manuel         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ utilise
                            │
┌─────────────────────────────────────────────────────────────┐
│                      MotorController                        │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - grbl: GRBLInterface                                       │
│ - current_theta1, theta2: float                             │
│ - current_steps_1, steps_2: int                             │
├─────────────────────────────────────────────────────────────┤
│ + move_to_angles()             # Déplacer vers angles       │
│ + move_incremental()           # Déplacement incrémental    │
│ + home_motors()                # Homing des moteurs         │
│ + execute_trajectory()         # Exécuter trajectoire       │
│ + angles_to_gcode_position()   # Convertir angles → G-code  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       A4988Config                           │
├─────────────────────────────────────────────────────────────┤
│ + microstep_modes: dict        # Configurations µstep       │
│ + max_current: float           # Courant max                │
│ + pin_mapping: dict            # Mapping des pins           │
├─────────────────────────────────────────────────────────────┤
│ + get_microstep_pins()         # Config pins MS1/MS2/MS3    │
│ + calculate_current_limit_vref() # Calcul Vref              │
│ + get_wiring_diagram()         # Schéma de câblage          │
│ + get_grbl_settings()          # Paramètres GRBL            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: Intégration

```
┌─────────────────────────────────────────────────────────────┐
│                      RobotController                        │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - kinematics: Kinematics                                    │
│ - grbl: GRBLInterface          # Optionnel                  │
│ - motor_controller: MotorController # Optionnel             │
│ - mode: ControlMode            # simulation/hardware/hybrid │
├─────────────────────────────────────────────────────────────┤
│ + move_to_angles()             # Déplacer vers angles       │
│ + move_to_position()           # Déplacer vers position     │
│ + execute_trajectory()         # Exécuter trajectoire       │
│ + plan_linear_trajectory()     # Planifier trajectoire      │
│ + home()                       # Retour origine             │
│ + get_current_position()       # Position actuelle          │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ utilise
                            │
┌─────────────────────────────────────────────────────────────┐
│                         RobotGUI                            │
├─────────────────────────────────────────────────────────────┤
│ - root: tk.Tk                  # Fenêtre principale         │
│ - robot: RobotController       # Contrôleur                 │
│ - config: RobotConfig                                       │
├─────────────────────────────────────────────────────────────┤
│ + create_control_tab()         # Onglet contrôle            │
│ + create_trajectory_tab()      # Onglet trajectoires        │
│ + create_config_tab()          # Onglet configuration       │
│ + connect()                    # Connecter robot            │
│ + move_to_angles()             # Déplacer vers angles       │
│ + move_to_position()           # Déplacer vers position     │
│ + plan_linear_trajectory()     # Planifier trajectoire      │
└─────────────────────────────────────────────────────────────┘
```

## Flux de Données

### 1. Mode Simulation

```
Utilisateur
    │
    ▼
Interface (GUI/Simulateur)
    │
    ▼
RobotController (mode=SIMULATION)
    │
    ▼
Kinematics
    │
    ├─→ forward_kinematics() → Position (x, y)
    │
    └─→ inverse_kinematics() → Angles (θ1, θ2)
```

### 2. Mode Matériel

```
Utilisateur
    │
    ▼
Interface (GUI/CLI)
    │
    ▼
RobotController (mode=HARDWARE)
    │
    ├─→ Kinematics → Calcul angles
    │
    └─→ MotorController
            │
            ▼
        GRBLInterface
            │
            ▼
        Port Série (USB)
            │
            ▼
        Arduino + GRBL
            │
            ▼
        Drivers A4988
            │
            ▼
        Moteurs Pas à Pas
            │
            ▼
        Bras Robotique
```

### 3. Mode Hybride

```
Utilisateur
    │
    ▼
Interface
    │
    ▼
RobotController (mode=HYBRID)
    │
    ├─→ Kinematics (simulation)
    │       │
    │       └─→ Visualisation
    │
    └─→ MotorController (matériel)
            │
            └─→ Contrôle physique
```

## Protocoles de Communication

### Communication GRBL

**Format des commandes:**
```
G-code → Arduino (GRBL) → Moteurs

Exemples:
- G90 G1 X100 Y50 F1000  # Déplacement absolu
- $H                      # Homing
- ?                       # Statut
- $X                      # Unlock
```

**Format des réponses:**
```
ok                        # Commande acceptée
error:N                   # Erreur (N = code)
<Idle|MPos:x,y,z|...>    # Statut
```

### Mapping Axes

```
Robot 2DDL          GRBL
─────────────────────────
θ1 (angle 1)    →   X (mm)
θ2 (angle 2)    →   Y (mm)
```

**Conversion:**
```python
# Angles → Position G-code
steps1, steps2 = config.angles_to_steps(theta1, theta2)
x_gcode = steps1 * 0.01  # mm
y_gcode = steps2 * 0.01  # mm
```

## Gestion des Erreurs

### Hiérarchie des Exceptions

```
Exception
│
├─ ValueError
│  ├─ Position hors limites
│  └─ Angles invalides
│
├─ ConnectionError
│  ├─ Port série introuvable
│  └─ GRBL non connecté
│
└─ RuntimeError
   ├─ Commande GRBL échouée
   └─ Timeout communication
```

### Stratégies de Récupération

1. **Position non atteignable:**
   - Vérifier avec `is_position_reachable()`
   - Proposer position la plus proche

2. **Erreur GRBL:**
   - Lire le code d'erreur
   - Tenter unlock ($X)
   - Soft reset si nécessaire

3. **Perte de communication:**
   - Détecter timeout
   - Tenter reconnexion
   - Mode dégradé (simulation)

## Extensibilité

### Ajouter un Nouveau Mode de Contrôle

```python
# 1. Définir le mode
class ControlMode(Enum):
    SIMULATION = "simulation"
    HARDWARE = "hardware"
    HYBRID = "hybrid"
    NOUVEAU_MODE = "nouveau_mode"  # Nouveau

# 2. Implémenter dans RobotController
def move_to_angles(self, theta1, theta2):
    if self.mode == ControlMode.NOUVEAU_MODE:
        # Logique spécifique
        pass
```

### Ajouter un Nouveau Type de Trajectoire

```python
# Dans Kinematics
def compute_circular_trajectory(self, center, radius, num_points):
    """Trajectoire circulaire"""
    trajectory = []
    for i in range(num_points):
        angle = 2 * np.pi * i / num_points
        x = center[0] + radius * np.cos(angle)
        y = center[1] + radius * np.sin(angle)
        
        result = self.inverse_kinematics(x, y)
        if result:
            trajectory.append([x, y, *result])
    
    return np.array(trajectory)
```

### Ajouter un Nouveau Driver

```python
# Créer un nouveau fichier: phase2_hardware/drv8825_config.py
class DRV8825Config:
    """Configuration pour driver DRV8825"""
    def __init__(self):
        self.microstep_modes = {
            1: (0, 0, 0),
            2: (1, 0, 0),
            4: (0, 1, 0),
            8: (1, 1, 0),
            16: (0, 0, 1),
            32: (1, 0, 1)  # DRV8825 supporte 1/32
        }
```

## Performance

### Optimisations Implémentées

1. **Calculs vectoriels:** Utilisation de NumPy
2. **Cache des positions:** Historique limité
3. **Communication asynchrone:** Threads pour GUI
4. **Validation précoce:** Vérification avant envoi

### Métriques Typiques

- **Calcul cinématique inverse:** < 1 ms
- **Envoi commande GRBL:** 10-50 ms
- **Fréquence simulation:** 60 FPS
- **Latence totale:** < 100 ms

## Sécurité

### Mécanismes de Sécurité

1. **Limites logicielles:**
   - Vérification angles avant mouvement
   - Vérification espace de travail

2. **Arrêt d'urgence:**
   - Soft reset GRBL (Ctrl-X)
   - Accessible depuis toutes les interfaces

3. **Validation des entrées:**
   - Type checking
   - Range checking
   - Sanitization

4. **Mode dégradé:**
   - Basculement automatique en simulation
   - Logs détaillés

## Tests

### Couverture des Tests

```
tests/test_kinematics.py
├─ TestKinematics
│  ├─ Cinématique directe (5 tests)
│  ├─ Cinématique inverse (8 tests)
│  ├─ Jacobienne (2 tests)
│  ├─ Espace de travail (3 tests)
│  └─ Trajectoires (2 tests)
│
└─ TestRobotConfig
   ├─ Configuration (4 tests)
   └─ Conversions (3 tests)

Total: 27 tests unitaires
```

### Exécution des Tests

```bash
# Tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=phase1_simulation --cov-report=html

# Tests spécifiques
pytest tests/test_kinematics.py::TestKinematics::test_forward_kinematics_zero_angles
```

## Maintenance

### Logs

Tous les modules utilisent `print()` pour les logs. Pour une application production, remplacer par `logging`:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Message d'information")
logger.warning("Avertissement")
logger.error("Erreur")
```

### Versioning

- **Version actuelle:** 1.0
- **Format:** MAJOR.MINOR.PATCH
- **Changelog:** À créer dans `CHANGELOG.md`

---

**Version:** 1.0  
**Date:** 2026-04-24  
**Auteur:** Projet Thèse - Bras Robotique 2DDL