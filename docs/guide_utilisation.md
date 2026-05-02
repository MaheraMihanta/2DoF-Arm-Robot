# User Guide - 2-DOF Robotic Arm

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Phase 1: Simulation](#phase-1-simulation)
4. [Phase 2: Hardware Control](#phase-2-hardware-control)
5. [Phase 3: Complete System](#phase-3-complete-system)
6. [Troubleshooting](#troubleshooting)

---

## Introduction

This project implements a position control system for a 2 degrees of freedom (2-DOF) robotic arm using:
- **Inverse kinematics** to calculate joint angles
- **Stepper motors** with A4988 drivers
- **GRBL** for motor control
- **Python** for implementation

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│              (Tkinter GUI / Console / Simulator)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Robot Controller                           │
│              (robot_controller.py)                           │
└──────────────┬────────────────────────────┬──────────────────┘
               │                            │
┌──────────────▼──────────────┐  ┌─────────▼──────────────────┐
│   Inverse Kinematics        │  │   Motor Control            │
│   (kinematics.py)           │  │   (motor_control.py)       │
└─────────────────────────────┘  └────────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   GRBL Interface          │
                                  │   (grbl_interface.py)     │
                                  └───────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   Arduino + GRBL          │
                                  └───────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   A4988 Drivers           │
                                  └───────────┬───────────────┘
                                              │
                                  ┌───────────▼───────────────┐
                                  │   Stepper Motors          │
                                  └───────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Arduino with GRBL (for hardware control)

### Installing Dependencies

```bash
# Clone or download the project
cd SIMULATION

# Install dependencies
pip install -r requirements.txt
```

### Installation Verification

```bash
# Test configuration
python phase1_simulation/config.py

# Test kinematics
python phase1_simulation/kinematics.py
```

---

## Phase 1: Simulation

### 1.1 Test Kinematics

```bash
cd phase1_simulation
python kinematics.py
```

**Expected output:**
```
=== Kinematics Test ===

1. Forward Kinematics:
   θ1=45.0°, θ2=30.0°
   → Position: x=318.20mm, y=183.71mm

2. Inverse Kinematics:
   Target position: x=250.00mm, y=150.00mm
   → θ1=31.0°, θ2=28.1°
   Verification: x=250.00mm, y=150.00mm
   Error: 0.0000mm
...
```

### 1.2 Launch Visual Simulator

```bash
python simulator.py
```

**Simulator commands:**
- **Arrow keys**: Angle control (θ1 and θ2)
- **Left click**: Set target position
- **M**: Change mode (angles/position)
- **E**: Change elbow configuration
- **R**: Reset
- **G**: Show/hide grid
- **W**: Show/hide workspace
- **ESC**: Quit

### 1.3 Run Tests

```bash
cd ../tests
pytest test_kinematics.py -v
```

---

## Phase 2: Hardware Control

### 2.1 Hardware Preparation

#### Arduino + A4988 Wiring

Consult detailed diagram:
```bash
python phase2_hardware/a4988_config.py
```

**Important points:**
1. ⚠️ **Set Vref BEFORE connecting motors**
2. Add capacitors (100µF + 0.1µF)
3. Check motor polarity
4. Provide heat sink

#### GRBL Configuration

1. Flash GRBL on Arduino:
   - Download GRBL from https://github.com/gnea/grbl
   - Use Arduino IDE to flash

2. Configure parameters:
```bash
python phase2_hardware/motor_control.py
# Choose option 6: Configure GRBL
```

### 2.2 GRBL Communication Test

```bash
cd phase2_hardware
python grbl_interface.py
```

**Test menu:**
```
1. Status          - Check GRBL state
2. Homing          - Return to origin
3. Unlock          - Unlock after alarm
4. Set origin      - Set current position as (0,0)
5-7. Jog           - Test movements
8. Parameters      - Display GRBL configuration
```

### 2.3 Motor Testing

```bash
python motor_control.py
```

**Recommended test sequence:**
1. Homing (option 1)
2. Set origin (option 2)
3. Move to angles (option 3) - Test with small angles
4. Check position (option 5)

---

## Phase 3: Complete System

### 3.1 Command Line Interface

```bash
cd phase3_integration
python robot_controller.py
```

**Available modes:**
- **Simulation**: Test without hardware
- **Hardware**: Direct robot control
- **Hybrid**: Simulation + hardware control

### 3.2 Graphical Interface

```bash
python gui.py
```

**Features:**
- Control by angles or position
- Trajectory planning
- Predefined trajectories (square, circle)
- Log console
- Real-time configuration

### 3.3 Usage Examples

#### Example 1: Simple Movement

```python
from config import config
from robot_controller import RobotController, ControlMode
import numpy as np

# Simulation mode
with RobotController(config, ControlMode.SIMULATION) as robot:
    # Move to angles
    robot.move_to_angles(np.radians(45), np.radians(30))
    
    # Move to position
    robot.move_to_position(250, 150)
    
    # Get current position
    x, y = robot.get_current_position()
    print(f"Position: ({x:.1f}, {y:.1f})")
```

#### Example 2: Linear Trajectory

```python
# Plan trajectory
trajectory = robot.plan_linear_trajectory(300, 200, num_points=50)

if trajectory is not None:
    # Execute trajectory
    robot.execute_trajectory(trajectory, feed_rate=1000)
```

#### Example 3: Circular Trajectory

```python
import numpy as np

# Circle center and radius
center_x, center_y = 225, 125
radius = 30
num_points = 36

# Generate points
for i in range(num_points + 1):
    angle = 2 * np.pi * i / num_points
    x = center_x + radius * np.cos(angle)
    y = center_y + radius * np.sin(angle)
    robot.move_to_position(x, y)
```

---

## Troubleshooting

### Problem: Cannot connect to GRBL

**Solutions:**
1. Check serial port:
   ```python
   import serial.tools.list_ports
   ports = serial.tools.list_ports.comports()
   for port in ports:
       print(port.device)
   ```

2. Verify GRBL is flashed on Arduino
3. Close other programs using serial port
4. Try another USB cable

### Problem: Position unreachable

**Possible causes:**
- Position outside workspace
- Angles out of limits
- Incorrect L1, L2 length configuration

**Verification:**
```python
from kinematics import Kinematics
from config import config

kin = Kinematics(config)
print(f"Position reachable: {kin.is_position_reachable(x, y)}")
```

### Problem: Motors not moving

**Checks:**
1. Vref correctly set
2. Motor power supply connected
3. ENABLE pins at LOW
4. Correct wiring (STEP, DIR)
5. Correct GRBL parameters ($100, $101)

### Problem: Erratic movements

**Solutions:**
1. Reduce speed (feed_rate)
2. Increase acceleration in GRBL ($120, $121)
3. Check capacitors
4. Check motor phase wiring

### Problem: Precision error

**Causes:**
- Motor step quantization
- Mechanical backlash
- Segment flexibility

**Improvement:**
1. Increase microstepping (1/16 or 1/32)
2. Add gear reducers
3. Calibrate steps/mm parameters

---

## Important Parameters

### Robot Configuration (config.py)

```python
L1 = 200.0  # Segment 1 length (mm)
L2 = 150.0  # Segment 2 length (mm)
steps_per_revolution = 200  # Steps per revolution
microsteps = 16  # Microstepping
```

### Critical GRBL Parameters

```
$100 = 100.0  # X steps/mm (to calibrate)
$101 = 100.0  # Y steps/mm (to calibrate)
$110 = 2000.0 # X max rate (mm/min)
$111 = 2000.0 # Y max rate (mm/min)
$120 = 500.0  # X acceleration (mm/s²)
$121 = 500.0  # Y acceleration (mm/s²)
```

### Calibration

To calibrate steps/mm:
1. Mark starting position
2. Command 100mm movement
3. Measure actual movement
4. Adjust: `$100 = $100 * (100 / actual_measurement)`

---

## Additional Resources

- **GRBL Documentation**: https://github.com/gnea/grbl/wiki
- **A4988 Datasheet**: https://www.pololu.com/product/1182
- **Kinematics Theory**: See `docs/theorie_cinematique.md`

---

## Support

For any questions or problems:
1. Consult Troubleshooting section
2. Check console logs
3. Test in simulation mode first
4. Verify hardware wiring

---

**Version:** 1.0  
**Date:** 2026-04-24  
**Author:** Thesis Project - 2-DOF Robotic Arm