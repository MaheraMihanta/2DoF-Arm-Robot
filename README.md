# Bras Robotique 2DDL Asservi en Position avec GRBL

Projet de contrôle d'un bras robotique à 2 degrés de liberté (2DDL) utilisant des moteurs pas à pas pilotés par GRBL.

## 🎯 Objectif

Implémenter un système de contrôle en position en boucle ouverte pour un bras robotique 2DDL, en utilisant la cinématique inverse pour déterminer les consignes d'angles θ1 et θ2.

## 📁 Structure du Projet

```
SIMULATION/
├── phase1_simulation/     # Modélisation et simulation
│   ├── kinematics.py      # Cinématique directe et inverse
│   ├── simulator.py       # Simulateur visuel
│   └── config.py          # Configuration du bras
├── phase2_hardware/       # Commande matérielle
│   ├── grbl_interface.py  # Interface GRBL
│   ├── motor_control.py   # Contrôle des moteurs
│   └── a4988_config.py    # Configuration A4988
├── phase3_integration/    # Intégration complète
│   ├── robot_controller.py # Contrôleur principal
│   └── gui.py             # Interface graphique
├── tests/                 # Tests unitaires
├── docs/                  # Documentation
└── requirements.txt       # Dépendances Python
```

## 🚀 Plan d'Action

### Phase 1: Modélisation et Simulation
- ✅ Créer la structure du projet
- ⏳ Implémenter le modèle cinématique (direct et inverse)
- ⏳ Créer un simulateur visuel du bras 2DDL
- ⏳ Valider la cinématique inverse avec des tests

### Phase 2: Commande Matérielle
- ⏳ Créer l'interface de communication avec GRBL
- ⏳ Implémenter la conversion angles → commandes moteurs
- ⏳ Tester la communication GRBL

### Phase 3: Intégration et Test
- ⏳ Intégrer cinématique + contrôle GRBL
- ⏳ Créer une interface de contrôle
- ⏳ Tester sur le matériel réel
- ⏳ Documentation finale

## 🔧 Matériel Requis

- Arduino avec GRBL
- 2x Moteurs pas à pas
- 2x Drivers A4988
- Alimentation appropriée
- Câbles de connexion

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🎮 Utilisation

### Simulation (Phase 1)
```bash
python phase1_simulation/simulator.py
```

### Contrôle Matériel (Phase 2)
```bash
python phase2_hardware/grbl_interface.py
```

### Système Complet (Phase 3)
```bash
python phase3_integration/robot_controller.py
```

## 📚 Documentation

Consultez le dossier `docs/` pour la documentation détaillée :
- Théorie de la cinématique
- Configuration GRBL
- Guide d'utilisation

## 🤝 Contribution

Ce projet est développé dans le cadre d'une thèse.

## 📄 Licence

À définir