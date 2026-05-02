# Kinematics Theory - 2-DOF Robotic Arm

## Table of Contents

1. [Introduction](#introduction)
2. [Geometric Model](#geometric-model)
3. [Forward Kinematics](#forward-kinematics)
4. [Inverse Kinematics](#inverse-kinematics)
5. [Jacobian](#jacobian)
6. [Workspace](#workspace)
7. [Singularities](#singularities)

---

## Introduction

A 2 degrees of freedom (2-DOF) robotic arm consists of two rigid segments connected by rotary joints. This document presents the mathematical theory necessary to control this type of robot.

### Notation

- **L₁**: Length of first segment (arm)
- **L₂**: Length of second segment (forearm)
- **θ₁**: Angle of first joint (base)
- **θ₂**: Angle of second joint (elbow)
- **(x, y)**: Cartesian position of end effector

---

## Geometric Model

### Robot Diagram

```
                    End Effector (x, y)
                         ●
                        /
                       /
                      / L₂
                     /
                    / θ₂
                   ●────────── Joint 2
                  /
                 /
                / L₁
               /
              / θ₁
             ●────────────────── Base (0, 0)
```

### Coordinate System

- **Origin**: Robot base (joint 1)
- **X-axis**: Horizontal, to the right
- **Y-axis**: Vertical, upward
- **Angles**: Measured counterclockwise (trigonometric)

---

## Forward Kinematics

### Problem

Given joint angles θ₁ and θ₂, calculate the Cartesian position (x, y) of the end effector.

### Solution

The end effector position is obtained by composition of transformations:

```
x = L₁·cos(θ₁) + L₂·cos(θ₁ + θ₂)
y = L₁·sin(θ₁) + L₂·sin(θ₁ + θ₂)
```

### Derivation

1. **Position of joint 2** (end of segment 1):
   ```
   x₁ = L₁·cos(θ₁)
   y₁ = L₁·sin(θ₁)
   ```

2. **Position of end effector** (end of segment 2):
   - Absolute angle of segment 2 is θ₁ + θ₂
   - Vector of segment 2 is:
     ```
     Δx = L₂·cos(θ₁ + θ₂)
     Δy = L₂·sin(θ₁ + θ₂)
     ```
   
3. **Final position**:
   ```
   x = x₁ + Δx = L₁·cos(θ₁) + L₂·cos(θ₁ + θ₂)
   y = y₁ + Δy = L₁·sin(θ₁) + L₂·sin(θ₁ + θ₂)
   ```

### Python Implementation

```python
def forward_kinematics(theta1, theta2, L1, L2):
    x = L1 * np.cos(theta1) + L2 * np.cos(theta1 + theta2)
    y = L1 * np.sin(theta1) + L2 * np.sin(theta1 + theta2)
    return x, y
```

---

## Inverse Kinematics

### Problem

Given a Cartesian position (x, y), calculate the joint angles θ₁ and θ₂ needed to reach this position.

### Geometric Solution

#### Step 1: Calculate θ₂

Using the **law of cosines**:

```
r² = x² + y²
r² = L₁² + L₂² + 2·L₁·L₂·cos(θ₂)

cos(θ₂) = (r² - L₁² - L₂²) / (2·L₁·L₂)
```

Therefore:
```
θ₂ = ±arccos((r² - L₁² - L₂²) / (2·L₁·L₂))
```

**Two possible solutions:**
- θ₂ > 0: "Elbow up" configuration
- θ₂ < 0: "Elbow down" configuration

#### Step 2: Calculate θ₁

Geometric decomposition:

```
θ₁ = atan2(y, x) - atan2(L₂·sin(θ₂), L₁ + L₂·cos(θ₂))
```

Where:
- `atan2(y, x)`: Angle of base-target line
- `atan2(L₂·sin(θ₂), L₁ + L₂·cos(θ₂))`: Correction angle

### Existence Conditions

Position (x, y) is reachable if and only if:

```
|L₁ - L₂| ≤ r ≤ L₁ + L₂
```

Where r = √(x² + y²) is the distance from base to target.

### Python Implementation

```python
def inverse_kinematics(x, y, L1, L2, elbow_up=True):
    # Distance to target
    r = np.sqrt(x**2 + y**2)
    
    # Check reachability
    if r > (L1 + L2) or r < abs(L1 - L2):
        return None  # Position unreachable
    
    # Calculate θ₂
    cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    
    if abs(cos_theta2) > 1.0:
        return None
    
    if elbow_up:
        theta2 = np.arccos(cos_theta2)
    else:
        theta2 = -np.arccos(cos_theta2)
    
    # Calculate θ₁
    k1 = L1 + L2 * np.cos(theta2)
    k2 = L2 * np.sin(theta2)
    theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)
    
    return theta1, theta2
```

### Numerical Example

**Data:**
- L₁ = 200 mm
- L₂ = 150 mm
- Target: (250, 150) mm

**Calculation:**

1. Distance: r = √(250² + 150²) = 291.55 mm
2. Verification: 50 ≤ 291.55 ≤ 350 ✓
3. cos(θ₂) = (291.55² - 200² - 150²) / (2·200·150) = 0.4518
4. θ₂ = arccos(0.4518) = 63.2° (elbow up)
5. k₁ = 200 + 150·cos(63.2°) = 267.77
6. k₂ = 150·sin(63.2°) = 133.83
7. θ₁ = atan2(150, 250) - atan2(133.83, 267.77) = 30.96° - 26.57° = 4.39°

**Verification:**
```
x = 200·cos(4.39°) + 150·cos(4.39° + 63.2°) = 250.0 ✓
y = 200·sin(4.39°) + 150·sin(4.39° + 63.2°) = 150.0 ✓
```

---

## Jacobian

### Definition

The Jacobian matrix J relates joint velocities to Cartesian velocities:

```
[ẋ]   [J₁₁  J₁₂] [θ̇₁]
[ẏ] = [J₂₁  J₂₂] [θ̇₂]
```

### Calculation

Derivation of forward kinematics:

```
ẋ = ∂x/∂θ₁·θ̇₁ + ∂x/∂θ₂·θ̇₂
ẏ = ∂y/∂θ₁·θ̇₁ + ∂y/∂θ₂·θ̇₂
```

**Result:**

```
J = [[-L₁·sin(θ₁) - L₂·sin(θ₁+θ₂),  -L₂·sin(θ₁+θ₂)]
     [ L₁·cos(θ₁) + L₂·cos(θ₁+θ₂),   L₂·cos(θ₁+θ₂)]]
```

### Usage

1. **Cartesian velocities → joint velocities:**
   ```
   [θ̇₁]       [ẋ]
   [θ̇₂] = J⁻¹ [ẏ]
   ```

2. **Cartesian forces → joint torques:**
   ```
   [τ₁]      [Fₓ]
   [τ₂] = Jᵀ [Fᵧ]
   ```

### Python Implementation

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

## Workspace

### Definition

The workspace is the set of all positions (x, y) reachable by the end effector.

### Geometric Shape

For a planar 2-DOF robot, the workspace is an **annular region**:

```
Outer radius: R_max = L₁ + L₂
Inner radius: R_min = |L₁ - L₂|
```

### Special Cases

1. **L₁ = L₂:**
   - R_min = 0
   - Workspace is a complete disk

2. **L₁ >> L₂:**
   - R_min ≈ L₁ - L₂
   - Narrow annulus

3. **L₂ >> L₁:**
   - R_min ≈ L₂ - L₁
   - Wide annulus

### Example

For L₁ = 200 mm and L₂ = 150 mm:
- R_max = 350 mm
- R_min = 50 mm
- Accessible area = π(350² - 50²) ≈ 377,000 mm²

---

## Singularities

### Definition

A **singularity** is a configuration where the robot loses a degree of freedom, meaning certain Cartesian movements become impossible.

### Detection

A singularity occurs when the Jacobian determinant is zero:

```
det(J) = 0
```

For our 2-DOF robot:

```
det(J) = L₁·L₂·sin(θ₂)
```

### Singular Configurations

1. **θ₂ = 0** (Extended configuration)
   - Both segments are aligned
   - Impossible to move radially

2. **θ₂ = π** (Folded configuration)
   - Both segments are opposite
   - Impossible to move radially

### Consequences

At singularity:
- Loss of control in certain directions
- Infinite joint velocities required
- Numerical instability

### Avoidance

1. **Limit θ₂:**
   ```python
   theta2_min = -π/2  # -90°
   theta2_max = π/2   # +90°
   ```

2. **Trajectory planning:**
   - Avoid singular zones
   - Change configuration if necessary

---

## Formula Summary

### Forward Kinematics
```
x = L₁·cos(θ₁) + L₂·cos(θ₁ + θ₂)
y = L₁·sin(θ₁) + L₂·sin(θ₁ + θ₂)
```

### Inverse Kinematics
```
r = √(x² + y²)
cos(θ₂) = (r² - L₁² - L₂²) / (2·L₁·L₂)
θ₂ = ±arccos(cos(θ₂))
θ₁ = atan2(y, x) - atan2(L₂·sin(θ₂), L₁ + L₂·cos(θ₂))
```

### Jacobian
```
J = [[-L₁·sin(θ₁) - L₂·sin(θ₁+θ₂),  -L₂·sin(θ₁+θ₂)]
     [ L₁·cos(θ₁) + L₂·cos(θ₁+θ₂),   L₂·cos(θ₁+θ₂)]]
```

### Workspace
```
|L₁ - L₂| ≤ √(x² + y²) ≤ L₁ + L₂
```

### Singularities
```
det(J) = L₁·L₂·sin(θ₂) = 0  ⟺  θ₂ = 0 or π
```

---

## References

1. **Spong, M. W., Hutchinson, S., & Vidyasagar, M.** (2006). *Robot Modeling and Control*. Wiley.

2. **Craig, J. J.** (2005). *Introduction to Robotics: Mechanics and Control*. Pearson.

3. **Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G.** (2009). *Robotics: Modelling, Planning and Control*. Springer.

---

**Version:** 1.0  
**Date:** 2026-04-24  
**Author:** Thesis Project - 2-DOF Robotic Arm