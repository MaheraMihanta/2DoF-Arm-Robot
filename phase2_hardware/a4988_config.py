"""
Configuration spécifique pour les drivers A4988
Documentation des paramètres et des connexions
"""


class A4988Config:
    """Configuration pour les drivers de moteurs pas à pas A4988"""
    
    def __init__(self):
        # Paramètres du driver A4988
        self.driver_name = "A4988"
        
        # Modes de microstepping disponibles
        # MS1, MS2, MS3 pins configuration
        self.microstep_modes = {
            1: (0, 0, 0),    # Full step
            2: (1, 0, 0),    # Half step
            4: (0, 1, 0),    # Quarter step
            8: (1, 1, 0),    # Eighth step
            16: (1, 1, 1),   # Sixteenth step
        }
        
        # Configuration actuelle
        self.microsteps = 16  # Mode par défaut: 1/16 step
        
        # Caractéristiques électriques
        self.max_current = 2.0  # Ampères (limité par le driver)
        self.logic_voltage = 5.0  # Volts (logique)
        self.motor_voltage_min = 8.0  # Volts
        self.motor_voltage_max = 35.0  # Volts
        
        # Timing (microsecondes)
        self.min_step_pulse_width = 1  # µs
        self.min_direction_setup_time = 200  # µs
        
        # Pins Arduino (exemple pour GRBL standard)
        self.pin_mapping = {
            'motor1': {
                'step': 2,      # Pin STEP moteur 1 (X axis)
                'direction': 5, # Pin DIR moteur 1
                'enable': 8,    # Pin ENABLE (commun ou séparé)
            },
            'motor2': {
                'step': 3,      # Pin STEP moteur 2 (Y axis)
                'direction': 6, # Pin DIR moteur 2
                'enable': 8,    # Pin ENABLE (commun)
            }
        }
        
        # Configuration de protection
        self.enable_thermal_protection = True
        self.enable_overcurrent_protection = True
        
    def get_microstep_pins(self, microsteps: int) -> tuple:
        """
        Retourne la configuration des pins MS1, MS2, MS3 pour le microstepping
        
        Args:
            microsteps: Nombre de microsteps (1, 2, 4, 8, ou 16)
            
        Returns:
            tuple: (MS1, MS2, MS3) configuration (0 ou 1)
        """
        if microsteps not in self.microstep_modes:
            raise ValueError(f"Microstepping {microsteps} non supporté. Valeurs: {list(self.microstep_modes.keys())}")
        
        return self.microstep_modes[microsteps]
    
    def calculate_current_limit_vref(self, desired_current: float) -> float:
        """
        Calcule la tension Vref nécessaire pour limiter le courant
        
        Formule A4988: I_max = Vref / (8 * Rs)
        Avec Rs = 0.05Ω (résistance de shunt typique)
        
        Args:
            desired_current: Courant désiré en Ampères
            
        Returns:
            float: Tension Vref à régler (Volts)
        """
        Rs = 0.05  # Ohms (résistance de shunt typique pour A4988)
        Vref = desired_current * 8 * Rs
        
        if Vref > 2.5:
            print(f"Attention: Vref={Vref:.2f}V dépasse la limite recommandée de 2.5V")
        
        return Vref
    
    def get_wiring_diagram(self) -> str:
        """
        Retourne un schéma de câblage en texte
        
        Returns:
            str: Diagramme de connexion
        """
        diagram = """
╔════════════════════════════════════════════════════════════════╗
║           SCHÉMA DE CÂBLAGE A4988 + ARDUINO + GRBL            ║
╚════════════════════════════════════════════════════════════════╝

MOTEUR 1 (Articulation 1 - θ1):
┌─────────────┐
│   A4988 #1  │
│             │
│  VMOT  ─────┼──── Alimentation moteur (12-24V)
│  GND   ─────┼──── Ground commun
│             │
│  1A    ─────┼──── Moteur Phase A (Coil 1)
│  1B    ─────┼──── Moteur Phase A (Coil 1)
│  2A    ─────┼──── Moteur Phase B (Coil 2)
│  2B    ─────┼──── Moteur Phase B (Coil 2)
│             │
│  STEP  ─────┼──── Arduino Pin 2 (X_STEP)
│  DIR   ─────┼──── Arduino Pin 5 (X_DIR)
│  ENABLE ────┼──── Arduino Pin 8 (ENABLE)
│             │
│  MS1   ─────┼──── VCC (pour 1/16 step)
│  MS2   ─────┼──── VCC (pour 1/16 step)
│  MS3   ─────┼──── VCC (pour 1/16 step)
│             │
│  RESET ─────┼──── VCC (ou SLEEP)
│  SLEEP ─────┼──── VCC (ou RESET)
│             │
│  VDD   ─────┼──── +5V Arduino
│  GND   ─────┼──── Ground
└─────────────┘

MOTEUR 2 (Articulation 2 - θ2):
┌─────────────┐
│   A4988 #2  │
│             │
│  VMOT  ─────┼──── Alimentation moteur (12-24V)
│  GND   ─────┼──── Ground commun
│             │
│  1A    ─────┼──── Moteur Phase A (Coil 1)
│  1B    ─────┼──── Moteur Phase A (Coil 1)
│  2A    ─────┼──── Moteur Phase B (Coil 2)
│  2B    ─────┼──── Moteur Phase B (Coil 2)
│             │
│  STEP  ─────┼──── Arduino Pin 3 (Y_STEP)
│  DIR   ─────┼──── Arduino Pin 6 (Y_DIR)
│  ENABLE ────┼──── Arduino Pin 8 (ENABLE - partagé)
│             │
│  MS1   ─────┼──── VCC (pour 1/16 step)
│  MS2   ─────┼──── VCC (pour 1/16 step)
│  MS3   ─────┼──── VCC (pour 1/16 step)
│             │
│  RESET ─────┼──── VCC (ou SLEEP)
│  SLEEP ─────┼──── VCC (ou RESET)
│             │
│  VDD   ─────┼──── +5V Arduino
│  GND   ─────┼──── Ground
└─────────────┘

ALIMENTATION:
- Moteurs: 12-24V DC, 2-3A minimum
- Arduino: USB ou 7-12V DC
- Ground commun entre Arduino et alimentation moteurs

CONDENSATEURS (IMPORTANT):
- 100µF électrolytique entre VMOT et GND (près de chaque driver)
- 0.1µF céramique entre VDD et GND (près de chaque driver)

RÉGLAGE Vref (Limitation de courant):
1. Débrancher les moteurs
2. Alimenter le driver
3. Mesurer la tension entre le potentiomètre et GND
4. Ajuster pour obtenir: Vref = I_max * 8 * 0.05
   Exemple: Pour 1A → Vref = 0.4V
            Pour 1.5A → Vref = 0.6V

NOTES:
- Toujours régler Vref AVANT de connecter les moteurs
- Ne jamais débrancher/brancher les moteurs sous tension
- Prévoir un dissipateur thermique sur les A4988
- Vérifier la polarité des moteurs (phases A et B)
"""
        return diagram
    
    def get_grbl_settings(self) -> dict:
        """
        Retourne les paramètres GRBL recommandés pour A4988
        
        Returns:
            dict: Paramètres GRBL
        """
        # Calcul des pas/mm basé sur la configuration
        # Pour un système de rotation, on utilise une conversion arbitraire
        steps_per_mm = 100.0  # À ajuster selon votre mécanique
        
        settings = {
            '$0': 10,      # Step pulse time (µs)
            '$1': 25,      # Step idle delay (ms)
            '$2': 0,       # Step pulse invert (mask)
            '$3': 0,       # Step direction invert (mask)
            '$4': 0,       # Invert step enable pin
            '$5': 0,       # Invert limit pins
            '$10': 1,      # Status report (WPos enabled)
            '$11': 0.010,  # Junction deviation (mm)
            '$12': 0.002,  # Arc tolerance (mm)
            '$20': 0,      # Soft limits (disabled)
            '$21': 0,      # Hard limits (disabled)
            '$22': 0,      # Homing cycle (disabled)
            '$23': 0,      # Homing direction invert
            '$24': 25.0,   # Homing feed rate (mm/min)
            '$25': 500.0,  # Homing seek rate (mm/min)
            '$26': 250,    # Homing debounce (ms)
            '$27': 1.0,    # Homing pull-off (mm)
            '$100': steps_per_mm,  # X steps/mm
            '$101': steps_per_mm,  # Y steps/mm
            '$102': steps_per_mm,  # Z steps/mm
            '$110': 2000.0,  # X max rate (mm/min)
            '$111': 2000.0,  # Y max rate (mm/min)
            '$112': 500.0,   # Z max rate (mm/min)
            '$120': 500.0,   # X acceleration (mm/s²)
            '$121': 500.0,   # Y acceleration (mm/s²)
            '$122': 100.0,   # Z acceleration (mm/s²)
            '$130': 200.0,   # X max travel (mm)
            '$131': 200.0,   # Y max travel (mm)
            '$132': 200.0,   # Z max travel (mm)
        }
        
        return settings
    
    def __str__(self):
        """Représentation textuelle de la configuration"""
        ms1, ms2, ms3 = self.get_microstep_pins(self.microsteps)
        
        return f"""Configuration A4988:
  Driver: {self.driver_name}
  Microstepping: 1/{self.microsteps} (MS1={ms1}, MS2={ms2}, MS3={ms3})
  Courant max: {self.max_current}A
  Tension moteur: {self.motor_voltage_min}-{self.motor_voltage_max}V
  Pulse min: {self.min_step_pulse_width}µs
  Setup time: {self.min_direction_setup_time}µs
"""


# Instance globale
a4988_config = A4988Config()


def main():
    """Fonction de test et d'affichage de la configuration"""
    print("=== Configuration A4988 ===\n")
    print(a4988_config)
    
    # Afficher le schéma de câblage
    print("\n" + a4988_config.get_wiring_diagram())
    
    # Calculer Vref pour différents courants
    print("\n=== Calcul Vref pour limitation de courant ===")
    for current in [0.5, 1.0, 1.5, 2.0]:
        vref = a4988_config.calculate_current_limit_vref(current)
        print(f"  {current}A → Vref = {vref:.3f}V")
    
    # Afficher les paramètres GRBL
    print("\n=== Paramètres GRBL recommandés ===")
    settings = a4988_config.get_grbl_settings()
    for param, value in sorted(settings.items()):
        print(f"  {param} = {value}")
    
    # Afficher les modes de microstepping
    print("\n=== Modes de Microstepping ===")
    for steps, (ms1, ms2, ms3) in a4988_config.microstep_modes.items():
        print(f"  1/{steps:2d} step: MS1={ms1}, MS2={ms2}, MS3={ms3}")


if __name__ == "__main__":
    main()

# Made with Bob
