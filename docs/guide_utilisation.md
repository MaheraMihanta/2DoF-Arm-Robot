# Guide d'Utilisation - Bras Robotique 2DDL

## Table des Matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Phase 1: Simulation](#phase-1-simulation)
4. [Phase 2: Contrôle Matériel](#phase-2-contrôle-matériel)
5. [Phase 3: Système Complet](#phase-3-système-complet)
6. [Dépannage](#dépannage)

---

## Introduction

Ce projet implémente un système de contrôle en position pour un bras robotique à 2 degrés de liberté (2DDL) utilisant:
- **Cinématique inverse** pour calculer les angles articulaires
- **Moteurs pas à pas** avec drivers A4988
- **GRBL** pour le contrôle des moteurs
- **Python** pour l'implémentation

### Architecture du Système

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Utilisateur                     │
│              (GUI Tkinter / Console / Simulateur)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Contrôleur Robot                           │
│              (robot_controller.py)                           │
└──────────────┬────────────────────────────┬──────────────────┘
               │                            │
┌──────────────▼──────────────┐  ┌─────────▼──────────────────┐
│   Cinématique Inverse       │  │   Contrôle Moteurs         │
│   (kinematics.py)           │  │   (motor_control.py)       │
└─────────────────────────────┘  └────────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   Interface GRBL          │
                                  │   (grbl_interface.py)     │
                                  └───────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   Arduino + GRBL          │
                                  └───────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   Drivers A4988           │
                                  └───────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   Moteurs Pas à Pas       │
                                  └───────────────────────────┘
```

---

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Arduino avec GRBL (pour le contrôle matériel)

### Installation des Dépendances

```bash
# Cloner ou télécharger le projet
cd SIMULATION

# Installer les dépendances
pip install -r requirements.txt
```

### Vérification de l'Installation

```bash
# Tester la configuration
python phase1_simulation/config.py

# Tester la cinématique
python phase1_simulation/kinematics.py
```

---

## Phase 1: Simulation

### 1.1 Tester la Cinématique

```bash
cd phase1_simulation
python kinematics.py
```

**Sortie attendue:**
```
=== Test de la Cinématique ===

1. Cinématique Directe:
   θ1=45.0°, θ2=30.0°
   → Position: x=318.20mm, y=183.71mm

2. Cinématique Inverse:
   Position cible: x=250.00mm, y=150.00mm
   → θ1=31.0°, θ2=28.1°
   Vérification: x=250.00mm, y=150.00mm
   Erreur: 0.0000mm
...
```

### 1.2 Lancer le Simulateur Visuel

```bash
python simulator.py
```

**Commandes du simulateur:**
- **Flèches** : Contrôle des angles (θ1 et θ2)
- **Clic gauche** : Définir une position cible
- **M** : Changer de mode (angles/position)
- **E** : Changer configuration du coude
- **R** : Réinitialiser
- **G** : Afficher/masquer la grille
- **W** : Afficher/masquer l'espace de travail
- **ESC** : Quitter

### 1.3 Exécuter les Tests

```bash
cd ../tests
pytest test_kinematics.py -v
```

---

## Phase 2: Contrôle Matériel

### 2.1 Préparation du Matériel

#### Câblage Arduino + A4988

Consultez le schéma détaillé:
```bash
python phase2_hardware/a4988_config.py
```

**Points importants:**
1. ⚠️ **Régler Vref AVANT de connecter les moteurs**
2. Ajouter des condensateurs (100µF + 0.1µF)
3. Vérifier la polarité des moteurs
4. Prévoir un dissipateur thermique

#### Configuration GRBL

1. Flasher GRBL sur l'Arduino:
   - Télécharger GRBL depuis https://github.com/gnea/grbl
   - Utiliser l'IDE Arduino pour flasher

2. Configurer les paramètres:
```bash
python phase2_hardware/motor_control.py
# Choisir option 6: Configurer GRBL
```

### 2.2 Test de Communication GRBL

```bash
cd phase2_hardware
python grbl_interface.py
```

**Menu de test:**
```
1. Statut          - Vérifier l'état de GRBL
2. Homing          - Retour à l'origine
3. Unlock          - Déverrouiller après alarme
4. Définir origine - Définir position actuelle comme (0,0)
5-7. Jog           - Mouvements de test
8. Paramètres      - Afficher configuration GRBL
```

### 2.3 Test des Moteurs

```bash
python motor_control.py
```

**Séquence de test recommandée:**
1. Homing (option 1)
2. Définir origine (option 2)
3. Déplacer vers angles (option 3) - Tester avec petits angles
4. Vérifier la position (option 5)

---

## Phase 3: Système Complet

### 3.1 Interface en Ligne de Commande

```bash
cd phase3_integration
python robot_controller.py
```

**Modes disponibles:**
- **Simulation** : Test sans matériel
- **Matériel** : Contrôle direct du robot
- **Hybride** : Simulation + contrôle matériel

### 3.2 Interface Graphique

```bash
python gui.py
```

**Fonctionnalités:**
- Contrôle par angles ou position
- Planification de trajectoires
- Trajectoires prédéfinies (carré, cercle)
- Console de logs
- Configuration en temps réel

### 3.3 Exemples d'Utilisation

#### Exemple 1: Déplacement Simple

```python
from config import config
from robot_controller import RobotController, ControlMode
import numpy as np

# Mode simulation
with RobotController(config, ControlMode.SIMULATION) as robot:
    # Déplacer vers des angles
    robot.move_to_angles(np.radians(45), np.radians(30))
    
    # Déplacer vers une position
    robot.move_to_position(250, 150)
    
    # Obtenir la position actuelle
    x, y = robot.get_current_position()
    print(f"Position: ({x:.1f}, {y:.1f})")
```

#### Exemple 2: Trajectoire Linéaire

```python
# Planifier une trajectoire
trajectory = robot.plan_linear_trajectory(300, 200, num_points=50)

if trajectory is not None:
    # Exécuter la trajectoire
    robot.execute_trajectory(trajectory, feed_rate=1000)
```

#### Exemple 3: Trajectoire Circulaire

```python
import numpy as np

# Centre et rayon du cercle
center_x, center_y = 225, 125
radius = 30
num_points = 36

# Générer les points
for i in range(num_points + 1):
    angle = 2 * np.pi * i / num_points
    x = center_x + radius * np.cos(angle)
    y = center_y + radius * np.sin(angle)
    robot.move_to_position(x, y)
```

---

## Dépannage

### Problème: Impossible de se connecter à GRBL

**Solutions:**
1. Vérifier le port série:
   ```python
   import serial.tools.list_ports
   ports = serial.tools.list_ports.comports()
   for port in ports:
       print(port.device)
   ```

2. Vérifier que GRBL est flashé sur l'Arduino
3. Fermer les autres programmes utilisant le port série
4. Essayer un autre câble USB

### Problème: Position non atteignable

**Causes possibles:**
- Position hors de l'espace de travail
- Angles hors limites
- Configuration incorrecte des longueurs L1, L2

**Vérification:**
```python
from kinematics import Kinematics
from config import config

kin = Kinematics(config)
print(f"Position atteignable: {kin.is_position_reachable(x, y)}")
```

### Problème: Moteurs ne bougent pas

**Vérifications:**
1. Vref correctement réglé
2. Alimentation moteurs connectée
3. Pins ENABLE à LOW
4. Câblage correct (STEP, DIR)
5. Paramètres GRBL corrects ($100, $101)

### Problème: Mouvements erratiques

**Solutions:**
1. Réduire la vitesse (feed_rate)
2. Augmenter l'accélération dans GRBL ($120, $121)
3. Vérifier les condensateurs
4. Vérifier le câblage des phases moteur

### Problème: Erreur de précision

**Causes:**
- Quantification des pas moteur
- Jeu mécanique
- Flexibilité des segments

**Amélioration:**
1. Augmenter le microstepping (1/16 ou 1/32)
2. Ajouter des réducteurs
3. Calibrer les paramètres steps/mm

---

## Paramètres Importants

### Configuration Robot (config.py)

```python
L1 = 200.0  # Longueur segment 1 (mm)
L2 = 150.0  # Longueur segment 2 (mm)
steps_per_revolution = 200  # Pas par tour
microsteps = 16  # Microstepping
```

### Paramètres GRBL Critiques

```
$100 = 100.0  # X steps/mm (à calibrer)
$101 = 100.0  # Y steps/mm (à calibrer)
$110 = 2000.0 # X max rate (mm/min)
$111 = 2000.0 # Y max rate (mm/min)
$120 = 500.0  # X acceleration (mm/s²)
$121 = 500.0  # Y acceleration (mm/s²)
```

### Calibration

Pour calibrer les steps/mm:
1. Marquer une position de départ
2. Commander un déplacement de 100mm
3. Mesurer le déplacement réel
4. Ajuster: `$100 = $100 * (100 / mesure_réelle)`

---

## Ressources Supplémentaires

- **Documentation GRBL**: https://github.com/gnea/grbl/wiki
- **Datasheet A4988**: https://www.pololu.com/product/1182
- **Théorie cinématique**: Voir `docs/theorie_cinematique.md`

---

## Support

Pour toute question ou problème:
1. Consulter la section Dépannage
2. Vérifier les logs dans la console
3. Tester en mode simulation d'abord
4. Vérifier le câblage matériel

---

**Version:** 1.0  
**Date:** 2026-04-24  
**Auteur:** Projet Thèse - Bras Robotique 2DDL