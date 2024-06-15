import smbus
import time

# Adresse I2C par défaut de l'appareil BH1750
DEVICE = 0x23  # Adresse I2C par défaut de l'appareil

# Commandes pour le BH1750
POWER_DOWN = 0x00  # Pas d'état actif
POWER_ON = 0x01  # Allumer
RESET = 0x07  # Réinitialiser la valeur du registre de données

# Démarrer la mesure à une résolution de 4 lx. Temps typique 16 ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Démarrer la mesure à une résolution de 1 lx. Temps typique 120 ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Démarrer la mesure à une résolution de 0.5 lx. Temps typique 120 ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Démarrer la mesure à une résolution de 1 lx. Temps typique 120 ms
# L'appareil est automatiquement mis hors tension après la mesure.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Démarrer la mesure à une résolution de 0.5 lx. Temps typique 120 ms
# L'appareil est automatiquement mis hors tension après la mesure.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Démarrer la mesure à une résolution de 1 lx. Temps typique 120 ms
# L'appareil est automatiquement mis hors tension après la mesure.
ONE_TIME_LOW_RES_MODE = 0x23

# Initialiser le bus I2C
bus = smbus.SMBus(1)  # Utilisez 0 si vous avez une Raspberry Pi Rev 1

def convertToNumber(data):
	# Fonction simple pour convertir 2 octets de données en un nombre décimal.
	result = (data[1] + (256 * data[0])) / 1.2
	return result

def readLight(addr=DEVICE):
	# Lire les données de l'interface I2C
	data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
	return convertToNumber(data)

def main():
	try:
		while True:
			level = readLight()
			print(f"Niveau de lumière: {level:.2f} lx")
			time.sleep(1)  # Attendre 1 seconde avant de lire à nouveau
	except KeyboardInterrupt:
		print("Arrêt du programme.")

if __name__ == "__main__":
	main()