# 🚀 Démarrage Rapide - Bras Robotique 2DDL

## Installation Express (5 minutes)

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Tester la configuration
python phase1_simulation/config.py

# 3. Lancer le simulateur
python phase1_simulation/simulator.py
```

## 🎮 Premiers Pas avec le Simulateur

### Commandes Essentielles

| Touche | Action |
|--------|--------|
| **←→** | Contrôler θ1 (articulation 1) |
| **↑↓** | Contrôler θ2 (articulation 2) |
| **Clic gauche** | Définir une position cible |
| **M** | Changer de mode (angles/position) |
| **R** | Réinitialiser |
| **ESC** | Quitter |

### Exercice 1: Contrôle Manuel

1. Lancez le simulateur
2. Utilisez les flèches pour déplacer le bras
3. Observez les angles et la position dans le panneau d'info

### Exercice 2: Contrôle par Position

1. Appuyez sur **M** pour passer en mode position
2. Cliquez sur un point dans l'espace de travail (zone bleue)
3. Le bras se déplace automatiquement vers ce point

## 🔧 Test avec Matériel (10 minutes)

### Prérequis
- Arduino avec GRBL flashé
- 2× Moteurs pas à pas
- 2× Drivers A4988
- Alimentation 12-24V

### Étapes Rapides

```bash
# 1. Vérifier la connexion
python phase2_hardware/grbl_interface.py
# Entrer votre port série (ex: COM3)

# 2. Tester les moteurs
python phase2_hardware/motor_control.py
# Menu: 1 (Homing) puis 3 (Déplacer vers angles)

# 3. Lancer l'interface complète
python phase3_integration/gui.py
```

## 📊 Interface Graphique

### Onglet Contrôle

1. **Connexion**
   - Mode: Choisir "simulation" ou "hardware"
   - Port: Entrer le port série (ex: COM3)
   - Cliquer "Connecter"

2. **Contrôle par Angles**
   - Ajuster θ1 et θ2 avec les curseurs
   - Cliquer "Déplacer"

3. **Contrôle par Position**
   - Entrer X et Y en mm
   - Cocher "Coude vers le haut" si désiré
   - Cliquer "Déplacer"

### Onglet Trajectoires

1. **Trajectoire Linéaire**
   - Entrer position cible (X, Y)
   - Nombre de points: 50 (par défaut)
   - Cliquer "Planifier" puis "Exécuter"

2. **Trajectoires Prédéfinies**
   - Carré, Cercle, ou Zigzag
   - Cliquer sur le bouton correspondant

## 🧪 Tests Unitaires

```bash
# Exécuter tous les tests
cd tests
pytest test_kinematics.py -v

# Test spécifique
pytest test_kinematics.py::TestKinematics::test_forward_kinematics_zero_angles -v
```

## 📝 Exemples de Code

### Exemple 1: Simulation Simple

```python
from phase1_simulation.config import config
from phase1_simulation.kinematics import Kinematics
import numpy as np

# Créer l'objet cinématique
kin = Kinematics(config)

# Cinématique directe
theta1, theta2 = np.radians(45), np.radians(30)
x, y = kin.forward_kinematics(theta1, theta2)
print(f"Position: ({x:.1f}, {y:.1f}) mm")

# Cinématique inverse
result = kin.inverse_kinematics(250, 150)
if result:
    theta1, theta2 = result
    print(f"Angles: θ1={np.degrees(theta1):.1f}°, θ2={np.degrees(theta2):.1f}°")
```

### Exemple 2: Contrôle Matériel

```python
import sys
sys.path.insert(0, 'phase1_simulation')
sys.path.insert(0, 'phase2_hardware')

from config import config
from grbl_interface import GRBLInterface
from motor_control import MotorController
import numpy as np

# Connexion GRBL
with GRBLInterface(port='COM3') as grbl:
    # Créer le contrôleur
    controller = MotorController(config, grbl)
    
    # Homing
    controller.home_motors()
    
    # Déplacer vers des angles
    controller.move_to_angles(np.radians(30), np.radians(20))
```

### Exemple 3: Système Complet

```python
import sys
sys.path.insert(0, 'phase1_simulation')
sys.path.insert(0, 'phase2_hardware')
sys.path.insert(0, 'phase3_integration')

from config import config
from robot_controller import RobotController, ControlMode

# Mode simulation
with RobotController(config, ControlMode.SIMULATION) as robot:
    # Déplacer vers une position
    robot.move_to_position(250, 150)
    
    # Planifier une trajectoire
    trajectory = robot.plan_linear_trajectory(300, 200, num_points=50)
    
    # Exécuter la trajectoire
    if trajectory is not None:
        robot.execute_trajectory(trajectory)
```

## 🎯 Cas d'Usage Typiques

### 1. Validation de la Cinématique

```bash
# Tester la cinématique
python phase1_simulation/kinematics.py

# Lancer les tests
pytest tests/test_kinematics.py -v
```

### 2. Calibration du Matériel

```bash
# Afficher la configuration A4988
python phase2_hardware/a4988_config.py

# Configurer GRBL
python phase2_hardware/motor_control.py
# Menu: 6 (Configurer GRBL)
```

### 3. Démonstration Interactive

```bash
# Interface complète
python phase3_integration/robot_controller.py

# Ou interface graphique
python phase3_integration/gui.py
```

## ⚠️ Problèmes Courants

### "Import numpy could not be resolved"

```bash
pip install numpy matplotlib pygame pyserial pytest
```

### "Port série introuvable"

**Windows:**
```python
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
for port in ports:
    print(port.device)
```

**Linux/Mac:**
```bash
ls /dev/tty*
# Chercher /dev/ttyUSB0 ou /dev/ttyACM0
```

### "Position non atteignable"

Vérifier que la position est dans l'espace de travail:
- Rayon max: L1 + L2 = 350 mm
- Rayon min: |L1 - L2| = 50 mm

### "Moteurs ne bougent pas"

1. Vérifier Vref sur les A4988
2. Vérifier l'alimentation moteurs
3. Vérifier les paramètres GRBL ($100, $101)

## 📚 Documentation Complète

- **Guide d'utilisation**: `docs/guide_utilisation.md`
- **Théorie cinématique**: `docs/theorie_cinematique.md`
- **README principal**: `README.md`

## 🆘 Support

1. Consulter la documentation dans `docs/`
2. Vérifier les exemples dans chaque module
3. Tester en mode simulation d'abord
4. Vérifier le câblage matériel

## 🎓 Prochaines Étapes

1. ✅ Maîtriser le simulateur
2. ✅ Comprendre la cinématique inverse
3. ✅ Tester avec le matériel
4. ✅ Créer vos propres trajectoires
5. ✅ Optimiser les paramètres

---

**Bon développement ! 🤖**