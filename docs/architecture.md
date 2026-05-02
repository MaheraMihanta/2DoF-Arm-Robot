# Project Architecture - 2-DOF Robotic Arm

## Overview

This document describes the software architecture of the 2-DOF robotic arm control system.

## Module Structure

```
SIMULATION/
│
├── phase1_simulation/          # Phase 1: Modeling and Simulation
│   ├── config.py              # Robot configuration
│   ├── kinematics.py          # Direct and inverse kinematics
│   └── simulator.py           # Visual simulator (Pygame)
│
├── phase2_hardware/           # Phase 2: Hardware Control
│   ├── grbl_interface.py      # Serial communication with GRBL
│   ├── motor_control.py       # Motor control
│   └── a4988_config.py        # A4988 driver configuration
│
├── phase3_integration/        # Phase 3: Integration
│   ├── robot_controller.py    # Main controller
│   └── gui.py                 # Graphical interface (Tkinter)
│
├── tests/                     # Unit tests
│   └── test_kinematics.py     # Kinematics tests
│
├── docs/                      # Documentation
│   ├── guide_utilisation.md   # User guide
│   ├── theorie_cinematique.md # Mathematical theory
│   └── architecture.md        # This document
│
├── README.md                  # Main documentation
├── QUICKSTART.md             # Quick start
└── requirements.txt          # Python dependencies
```

## Class Diagram

### Phase 1: Simulation

```
┌─────────────────────────────────────────────────────────────┐
│                        RobotConfig                          │
├─────────────────────────────────────────────────────────────┤
│ + L1: float                    # Segment 1 length            │
│ + L2: float                    # Segment 2 length            │
│ + steps_per_revolution: int    # Steps per revolution        │
│ + microsteps: int              # Microstepping              │
│ + theta1_min/max: float        # Angular limits             │
│ + theta2_min/max: float                                     │
├─────────────────────────────────────────────────────────────┤
│ + is_angle_valid()             # Check limits               │
│ + angles_to_steps()            # Convert angles → steps     │
│ + steps_to_angles()            # Convert steps → angles     │
│ + get_workspace_limits()       # Workspace limits           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ uses
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
│ + jacobian()                   # Jacobian matrix            │
│ + get_joint_positions()        # Joint positions            │
│ + is_position_reachable()      # Check reachability         │
│ + compute_trajectory()         # Plan trajectory            │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ uses
                            │
┌─────────────────────────────────────────────────────────────┐
│                      RobotSimulator                         │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - kinematics: Kinematics                                    │
│ - screen: pygame.Surface                                    │
│ - theta1, theta2: float        # Current state              │
├─────────────────────────────────────────────────────────────┤
│ + draw_robot()                 # Draw arm                   │
│ + draw_workspace()             # Draw workspace             │
│ + handle_input()               # Handle user input          │
│ + run()                        # Main loop                  │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Hardware

```
┌─────────────────────────────────────────────────────────────┐
│                      GRBLInterface                          │
├─────────────────────────────────────────────────────────────┤
│ - port: str                    # Serial port                │
│ - baudrate: int                # Communication speed        │
│ - serial_connection: Serial    # Serial connection          │
│ - is_connected: bool                                        │
├─────────────────────────────────────────────────────────────┤
│ + connect()                    # Establish connection       │
│ + disconnect()                 # Close connection           │
│ + send_command()               # Send G-code                │
│ + get_status()                 # Read GRBL status           │
│ + home()                       # Homing                     │
│ + move_absolute()              # Absolute movement          │
│ + jog()                        # Manual movement            │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ uses
                            │
┌─────────────────────────────────────────────────────────────┐
│                      MotorController                        │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - grbl: GRBLInterface                                       │
│ - current_theta1, theta2: float                             │
│ - current_steps_1, steps_2: int                             │
├─────────────────────────────────────────────────────────────┤
│ + move_to_angles()             # Move to angles             │
│ + move_incremental()           # Incremental movement       │
│ + home_motors()                # Motor homing               │
│ + execute_trajectory()         # Execute trajectory         │
│ + angles_to_gcode_position()   # Convert angles → G-code    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       A4988Config                           │
├─────────────────────────────────────────────────────────────┤
│ + microstep_modes: dict        # µstep configurations       │
│ + max_current: float           # Max current                │
│ + pin_mapping: dict            # Pin mapping                │
├─────────────────────────────────────────────────────────────┤
│ + get_microstep_pins()         # MS1/MS2/MS3 pin config     │
│ + calculate_current_limit_vref() # Calculate Vref           │
│ + get_wiring_diagram()         # Wiring diagram             │
│ + get_grbl_settings()          # GRBL parameters            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: Integration

```
┌─────────────────────────────────────────────────────────────┐
│                      RobotController                        │
├─────────────────────────────────────────────────────────────┤
│ - config: RobotConfig                                       │
│ - kinematics: Kinematics                                    │
│ - grbl: GRBLInterface          # Optional                   │
│ - motor_controller: MotorController # Optional              │
│ - mode: ControlMode            # simulation/hardware/hybrid │
├─────────────────────────────────────────────────────────────┤
│ + move_to_angles()             # Move to angles             │
│ + move_to_position()           # Move to position           │
│ + execute_trajectory()         # Execute trajectory         │
│ + plan_linear_trajectory()     # Plan trajectory            │
│ + home()                       # Return to origin           │
│ + get_current_position()       # Current position           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ uses
                            │
┌─────────────────────────────────────────────────────────────┐
│                         RobotGUI                            │
├─────────────────────────────────────────────────────────────┤
│ - root: tk.Tk                  # Main window                │
│ - robot: RobotController       # Controller                 │
│ - config: RobotConfig                                       │
├─────────────────────────────────────────────────────────────┤
│ + create_control_tab()         # Control tab                │
│ + create_trajectory_tab()      # Trajectory tab             │
│ + create_config_tab()          # Configuration tab          │
│ + connect()                    # Connect robot              │
│ + move_to_angles()             # Move to angles             │
│ + move_to_position()           # Move to position           │
│ + plan_linear_trajectory()     # Plan trajectory            │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Simulation Mode

```
User
    │
    ▼
