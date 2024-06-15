# sensor.py
#BH1750 for sun brightness
#DS18B20 for temperature

import time
from w1thermsensor import W1ThermSensor, SensorNotReadyError, NoSensorFoundError
import smbus

# Définir les IDs des capteurs DS18B20
SENSOR_IDS = {
	"temp_E": "0000006bbe43",
	"temp_A": "0000006b6275",
	"temp_S": "00000069d1fe"
}

# Adresse I2C par défaut du BH1750
DEVICE = 0x23

# Commandes pour le BH1750
ONE_TIME_HIGH_RES_MODE_1 = 0x20

# Initialiser le bus I2C
bus = smbus.SMBus(1)  # Utilisez 0 si vous avez une Raspberry Pi Rev 1

def convert_to_number(data):
	result = (data[1] + (256 * data[0])) / 1.2
	return result

def read_light(addr=DEVICE):
	data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
	return convert_to_number(data)

def read_all_temperatures():
	temperatures = {}
	try:
		sensors = W1ThermSensor.get_available_sensors()
		for sensor in sensors:
			try:
				temperature_celsius = sensor.get_temperature()
				if sensor.id in SENSOR_IDS.values():
					for key, value in SENSOR_IDS.items():
						if sensor.id == value:
							temperatures[key] = temperature_celsius
							break
			except SensorNotReadyError as e:
				print(f"Erreur lors de la lecture de la température depuis le capteur {sensor.id}: {e}")
	except NoSensorFoundError as e:
		print(f"Aucun capteur trouvé: {e}")
	return temperatures

def sensor_loop(temperatures):
	while True:
		new_temperatures = read_all_temperatures()
		light_intensity = read_light()

		# Mettre à jour le dictionnaire partagé
		temperatures.update(new_temperatures)
		temperatures['light'] = light_intensity

		# Implémenter la journalisation ou le traitement supplémentaire si nécessaire
		print(f"Températures: {new_temperatures}, Intensité lumineuse: {light_intensity:.2f} lx")
		time.sleep(15)

if __name__ == "__main__":
	dummy_temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0, 'light': 0.0}
	sensor_loop(dummy_temperatures)
