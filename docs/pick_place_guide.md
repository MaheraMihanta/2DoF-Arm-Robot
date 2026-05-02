# Guide Pick & Place - Bras Robotique 2DDL

## Introduction

Ce guide explique le système de préhension et de tri d'objets implémenté pour le bras robotique 2DDL. Le système permet au robot de saisir des cubes colorés et de les trier automatiquement dans des zones de dépôt correspondant à leur couleur.

---

## 1. Théorie de la Préhension

### 1.1 Concept de la Pince (Gripper)

La pince est un effecteur terminal attaché à l'extrémité du bras robotique. Elle possède deux mâchoires qui peuvent s'ouvrir et se fermer pour saisir des objets.

**Paramètres de la pince :**
- **Longueur** : 40 mm depuis l'effecteur final
- **Largeur ouverte** : 80 mm (permet de saisir des objets jusqu'à 80 mm)
- **Largeur fermée** : 30 mm (maintien sécurisé des objets)
- **Vitesse d'animation** : 0.3 secondes pour ouvrir/fermer

**États de la pince :**
- `OPEN` : Pince ouverte, prête à saisir
- `CLOSED` : Pince fermée, peut tenir un objet
- `OPENING` : Animation d'ouverture en cours
- `CLOSING` : Animation de fermeture en cours

### 1.2 Détection de Saisie

La saisie d'un objet est possible si :
1. La pince est ouverte
2. L'objet est à portée (distance ≤ tolérance de saisie)
3. La pince se ferme ensuite pour maintenir l'objet

**Tolérance de saisie** : 5 mm par défaut

### 1.3 Cinématique de la Pince

La position de la pince est calculée en prolongeant l'effecteur final :

```
gripper_x = end_effector_x + gripper_length × cos(θ_bras)
gripper_y = end_effector_y + gripper_length × sin(θ_bras)
```

Où `θ_bras` est l'angle du segment L2 par rapport à l'horizontale.

---

## 2. Objets Manipulables

### 2.1 Cubes Colorés

Les cubes sont des objets simples avec les propriétés suivantes :
- **Taille** : 20 mm × 20 mm
- **Couleurs disponibles** : rouge, bleu, vert, jaune
- **États** : libre ou saisi

**Représentation visuelle :**
- Carré coloré avec bordure noire
- Bordure épaisse (3px) si saisi
- Croix blanche au centre si tenu par la pince

### 2.2 Zones de Dépôt

Chaque couleur possède une zone de dépôt dédiée :

| Couleur | Position (x, y) | Distance du centre |
|---------|-----------------|-------------------|
| Rouge   | (250, 150)      | ~290 mm          |
| Bleu    | (250, 50)       | ~255 mm          |
| Vert    | (150, 200)      | ~250 mm          |
| Jaune   | (150, 50)       | ~158 mm          |

**Taille des zones** : 40 mm × 40 mm (2× la taille d'un cube)

### 2.3 Génération Intelligente des Positions

Les cubes sont générés aléatoirement dans l'espace de travail atteignable :

**Algorithme de génération :**
```
Pour chaque cube :
    1. Générer position en coordonnées polaires
       - Rayon : 100-280 mm (zone sûre)
       - Angle : -90° à +90° (devant le robot)
    
    2. Vérifier atteignabilité
       - Distance entre r_min+20 et r_max-20
       - r_min = |L1 - L2| = 50 mm
       - r_max = L1 + L2 = 350 mm
    
    3. Vérifier espacement
       - Distance minimale entre cubes : 2.5 × taille_cube
    
    4. Éviter les zones de dépôt
       - Marge de 50 mm autour de chaque zone
```

---

## 3. Trajectoires Pick & Place

### 3.1 Trajectoire de Saisie (Pick)

Une trajectoire de saisie se compose de 3 phases :

**Phase 1 : Approche verticale**
- Descendre à une hauteur d'approche (50 mm) au-dessus du cube
- Pince ouverte

**Phase 2 : Descente**
- Descendre jusqu'au niveau du cube
- Fermer la pince à mi-parcours

**Phase 3 : Remontée**
- Remonter à la hauteur d'approche
- Cube saisi et tenu par la pince

**Nombre de points** : ~30 points par phase

### 3.2 Trajectoire de Dépôt (Place)

Une trajectoire de dépôt se compose de 3 phases :

**Phase 1 : Approche**
- Se déplacer au-dessus de la zone de dépôt
- Hauteur d'approche : 50 mm
- Pince fermée, cube tenu

**Phase 2 : Descente**
- Descendre jusqu'au niveau de dépôt
- Ouvrir la pince à 75% de la descente

**Phase 3 : Remontée**
- Remonter à la hauteur d'approche
- Cube déposé, pince ouverte

### 3.3 Trajectoire Complète Pick & Place

La méthode `compute_pick_and_place_trajectory()` combine les deux trajectoires :

```
Trajectoire complète = [
    Points de descente pick (approche → cube),
    Points de remontée pick (cube → hauteur),
    Points de transfert (position pick → position place),
    Points de descente place (hauteur → zone),
    Points de remontée place (zone → hauteur)
]
```

**Optimisation** : Les points dupliqués entre phases sont éliminés.

**Format des points** : `[x, y, θ1, θ2]`
- `x, y` : Position cartésienne (mm)
- `θ1, θ2` : Angles articulaires (radians)

---

## 4. Algorithme de Tri

### 4.1 Stratégie de Tri

Le scénario `ColorSortingScenario` implémente une stratégie de tri simple mais efficace :

**Algorithme du plus proche :**
```
Tant qu'il reste des cubes non triés :
    1. Trouver le cube non trié le plus proche
    2. Planifier trajectoire pick & place vers sa zone
    3. Exécuter la trajectoire
    4. Mettre à jour le score
```

**Critère de tri :**
- Un cube est considéré "trié" s'il est dans la zone de sa couleur
- Distance minimale pour validation : centre du cube dans la zone

### 4.2 États du Scénario

Le scénario peut être dans l'un des états suivants :

| État | Description |
|------|-------------|
| `IDLE` | En attente, prêt à démarrer |
| `INITIALIZING` | Création des objets en cours |
| `RUNNING` | Tri en cours d'exécution |
| `PAUSED` | Tri mis en pause |
| `COMPLETED` | Tous les cubes triés avec succès |
| `FAILED` | Échec (position inaccessible) |

### 4.3 Synchronisation Pince-Trajectoire

L'exécution de la trajectoire est synchronisée avec les actions de la pince :

**Ratios de progression :**
- **25-35%** : Fermeture de la pince (descente vers le cube)
- **35-45%** : Saisie du cube (après fermeture)
- **70-80%** : Ouverture de la pince (au-dessus de la zone)

**Mise à jour continue :**
- La position du cube tenu est mise à jour à chaque frame
- Synchronisation avec la position de la pince en temps réel

---

## 5. Métriques et Suivi

### 5.1 Statistiques de Performance

Le système suit les métriques suivantes :

- **Nombre total de cubes** : Cubes à trier
- **Cubes triés** : Cubes correctement placés
- **Nombre de mouvements** : Trajectoires exécutées
- **Placements réussis** : Cubes dans la bonne zone
- **Tentatives échouées** : Trajectoires impossibles
- **Temps écoulé** : Durée totale du tri

### 5.2 Calcul du Score

```python
score = nombre_de_cubes_correctement_placés
progression = (score / total_cubes) × 100%
```

Un cube est correctement placé si :
1. Il est dans une zone de dépôt
2. La couleur du cube correspond à la couleur de la zone

---

## 6. Gestion des Erreurs

### 6.1 Positions Inaccessibles

Si un cube ou une zone est inaccessible :
- La cinématique inverse retourne `None`
- Le scénario enregistre un échec
- Le tri continue avec le cube suivant

### 6.2 Collisions (Non implémenté)

**Note** : La détection de collision entre cubes n'est pas implémentée dans cette version. Les cubes peuvent se chevaucher visuellement mais cela n'affecte pas la logique de tri.

### 6.3 Limites Articulaires

Toutes les trajectoires respectent les limites articulaires :
- θ1 : -180° à +180°
- θ2 : -150° à +150°

---

## 7. Utilisation Pratique

### 7.1 Contrôles du Simulateur

| Touche | Action |
|--------|--------|
| **P** | Démarrer/arrêter le tri automatique |
| **O** | Ouvrir/fermer la pince manuellement |
| **C** | Créer de nouveaux cubes aléatoires |
| **S** | Pause/reprendre le scénario |
| **R** | Réinitialiser le robot |

### 7.2 Exemple de Session

```python
# Initialiser le scénario avec 4 cubes
scenario.initialize(num_cubes=4)

# Démarrer le tri automatique
scenario.start()

# Le système exécute automatiquement :
# 1. Trouve le cube le plus proche
# 2. Planifie la trajectoire pick & place
# 3. Exécute le mouvement
# 4. Répète jusqu'à ce que tous les cubes soient triés
```

### 7.3 Intégration dans un Projet

```python
from phase1_simulation.config import RobotConfig
from phase1_simulation.kinematics import Kinematics
from phase1_simulation.gripper import Gripper
from phase1_simulation.objects import ObjectManager
from phase1_simulation.pick_place_scenarios import ColorSortingScenario

# Configuration
config = RobotConfig()
kinematics = Kinematics(config)
gripper = Gripper(config)
object_manager = ObjectManager(config)

# Créer le scénario
scenario = ColorSortingScenario(config, kinematics, gripper, object_manager)

# Initialiser et démarrer
scenario.initialize(num_cubes=4, colors=['red', 'blue', 'green', 'yellow'])
scenario.start()

# Exécuter une étape
current_pos = kinematics.forward_kinematics(theta1, theta2)
result = scenario.execute_sort_step(current_pos)

if result:
    trajectory, description = result
    # Exécuter la trajectoire...
```

---

## 8. Améliorations Futures

### 8.1 Optimisations Possibles

- **Algorithme TSP** : Optimiser l'ordre de tri pour minimiser la distance totale
- **Interpolation spline** : Trajectoires plus fluides
- **Détection de collision** : Éviter les chevauchements entre cubes
- **Physique réaliste** : Gravité, friction, rebonds

### 8.2 Extensions

- **Objets de formes variées** : Cylindres, sphères
- **Tri multi-critères** : Couleur + taille + forme
- **Zones de dépôt dynamiques** : Positions changeantes
- **Mode collaboratif** : Plusieurs bras robotiques

---

## Conclusion

Le système pick & place implémenté démontre les capacités d'un bras robotique 2DDL pour des tâches de manipulation d'objets. L'architecture modulaire permet une extension facile et une intégration dans des projets plus complexes.

**Points forts :**
- ✅ Trajectoires validées par cinématique inverse
- ✅ Synchronisation précise pince-mouvement
- ✅ Génération intelligente de positions atteignables
- ✅ Gestion robuste des erreurs
- ✅ Métriques de performance complètes

---

*Document généré par IBM Bob - 2 mai 2026*