Interface (GUI/Simulator)
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

### 2. Hardware Mode

```
User
    │
    ▼
Interface (GUI/CLI)
    │
    ▼
RobotController (mode=HARDWARE)
    │
    ├─→ Kinematics → Angle calculation
    │
    └─→ MotorController
            │
            ▼
        GRBLInterface
            │
            ▼
        Serial Port (USB)
            │
            ▼
        Arduino + GRBL
            │
            ▼
        A4988 Drivers
            │
            ▼
        Stepper Motors
            │
            ▼
        Robotic Arm
```

### 3. Hybrid Mode

```
User
    │
    ▼
Interface
    │
    ▼
RobotController (mode=HYBRID)
    │
    ├─→ Kinematics (simulation)
    │       │
    │       └─→ Visualization
    │
    └─→ MotorController (hardware)
            │
            └─→ Physical control
```

## Communication Protocols

### GRBL Communication

**Command format:**
```
G-code → Arduino (GRBL) → Motors

Examples:
- G90 G1 X100 Y50 F1000  # Absolute movement
- $H                      # Homing
- ?                       # Status
- $X                      # Unlock
```

**Response format:**
```
ok                        # Command accepted
error:N                   # Error (N = code)
<Idle|MPos:x,y,z|...>    # Status
```

### Axis Mapping

```
2-DOF Robot         GRBL
─────────────────────────
θ1 (angle 1)    →   X (mm)
θ2 (angle 2)    →   Y (mm)
```

**Conversion:**
```python
# Angles → G-code position
steps1, steps2 = config.angles_to_steps(theta1, theta2)
x_gcode = steps1 * 0.01  # mm
y_gcode = steps2 * 0.01  # mm
```

## Error Handling

### Exception Hierarchy

```
Exception
│
├─ ValueError
│  ├─ Position out of bounds
│  └─ Invalid angles
│
├─ ConnectionError
│  ├─ Serial port not found
│  └─ GRBL not connected
│
└─ RuntimeError
   ├─ GRBL command failed
   └─ Communication timeout
```

### Recovery Strategies

1. **Unreachable position:**
   - Check with `is_position_reachable()`
   - Propose nearest position

2. **GRBL error:**
   - Read error code
   - Attempt unlock ($X)
   - Soft reset if necessary

3. **Communication loss:**
   - Detect timeout
   - Attempt reconnection
   - Degraded mode (simulation)

## Extensibility

### Adding a New Control Mode

```python
# 1. Define mode
class ControlMode(Enum):
    SIMULATION = "simulation"
    HARDWARE = "hardware"
    HYBRID = "hybrid"
    NEW_MODE = "new_mode"  # New

# 2. Implement in RobotController
def move_to_angles(self, theta1, theta2):
    if self.mode == ControlMode.NEW_MODE:
        # Specific logic
        pass
```

### Adding a New Trajectory Type

```python
# In Kinematics
def compute_circular_trajectory(self, center, radius, num_points):
    """Circular trajectory"""
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

### Adding a New Driver

```python
# Create new file: phase2_hardware/drv8825_config.py
class DRV8825Config:
    """Configuration for DRV8825 driver"""
    def __init__(self):
        self.microstep_modes = {
            1: (0, 0, 0),
            2: (1, 0, 0),
            4: (0, 1, 0),
            8: (1, 1, 0),
            16: (0, 0, 1),
            32: (1, 0, 1)  # DRV8825 supports 1/32
        }
```

## Performance

### Implemented Optimizations

1. **Vector calculations:** Using NumPy
2. **Position cache:** Limited history
3. **Asynchronous communication:** Threads for GUI
4. **Early validation:** Verification before sending

### Typical Metrics

- **Inverse kinematics calculation:** < 1 ms
- **GRBL command sending:** 10-50 ms
- **Simulation frequency:** 60 FPS
- **Total latency:** < 100 ms

## Security

### Security Mechanisms

1. **Software limits:**
   - Angle verification before movement
   - Workspace verification

2. **Emergency stop:**
   - GRBL soft reset (Ctrl-X)
   - Accessible from all interfaces

3. **Input validation:**
   - Type checking
   - Range checking
   - Sanitization

4. **Degraded mode:**
   - Automatic switch to simulation
   - Detailed logs

## Tests

### Test Coverage

```
tests/test_kinematics.py
├─ TestKinematics
│  ├─ Direct kinematics (5 tests)
│  ├─ Inverse kinematics (8 tests)
│  ├─ Jacobian (2 tests)
│  ├─ Workspace (3 tests)
│  └─ Trajectories (2 tests)
│
└─ TestRobotConfig
   ├─ Configuration (4 tests)
   └─ Conversions (3 tests)

Total: 27 unit tests
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=phase1_simulation --cov-report=html

# Specific tests
pytest tests/test_kinematics.py::TestKinematics::test_forward_kinematics_zero_angles
```

## Maintenance

### Logs

All modules use `print()` for logs. For production application, replace with `logging`:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning")
logger.error("Error")
```

### Versioning

- **Current version:** 1.0
- **Format:** MAJOR.MINOR.PATCH
- **Changelog:** To be created in `CHANGELOG.md`

---

**Version:** 1.0  
**Date:** 2026-04-24  
**Author:** Thesis Project - 2-DOF Robotic Arm