# Pick & Place Guide - 2-DOF Robotic Arm

## Introduction

This guide explains the grasping and object sorting system implemented for the 2-DOF robotic arm. The system allows the robot to grasp colored cubes and automatically sort them into drop zones corresponding to their color.

---

## 1. Grasping Theory

### 1.1 Gripper Concept

The gripper is an end effector attached to the end of the robotic arm. It has two jaws that can open and close to grasp objects.

**Gripper parameters:**
- **Length**: 40 mm from end effector
- **Open width**: 80 mm (allows grasping objects up to 80 mm)
- **Closed width**: 30 mm (secure object holding)
- **Animation speed**: 0.3 seconds to open/close

**Gripper states:**
- `OPEN`: Gripper open, ready to grasp
- `CLOSED`: Gripper closed, can hold object
- `OPENING`: Opening animation in progress
- `CLOSING`: Closing animation in progress

### 1.2 Grasp Detection

Grasping an object is possible if:
1. Gripper is open
2. Object is within reach (distance ≤ grasp tolerance)
3. Gripper then closes to hold object

**Grasp tolerance**: 5 mm by default

### 1.3 Gripper Kinematics

Gripper position is calculated by extending the end effector:

```
gripper_x = end_effector_x + gripper_length × cos(θ_arm)
gripper_y = end_effector_y + gripper_length × sin(θ_arm)
```

Where `θ_arm` is the angle of segment L2 relative to horizontal.

---

## 2. Manipulable Objects

### 2.1 Colored Cubes

Cubes are simple objects with the following properties:
- **Size**: 20 mm × 20 mm
- **Available colors**: red, blue, green, yellow
- **States**: free or grasped

**Visual representation:**
- Colored square with black border
- Thick border (3px) if grasped
- White cross at center if held by gripper

### 2.2 Drop Zones

Each color has a dedicated drop zone:

| Color  | Position (x, y) | Distance from center |
|--------|-----------------|---------------------|
| Red    | (250, 150)      | ~290 mm            |
| Blue   | (250, 50)       | ~255 mm            |
| Green  | (150, 200)      | ~250 mm            |
| Yellow | (150, 50)       | ~158 mm            |

**Zone size**: 40 mm × 40 mm (2× cube size)

### 2.3 Intelligent Position Generation

Cubes are randomly generated in the reachable workspace:

**Generation algorithm:**
```
For each cube:
    1. Generate position in polar coordinates
       - Radius: 100-280 mm (safe zone)
       - Angle: -90° to +90° (in front of robot)
    
    2. Check reachability
       - Distance between r_min+20 and r_max-20
       - r_min = |L1 - L2| = 50 mm
       - r_max = L1 + L2 = 350 mm
    
    3. Check spacing
       - Minimum distance between cubes: 2.5 × cube_size
    
    4. Avoid drop zones
       - 50 mm margin around each zone
```

---

## 3. Pick & Place Trajectories

### 3.1 Pick Trajectory

A pick trajectory consists of 3 phases:

**Phase 1: Vertical approach**
- Descend to approach height (50 mm) above cube
- Gripper open

**Phase 2: Descent**
- Descend to cube level
- Close gripper at mid-descent

**Phase 3: Ascent**
- Rise to approach height
- Cube grasped and held by gripper

**Number of points**: ~30 points per phase

### 3.2 Place Trajectory

A place trajectory consists of 3 phases:

**Phase 1: Approach**
- Move above drop zone
- Approach height: 50 mm
- Gripper closed, cube held

**Phase 2: Descent**
- Descend to drop level
- Open gripper at 75% of descent

**Phase 3: Ascent**
- Rise to approach height
- Cube deposited, gripper open

### 3.3 Complete Pick & Place Trajectory

The `compute_pick_and_place_trajectory()` method combines both trajectories:

```
Complete trajectory = [
    Pick descent points (approach → cube),
    Pick ascent points (cube → height),
    Transfer points (pick position → place position),
    Place descent points (height → zone),
    Place ascent points (zone → height)
]
```

**Optimization**: Duplicate points between phases are eliminated.

**Point format**: `[x, y, θ1, θ2]`
- `x, y`: Cartesian position (mm)
- `θ1, θ2`: Joint angles (radians)

---

## 4. Sorting Algorithm

### 4.1 Sorting Strategy

The `ColorSortingScenario` implements a simple but effective sorting strategy:

