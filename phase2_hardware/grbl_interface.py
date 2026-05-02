"""
Interface de communication avec GRBL
Gère la communication série et l'envoi de commandes G-code
"""

import serial
import time
import re
from typing import Optional, List, Tuple
from enum import Enum


class GRBLStatus(Enum):
    """États possibles de GRBL"""
    IDLE = "Idle"
    RUN = "Run"
    HOLD = "Hold"
    JOG = "Jog"
    ALARM = "Alarm"
    DOOR = "Door"
    CHECK = "Check"
    HOME = "Home"
    SLEEP = "Sleep"
    UNKNOWN = "Unknown"


class GRBLInterface:
    """Interface de communication avec GRBL via port série"""
    
    def __init__(self, port: str = 'COM8', baudrate: int = 115200, timeout: float = 2.0):
        """
        Initialise l'interface GRBL
        
        Args:
            port: Port série (ex: 'COM3' sur Windows, '/dev/ttyUSB0' sur Linux)
            baudrate: Vitesse de communication (généralement 115200 pour GRBL)
            timeout: Timeout pour les opérations série (secondes)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.grbl_version = None
        
        # Buffer pour les réponses
        self.response_buffer: List[str] = []
        
    def connect(self) -> bool:
        """
        Établit la connexion avec GRBL
        
        Returns:
            bool: True si la connexion est établie
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Attendre l'initialisation de GRBL
            time.sleep(2)
            
            # Vider le buffer
            self.serial_connection.flushInput()
            
            # Lire le message de démarrage de GRBL
            startup_msg = self._read_line()
            print(f"GRBL Startup: {startup_msg}")
            
            # Extraire la version
            version_match = re.search(r'Grbl\s+([\d.]+)', startup_msg)
            if version_match:
                self.grbl_version = version_match.group(1)
                print(f"GRBL Version: {self.grbl_version}")
            
            self.is_connected = True
            print(f"Connecté à GRBL sur {self.port}")
            
            return True
            
        except serial.SerialException as e:
            print(f"Erreur de connexion: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Ferme la connexion série"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.is_connected = False
            print("Déconnecté de GRBL")
    
    def _read_line(self, timeout: Optional[float] = None) -> str:
        """
        Lit une ligne depuis le port série
        
        Args:
            timeout: Timeout optionnel pour cette lecture
            
        Returns:
            str: Ligne lue (sans le retour à la ligne)
        """
        if not self.is_connected or not self.serial_connection:
            return ""
        
        old_timeout = self.serial_connection.timeout
        if timeout is not None:
            self.serial_connection.timeout = timeout
        
        try:
            line = self.serial_connection.readline().decode('utf-8').strip()
            return line
        except Exception as e:
            print(f"Erreur de lecture: {e}")
            return ""
        finally:
            self.serial_connection.timeout = old_timeout
    
    def send_command(self, command: str, wait_for_ok: bool = True) -> Tuple[bool, List[str]]:
        """
        Envoie une commande G-code à GRBL
        
        Args:
            command: Commande G-code à envoyer
            wait_for_ok: Attendre la confirmation 'ok' ou 'error'
            
        Returns:
            tuple: (succès, liste des réponses)
        """
        if not self.is_connected or not self.serial_connection:
            print("Erreur: Non connecté à GRBL")
            return False, []
        
        # Nettoyer la commande
        command = command.strip()
        
        # Envoyer la commande
        try:
            self.serial_connection.write((command + '\n').encode('utf-8'))
            print(f"Envoyé: {command}")
            
            if not wait_for_ok:
                return True, []
            
            # Attendre la réponse
            responses = []
            while True:
                response = self._read_line()
                
                if not response:
                    break
                
                responses.append(response)
                print(f"Reçu: {response}")
                
                # Vérifier si c'est une réponse finale
                if response.lower() == 'ok':
                    return True, responses
                elif response.lower().startswith('error'):
                    return False, responses
            
            return False, responses
            
        except Exception as e:
            print(f"Erreur d'envoi: {e}")
            return False, []
    
    def send_gcode_list(self, gcode_list: List[str]) -> bool:
        """
        Envoie une liste de commandes G-code
        
        Args:
            gcode_list: Liste de commandes G-code
            
        Returns:
            bool: True si toutes les commandes ont été envoyées avec succès
        """
        for gcode in gcode_list:
            success, _ = self.send_command(gcode)
            if not success:
                print(f"Échec de la commande: {gcode}")
                return False
        return True
    
    def get_status(self) -> Tuple[GRBLStatus, dict]:
        """
        Demande le statut actuel de GRBL
        
        Returns:
            tuple: (état, dictionnaire avec les informations de statut)
        """
        if not self.is_connected or not self.serial_connection:
            return GRBLStatus.UNKNOWN, {}
        
        # Envoyer la commande de statut
        self.serial_connection.write(b'?')
        
        # Lire la réponse
        response = self._read_line(timeout=0.5)
        
        if not response or not response.startswith('<'):
            return GRBLStatus.UNKNOWN, {}
        
        # Parser la réponse (format: <Idle|MPos:0.000,0.000,0.000|...>)
        try:
            # Extraire l'état
            state_match = re.search(r'<([^|]+)', response)
            state_str = state_match.group(1) if state_match else "Unknown"
            
            # Convertir en enum
            try:
                state = GRBLStatus(state_str)
            except ValueError:
                state = GRBLStatus.UNKNOWN
            
            # Extraire les positions
            info = {}
            
            # Position machine (MPos)
            mpos_match = re.search(r'MPos:([-\d.]+),([-\d.]+),([-\d.]+)', response)
            if mpos_match:
                info['mpos'] = [float(mpos_match.group(i)) for i in range(1, 4)]
            
            # Position de travail (WPos)
            wpos_match = re.search(r'WPos:([-\d.]+),([-\d.]+),([-\d.]+)', response)
            if wpos_match:
                info['wpos'] = [float(wpos_match.group(i)) for i in range(1, 4)]
            
            return state, info
            
        except Exception as e:
            print(f"Erreur de parsing du statut: {e}")
            return GRBLStatus.UNKNOWN, {}
    
    def home(self) -> bool:
        """
        Lance la séquence de homing (retour à l'origine)
        
        Returns:
            bool: True si le homing est réussi
        """
        print("Lancement du homing...")
        success, responses = self.send_command('$H')
        
        if success:
            print("Homing terminé")
        else:
            print("Échec du homing")
        
        return success
    
    def unlock(self) -> bool:
        """
        Déverrouille GRBL (après une alarme)
        
        Returns:
            bool: True si le déverrouillage est réussi
        """
        print("Déverrouillage de GRBL...")
        success, _ = self.send_command('$X')
        return success
    
    def soft_reset(self):
        """Effectue un soft reset de GRBL"""
        if self.is_connected and self.serial_connection:
            print("Soft reset de GRBL...")
            self.serial_connection.write(b'\x18')  # Ctrl-X
            time.sleep(2)
            
            # Lire le message de redémarrage
            startup_msg = self._read_line()
            print(f"GRBL redémarré: {startup_msg}")
    
    def set_work_zero(self) -> bool:
        """
        Définit la position actuelle comme origine du système de coordonnées de travail
        
        Returns:
            bool: True si réussi
        """
        print("Définition de l'origine de travail...")
        success, _ = self.send_command('G10 L20 P0 X0 Y0 Z0')
        return success
    
    def jog(self, x: Optional[float] = None, y: Optional[float] = None, 
            z: Optional[float] = None, feed_rate: float = 1000) -> bool:
        """
        Commande de jog (déplacement manuel)
        
        Args:
            x, y, z: Déplacements relatifs (mm)
            feed_rate: Vitesse d'avance (mm/min)
            
        Returns:
            bool: True si la commande est acceptée
        """
        # Construire la commande de jog
        jog_cmd = f"$J=G91 F{feed_rate}"
        
        if x is not None:
            jog_cmd += f" X{x:.3f}"
        if y is not None:
            jog_cmd += f" Y{y:.3f}"
        if z is not None:
            jog_cmd += f" Z{z:.3f}"
        
        success, _ = self.send_command(jog_cmd, wait_for_ok=False)
        return success
    
    def move_absolute(self, x: Optional[float] = None, y: Optional[float] = None,
                     z: Optional[float] = None, feed_rate: float = 1000) -> bool:
        """
        Déplacement en coordonnées absolues
        
        Args:
            x, y, z: Positions absolues (mm)
            feed_rate: Vitesse d'avance (mm/min)
            
        Returns:
            bool: True si réussi
        """
        # Mode absolu + interpolation linéaire
        gcode = f"G90 G1 F{feed_rate}"
        
        if x is not None:
            gcode += f" X{x:.3f}"
        if y is not None:
            gcode += f" Y{y:.3f}"
        if z is not None:
            gcode += f" Z{z:.3f}"
        
        success, _ = self.send_command(gcode)
        return success
    
    def get_settings(self) -> dict:
        """
        Récupère les paramètres de configuration de GRBL
        
        Returns:
            dict: Dictionnaire des paramètres
        """
        if not self.is_connected:
            return {}
        
        # Envoyer la commande $$
        self.serial_connection.write(b'$$\n')
        time.sleep(0.5)
        
        settings = {}
        while True:
            line = self._read_line(timeout=0.1)
            if not line:
                break
            
            # Parser les lignes de paramètres (format: $N=value)
            match = re.match(r'\$(\d+)=([\d.]+)', line)
            if match:
                param_num = int(match.group(1))
                param_value = float(match.group(2))
                settings[param_num] = param_value
        
        return settings
    
    def set_setting(self, param_num: int, value: float) -> bool:
        """
        Modifie un paramètre de configuration GRBL
        
        Args:
            param_num: Numéro du paramètre
            value: Nouvelle valeur
            
        Returns:
            bool: True si réussi
        """
        command = f"${param_num}={value}"
        success, _ = self.send_command(command)
        return success
    
    def __enter__(self):
        """Support du context manager"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager"""
        self.disconnect()


def main():
    """Fonction de test de l'interface GRBL"""
    print("=== Test Interface GRBL ===\n")
    
    # Configuration
    port = input("Port série (ex: COM3 ou /dev/ttyUSB0): ").strip()
    if not port:
        port = "COM3"
    
    # Utilisation avec context manager
    with GRBLInterface(port=port) as grbl:
        if not grbl.is_connected:
            print("Impossible de se connecter à GRBL")
            return
        
        # Menu interactif
        while True:
            print("\n--- Menu ---")
            print("1. Statut")
            print("2. Homing")
            print("3. Unlock")
            print("4. Définir origine")
            print("5. Jog X+10")
            print("6. Jog Y+10")
            print("7. Déplacement absolu")
            print("8. Paramètres")
            print("9. Soft Reset")
            print("0. Quitter")
            
            choice = input("\nChoix: ").strip()
            
            if choice == '1':
                state, info = grbl.get_status()
                print(f"État: {state.value}")
                if 'mpos' in info:
                    print(f"Position machine: {info['mpos']}")
                if 'wpos' in info:
                    print(f"Position travail: {info['wpos']}")
            
            elif choice == '2':
                grbl.home()
            
            elif choice == '3':
                grbl.unlock()
            
            elif choice == '4':
                grbl.set_work_zero()
            
            elif choice == '5':
                grbl.jog(x=10)
            
            elif choice == '6':
                grbl.jog(y=10)
            
            elif choice == '7':
                x = float(input("X: "))
                y = float(input("Y: "))
                grbl.move_absolute(x=x, y=y)
            
            elif choice == '8':
                settings = grbl.get_settings()
                print("\nParamètres GRBL:")
                for num, value in sorted(settings.items()):
                    print(f"  ${num} = {value}")
            
            elif choice == '9':
                grbl.soft_reset()
            
            elif choice == '0':
                break


if __name__ == "__main__":
    main()

# Made with Bob
