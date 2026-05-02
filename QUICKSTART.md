# 🚀 Quick Start - 2-DOF Robotic Arm

## Express Installation (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test configuration
python phase1_simulation/config.py

# 3. Launch simulator
python phase1_simulation/simulator.py
```

## 🎮 First Steps with the Simulator

### Essential Commands

| Key | Action |
|--------|--------|
| **←→** | Control θ1 (joint 1) |
| **↑↓** | Control θ2 (joint 2) |
| **Left click** | Set target position |
| **M** | Change mode (angles/position) |
| **R** | Reset |
| **ESC** | Quit |

### Exercise 1: Manual Control

1. Launch the simulator
2. Use arrow keys to move the arm
3. Observe angles and position in the info panel

### Exercise 2: Position Control

1. Press **M** to switch to position mode
2. Click on a point in the workspace (blue area)
3. The arm automatically moves to that point

## 🔧 Hardware Testing (10 minutes)

### Prerequisites
- Arduino with GRBL flashed
- 2× Stepper motors
- 2× A4988 drivers
- 12-24V power supply

### Quick Steps

```bash
# 1. Check connection
python phase2_hardware/grbl_interface.py
# Enter your serial port (e.g., COM3)

# 2. Test motors
python phase2_hardware/motor_control.py
# Menu: 1 (Homing) then 3 (Move to angles)

# 3. Launch complete interface
python phase3_integration/gui.py
```

## 📊 Graphical Interface

### Control Tab

1. **Connection**
   - Mode: Choose "simulation" or "hardware"
   - Port: Enter serial port (e.g., COM3)
   - Click "Connect"

2. **Angle Control**
   - Adjust θ1 and θ2 with sliders
   - Click "Move"

3. **Position Control**
   - Enter X and Y in mm
   - Check "Elbow up" if desired
   - Click "Move"

### Trajectories Tab

1. **Linear Trajectory**
   - Enter target position (X, Y)
   - Number of points: 50 (default)
   - Click "Plan" then "Execute"

2. **Predefined Trajectories**
   - Square, Circle, or Zigzag
   - Click corresponding button

## 🧪 Unit Tests

```bash
# Run all tests
cd tests
pytest test_kinematics.py -v

# Specific test
pytest test_kinematics.py::TestKinematics::test_forward_kinematics_zero_angles -v
```

## 📝 Code Examples

### Example 1: Simple Simulation

```python
from phase1_simulation.config import config
from phase1_simulation.kinematics import Kinematics
import numpy as np

# Create kinematic object
kin = Kinematics(config)

# Forward kinematics
theta1, theta2 = np.radians(45), np.radians(30)
x, y = kin.forward_kinematics(theta1, theta2)
print(f"Position: ({x:.1f}, {y:.1f}) mm")

# Inverse kinematics
result = kin.inverse_kinematics(250, 150)
if result:
    theta1, theta2 = result
    print(f"Angles: θ1={np.degrees(theta1):.1f}°, θ2={np.degrees(theta2):.1f}°")
```

### Example 2: Hardware Control

```python
import sys
sys.path.insert(0, 'phase1_simulation')
sys.path.insert(0, 'phase2_hardware')

from config import config
from grbl_interface import GRBLInterface
from motor_control import MotorController
import numpy as np

# GRBL connection
with GRBLInterface(port='COM3') as grbl:
    # Create controller
    controller = MotorController(config, grbl)
    
    # Homing
    controller.home_motors()
    
    # Move to angles
    controller.move_to_angles(np.radians(30), np.radians(20))
```

### Example 3: Complete System

```python
import sys
sys.path.insert(0, 'phase1_simulation')
sys.path.insert(0, 'phase2_hardware')
sys.path.insert(0, 'phase3_integration')

from config import config
from robot_controller import RobotController, ControlMode

# Simulation mode
with RobotController(config, ControlMode.SIMULATION) as robot:
    # Move to position
    robot.move_to_position(250, 150)
    
    # Plan trajectory
    trajectory = robot.plan_linear_trajectory(300, 200, num_points=50)
    
    # Execute trajectory
    if trajectory is not None:
        robot.execute_trajectory(trajectory)
```

## 🎯 Typical Use Cases

### 1. Kinematics Validation

```bash
# Test kinematics
python phase1_simulation/kinematics.py

# Run tests
pytest tests/test_kinematics.py -v
```

### 2. Hardware Calibration

```bash
# Display A4988 configuration
python phase2_hardware/a4988_config.py

# Configure GRBL
python phase2_hardware/motor_control.py
# Menu: 6 (Configure GRBL)
```

### 3. Interactive Demonstration

```bash
# Complete interface
python phase3_integration/robot_controller.py

# Or graphical interface
python phase3_integration/gui.py
```

## ⚠️ Common Issues

### "Import numpy could not be resolved"

```bash
pip install numpy matplotlib pygame pyserial pytest
```

### "Serial port not found"

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
# Look for /dev/ttyUSB0 or /dev/ttyACM0
```

### "Position unreachable"

Verify that the position is within the workspace:
- Max radius: L1 + L2 = 350 mm
- Min radius: |L1 - L2| = 50 mm

### "Motors not moving"

1. Check Vref on A4988 drivers
2. Check motor power supply
3. Check GRBL parameters ($100, $101)

## 📚 Complete Documentation

- **User guide**: `docs/guide_utilisation.md`
- **Kinematics theory**: `docs/theorie_cinematique.md`
- **Main README**: `README.md`

## 🆘 Support

1. Consult documentation in `docs/`
2. Check examples in each module
3. Test in simulation mode first
4. Verify hardware wiring

## 🎓 Next Steps

1. ✅ Master the simulator
2. ✅ Understand inverse kinematics
3. ✅ Test with hardware
4. ✅ Create your own trajectories
5. ✅ Optimize parameters

---

**Happy developing! 🤖**