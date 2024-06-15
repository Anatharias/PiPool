# control.py

import time
import RPi.GPIO as GPIO

# Configuration des pins GPIO pour le relais
RELAY_PIN = 18  # Par exemple

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

def relay_on():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Relais activé")

def relay_off():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Relais désactivé")

def control_loop():
    try:
        while True:
            # Ajouter la logique pour le contrôle du relais
            # Exemple basique pour activer et désactiver le relais
            relay_on()
            time.sleep(5)  # Relais activé pendant 5 secondes
            relay_off()
            time.sleep(5)  # Relais désactivé pendant 5 secondes

    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    control_loop()
