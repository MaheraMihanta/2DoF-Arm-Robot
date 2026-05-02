# Théorie de la Cinématique - Bras Robotique 2DDL

## Table des Matières

1. [Introduction](#introduction)
2. [Modèle Géométrique](#modèle-géométrique)
3. [Cinématique Directe](#cinématique-directe)
4. [Cinématique Inverse](#cinématique-inverse)
5. [Jacobienne](#jacobienne)
6. [Espace de Travail](#espace-de-travail)
7. [Singularités](#singularités)

---

## Introduction

Un bras robotique à 2 degrés de liberté (2DDL) est composé de deux segments rigides reliés par des articulations rotatives. Ce document présente la théorie mathématique nécessaire pour contrôler ce type de robot.

### Notation

- **L₁** : Longueur du premier segment (bras)
- **L₂** : Longueur du deuxième segment (avant-bras)
- **θ₁** : Angle de la première articulation (base)
- **θ₂** : Angle de la deuxième articulation (coude)
- **(x, y)** : Position cartésienne de l'effecteur final

---

## Modèle Géométrique

### Schéma du Robot

```
                    Effecteur (x, y)
                         ●
                        /
                       /
                      / L₂
                     /
                    / θ₂
                   ●────────── Articulation 2
                  /
                 /
                / L₁
               /
              / θ₁
             ●────────────────── Base (0, 0)
```

### Système de Coordonnées

- **Origine** : Base du robot (articulation 1)
- **Axe X** : Horizontal, vers la droite
- **Axe Y** : Vertical, vers le haut
- **Angles** : Mesurés dans le sens trigonométrique (anti-horaire)

---

## Cinématique Directe

### Problème

Étant donnés les angles articulaires θ₁ et θ₂, calculer la position cartésienne (x, y) de l'effecteur final.

### Solution

La position de l'effecteur final est obtenue par composition des transformations:

```
x = L₁·cos(θ₁) + L₂·cos(θ₁ + θ₂)
y = L₁·sin(θ₁) + L₂·sin(θ₁ + θ₂)
```

### Démonstration

1. **Position de l'articulation 2** (extrémité du segment 1):
   ```
   x₁ = L₁·cos(θ₁)
   y₁ = L₁·sin(θ₁)
   ```

2. **Position de l'effecteur** (extrémité du segment 2):
   - L'angle absolu du segment 2 est θ₁ + θ₂
   - Le vecteur du segment 2 est:
     ```
     Δx = L₂·cos(θ₁ + θ₂)
     Δy = L₂·sin(θ₁ + θ₂)
     ```
   
3. **Position finale**:
   ```
   x = x₁ + Δx = L₁·cos(θ₁) + L₂·cos(θ₁ + θ₂)
   y = y₁ + Δy = L₁·sin(θ₁) + L₂·sin(θ₁ + θ₂)
   ```

### Implémentation Python

```python
def forward_kinematics(theta1, theta2, L1, L2):
    x = L1 * np.cos(theta1) + L2 * np.cos(theta1 + theta2)
    y = L1 * np.sin(theta1) + L2 * np.sin(theta1 + theta2)
    return x, y
```

---

## Cinématique Inverse

### Problème

Étant donnée une position cartésienne (x, y), calculer les angles articulaires θ₁ et θ₂ nécessaires pour atteindre cette position.

### Solution Géométrique

#### Étape 1: Calcul de θ₂

Utilisation de la **loi des cosinus**:

```
r² = x² + y²
r² = L₁² + L₂² + 2·L₁·L₂·cos(θ₂)

cos(θ₂) = (r² - L₁² - L₂²) / (2·L₁·L₂)
```

Donc:
```
θ₂ = ±arccos((r² - L₁² - L₂²) / (2·L₁·L₂))
```

**Deux solutions possibles:**
- θ₂ > 0 : Configuration "coude vers le haut"
- θ₂ < 0 : Configuration "coude vers le bas"

#### Étape 2: Calcul de θ₁

Décomposition géométrique:

```
θ₁ = atan2(y, x) - atan2(L₂·sin(θ₂), L₁ + L₂·cos(θ₂))
```

Où:
- `atan2(y, x)` : Angle de la ligne base-cible
- `atan2(L₂·sin(θ₂), L₁ + L₂·cos(θ₂))` : Angle de correction

### Conditions d'Existence

La position (x, y) est atteignable si et seulement si:

```
|L₁ - L₂| ≤ r ≤ L₁ + L₂
```

Où r = √(x² + y²) est la distance de la base à la cible.

### Implémentation Python

```python
def inverse_kinematics(x, y, L1, L2, elbow_up=True):
    # Distance à la cible
    r = np.sqrt(x**2 + y**2)
    
    # Vérifier l'atteignabilité
    if r > (L1 + L2) or r < abs(L1 - L2):
        return None  # Position non atteignable
    
    # Calcul de θ₂
    cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    
    if abs(cos_theta2) > 1.0:
        return None
    
    if elbow_up:
        theta2 = np.arccos(cos_theta2)
    else:
        theta2 = -np.arccos(cos_theta2)
    
    # Calcul de θ₁
    k1 = L1 + L2 * np.cos(theta2)
    k2 = L2 * np.sin(theta2)
    theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)
    
    return theta1, theta2
```

### Exemple Numérique

**Données:**
- L₁ = 200 mm
- L₂ = 150 mm
- Cible: (250, 150) mm

**Calcul:**

1. Distance: r = √(250² + 150²) = 291.55 mm
2. Vérification: 50 ≤ 291.55 ≤ 350 ✓
3. cos(θ₂) = (291.55² - 200² - 150²) / (2·200·150) = 0.4518
4. θ₂ = arccos(0.4518) = 63.2° (coude haut)
5. k₁ = 200 + 150·cos(63.2°) = 267.77
6. k₂ = 150·sin(63.2°) = 133.83
7. θ₁ = atan2(150, 250) - atan2(133.83, 267.77) = 30.96° - 26.57° = 4.39°

**Vérification:**
```
x = 200·cos(4.39°) + 150·cos(4.39° + 63.2°) = 250.0 ✓
y = 200·sin(4.39°) + 150·sin(4.39° + 63.2°) = 150.0 ✓
```

---

## Jacobienne

### Définition

La matrice jacobienne J relie les vitesses articulaires aux vitesses cartésiennes:

```
[ẋ]   [J₁₁  J₁₂] [θ̇₁]
[ẏ] = [J₂₁  J₂₂] [θ̇₂]
```

### Calcul

Dérivation de la cinématique directe:

```
ẋ = ∂x/∂θ₁·θ̇₁ + ∂x/∂θ₂·θ̇₂
ẏ = ∂y/∂θ₁·θ̇₁ + ∂y/∂θ₂·θ̇₂
```

**Résultat:**

```
J = [[-L₁·sin(θ₁) - L₂·sin(θ₁+θ₂),  -L₂·sin(θ₁+θ₂)]
     [ L₁·cos(θ₁) + L₂·cos(θ₁+θ₂),   L₂·cos(θ₁+θ₂)]]
```

### Utilisation

1. **Vitesses cartésiennes → vitesses articulaires:**
   ```
   [θ̇₁]       [ẋ]
   [θ̇₂] = J⁻¹ [ẏ]
   ```

2. **Forces cartésiennes → couples articulaires:**
   ```
   [τ₁]      [Fₓ]
   [τ₂] = Jᵀ [Fᵧ]
   ```

### Implémentation Python

```python
def jacobian(theta1, theta2, L1, L2):
    s1 = np.sin(theta1)
    c1 = np.cos(theta1)
    s12 = np.sin(theta1 + theta2)
    c12 = np.cos(theta1 + theta2)
    
    J = np.array([
        [-L1*s1 - L2*s12, -L2*s12],
        [ L1*c1 + L2*c12,  L2*c12]
    ])
    
    return J
```

---

## Espace de Travail

### Définition

L'espace de travail est l'ensemble de toutes les positions (x, y) atteignables par l'effecteur final.

### Forme Géométrique

Pour un robot 2DDL plan, l'espace de travail est une **couronne circulaire**:

```
Rayon extérieur: R_max = L₁ + L₂
Rayon intérieur: R_min = |L₁ - L₂|
```

### Cas Particuliers

1. **L₁ = L₂:**
   - R_min = 0
   - L'espace de travail est un disque complet

2. **L₁ >> L₂:**
   - R_min ≈ L₁ - L₂
   - Couronne étroite

3. **L₂ >> L₁:**
   - R_min ≈ L₂ - L₁
   - Couronne large

### Exemple

Pour L₁ = 200 mm et L₂ = 150 mm:
- R_max = 350 mm
- R_min = 50 mm
- Surface accessible = π(350² - 50²) ≈ 377,000 mm²

---

## Singularités

### Définition

Une **singularité** est une configuration où le robot perd un degré de liberté, c'est-à-dire où certains mouvements cartésiens deviennent impossibles.

### Détection

Une singularité se produit quand le déterminant de la jacobienne est nul:

```
det(J) = 0
```

Pour notre robot 2DDL:

```
det(J) = L₁·L₂·sin(θ₂)
```

### Configurations Singulières

1. **θ₂ = 0** (Configuration étendue)
   - Les deux segments sont alignés
   - Impossible de se déplacer radialement

2. **θ₂ = π** (Configuration repliée)
   - Les deux segments sont opposés
   - Impossible de se déplacer radialement

### Conséquences

En singularité:
- Perte de contrôle dans certaines directions
- Vitesses articulaires infinies requises
- Instabilité numérique

### Évitement

1. **Limiter θ₂:**
   ```python
   theta2_min = -π/2  # -90°
   theta2_max = π/2   # +90°
   ```

2. **Planification de trajectoire:**
   - Éviter les zones singulières
   - Changer de configuration si nécessaire

---

## Résumé des Formules

### Cinématique Directe
```
x = L₁·cos(θ₁) + L₂·cos(θ₁ + θ₂)
y = L₁·sin(θ₁) + L₂·sin(θ₁ + θ₂)
```

### Cinématique Inverse
```
r = √(x² + y²)
cos(θ₂) = (r² - L₁² - L₂²) / (2·L₁·L₂)
θ₂ = ±arccos(cos(θ₂))
θ₁ = atan2(y, x) - atan2(L₂·sin(θ₂), L₁ + L₂·cos(θ₂))
```

### Jacobienne
```
J = [[-L₁·sin(θ₁) - L₂·sin(θ₁+θ₂),  -L₂·sin(θ₁+θ₂)]
     [ L₁·cos(θ₁) + L₂·cos(θ₁+θ₂),   L₂·cos(θ₁+θ₂)]]
```

### Espace de Travail
```
|L₁ - L₂| ≤ √(x² + y²) ≤ L₁ + L₂
```

### Singularités
```
det(J) = L₁·L₂·sin(θ₂) = 0  ⟺  θ₂ = 0 ou π
```

---

## Références

1. **Spong, M. W., Hutchinson, S., & Vidyasagar, M.** (2006). *Robot Modeling and Control*. Wiley.

2. **Craig, J. J.** (2005). *Introduction to Robotics: Mechanics and Control*. Pearson.

3. **Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G.** (2009). *Robotics: Modelling, Planning and Control*. Springer.

---

**Version:** 1.0  
**Date:** 2026-04-24  
**Auteur:** Projet Thèse - Bras Robotique 2DDL