**Nearest-first algorithm:**
```
While unsorted cubes remain:
    1. Find nearest unsorted cube
    2. Plan pick & place trajectory to its zone
    3. Execute trajectory
    4. Update score
```

**Sorting criterion:**
- A cube is considered "sorted" if it's in its color zone
- Minimum distance for validation: cube center in zone

### 4.2 Scenario States

The scenario can be in one of the following states:

| State | Description |
|-------|-------------|
| `IDLE` | Waiting, ready to start |
| `INITIALIZING` | Object creation in progress |
| `RUNNING` | Sorting in execution |
| `PAUSED` | Sorting paused |
| `COMPLETED` | All cubes sorted successfully |
| `FAILED` | Failure (unreachable position) |

### 4.3 Gripper-Trajectory Synchronization

Trajectory execution is synchronized with gripper actions:

**Progress ratios:**
- **25-35%**: Gripper closing (descent toward cube)
- **35-45%**: Cube grasping (after closing)
- **70-80%**: Gripper opening (above zone)

**Continuous update:**
- Held cube position updated each frame
- Real-time synchronization with gripper position

---

## 5. Metrics and Tracking

### 5.1 Performance Statistics

The system tracks the following metrics:

- **Total cubes**: Cubes to sort
- **Sorted cubes**: Correctly placed cubes
- **Number of movements**: Executed trajectories
- **Successful placements**: Cubes in correct zone
- **Failed attempts**: Impossible trajectories
- **Elapsed time**: Total sorting duration

### 5.2 Score Calculation

```python
score = number_of_correctly_placed_cubes
progress = (score / total_cubes) × 100%
```

A cube is correctly placed if:
1. It's in a drop zone
2. Cube color matches zone color

---

## 6. Error Handling

### 6.1 Unreachable Positions

If a cube or zone is unreachable:
- Inverse kinematics returns `None`
- Scenario records failure
- Sorting continues with next cube

### 6.2 Collisions (Not implemented)

**Note**: Collision detection between cubes is not implemented in this version. Cubes can visually overlap but this doesn't affect sorting logic.

### 6.3 Joint Limits

All trajectories respect joint limits:
- θ1: -180° to +180°
- θ2: -150° to +150°

---

## 7. Practical Usage

### 7.1 Simulator Controls

| Key | Action |
|-----|--------|
| **P** | Start/stop automatic sorting |
| **O** | Open/close gripper manually |
| **C** | Create new random cubes |
| **S** | Pause/resume scenario |
| **R** | Reset robot |

### 7.2 Example Session

```python
# Initialize scenario with 4 cubes
scenario.initialize(num_cubes=4)

# Start automatic sorting
scenario.start()

# System automatically executes:
# 1. Finds nearest cube
# 2. Plans pick & place trajectory
# 3. Executes movement
# 4. Repeats until all cubes are sorted
```

### 7.3 Integration in a Project

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

# Create scenario
scenario = ColorSortingScenario(config, kinematics, gripper, object_manager)

# Initialize and start
scenario.initialize(num_cubes=4, colors=['red', 'blue', 'green', 'yellow'])
scenario.start()

# Execute step
current_pos = kinematics.forward_kinematics(theta1, theta2)
result = scenario.execute_sort_step(current_pos)

if result:
    trajectory, description = result
    # Execute trajectory...
```

---

## 8. Future Improvements

### 8.1 Possible Optimizations

- **TSP algorithm**: Optimize sorting order to minimize total distance
- **Spline interpolation**: Smoother trajectories
- **Collision detection**: Avoid overlaps between cubes
- **Realistic physics**: Gravity, friction, bounces

### 8.2 Extensions

- **Varied object shapes**: Cylinders, spheres
- **Multi-criteria sorting**: Color + size + shape
- **Dynamic drop zones**: Changing positions
- **Collaborative mode**: Multiple robotic arms

---

## Conclusion

The implemented pick & place system demonstrates the capabilities of a 2-DOF robotic arm for object manipulation tasks. The modular architecture allows easy extension and integration into more complex projects.

**Strengths:**
- ✅ Trajectories validated by inverse kinematics
- ✅ Precise gripper-movement synchronization
- ✅ Intelligent generation of reachable positions
- ✅ Robust error handling
- ✅ Complete performance metrics

---

*Document generated by IBM Bob - May 2, 2026*