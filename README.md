# 2-DOF Position-Controlled Robotic Arm with GRBL

Project for controlling a 2 degrees of freedom (2-DOF) robotic arm using stepper motors driven by GRBL.

## 🎯 Objective

Implement an open-loop position control system for a 2-DOF robotic arm, using inverse kinematics to determine the angle setpoints θ1 and θ2.

## 📁 Project Structure

```
SIMULATION/
├── phase1_simulation/     # Modeling and simulation
│   ├── kinematics.py      # Direct and inverse kinematics
│   ├── simulator.py       # Visual simulator
│   └── config.py          # Arm configuration
├── phase2_hardware/       # Hardware control
│   ├── grbl_interface.py  # GRBL interface
│   ├── motor_control.py   # Motor control
│   └── a4988_config.py    # A4988 configuration
├── phase3_integration/    # Complete integration
│   ├── robot_controller.py # Main controller
│   └── gui.py             # Graphical interface
├── tests/                 # Unit tests
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## 🚀 Action Plan

### Phase 1: Modeling and Simulation
- ✅ Create project structure
- ⏳ Implement kinematic model (direct and inverse)
- ⏳ Create visual simulator for 2-DOF arm
- ⏳ Validate inverse kinematics with tests

### Phase 2: Hardware Control
- ⏳ Create communication interface with GRBL
- ⏳ Implement angles → motor commands conversion
- ⏳ Test GRBL communication

### Phase 3: Integration and Testing
- ⏳ Integrate kinematics + GRBL control
- ⏳ Create control interface
- ⏳ Test on real hardware
- ⏳ Final documentation

## 🔧 Required Hardware

- Arduino with GRBL
- 2x Stepper motors
- 2x A4988 drivers
- Appropriate power supply
- Connection cables

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Simulation (Phase 1)
```bash
python phase1_simulation/simulator.py
```

### Hardware Control (Phase 2)
```bash
python phase2_hardware/grbl_interface.py
```

### Complete System (Phase 3)
```bash
python phase3_integration/robot_controller.py
```

## 📚 Documentation

Consult the `docs/` folder for detailed documentation:
- Kinematics theory
- GRBL configuration
- User guide

## 🤝 Contribution

This project is developed as part of a thesis.

## 📄 License

To be defined