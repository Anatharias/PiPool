import smbus
import json

class LightSensor:
    def __init__(self, config):
        self.device = config['sensors']['light']['device_address']
        self.mode = config['sensors']['light']['mode']
        self.bus = smbus.SMBus(config['sensors']['light']['bus_number'])
        self.average_samples = config['average_samples']
        self.light_threshold = config['light_threshold']
        self.light_history = []

    def get_light_level(self):
        """Read the light level from the sensor."""
        try:
            data = self.bus.read_i2c_block_data(int(self.device, 16), int(self.mode, 16))
            light_level = self.convert_to_number(data)
            return light_level
        except IOError:
            return None

    def convert_to_number(self, data):
        """Convert the raw light sensor data to a number."""
        try:
            return (data[1] + (256 * data[0])) / 1.2
        except IndexError:
            return None

    def update_light_history(self, light_level):
        """Update the history of light levels with a new sample, ignoring the first one."""
        if len(self.light_history) < self.average_samples:
            self.light_history.append(light_level)
        else:
            self.light_history.pop(0)
            self.light_history.append(light_level)

    def get_moving_mean(self):
        """Calculate the moving mean of the light levels."""
        if len(self.light_history) <= 1:
            return None
        return sum(self.light_history[1:]) / (len(self.light_history) - 1)

    def is_average_light_sufficient(self):
        """Check if the moving mean of light is above the threshold."""
        mean_light = self.get_moving_mean()
        if mean_light is not None:
            return mean_light > self.light_threshold
        return False

# Charger la configuration depuis le fichier config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Créer une instance de LightSensor avec la configuration chargée
sensor = LightSensor(config)

# Mettre à jour l'historique des niveaux de lumière et obtenir le résultat
light_level = sensor.get_light_level()
if light_level is not None:
    sensor.update_light_history(light_level)

# Obtenir la moyenne mobile et vérifier si elle dépasse le seuil
average_light = sensor.get_moving_mean()
result = sensor.is_average_light_sufficient()

# Afficher les résultats
print(f"Valeur moyenne de la lumière: {average_light}")
print(f"Luminosité moyenne dépasse la limite: {result}")