import time
import json
import logging
import os
from typing import Dict, Any
from w1thermsensor import W1ThermSensor, NoSensorFoundError
import smbus

class ConfigError(Exception):
    pass

def load_config(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ConfigError(f"Error loading configuration: {e}")

class SensorManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        self.temperature_sensors = self._initialize_temperature_sensors()
        self.light_sensor = self._initialize_light_sensor()

    def setup_logging(self):
        if self.config['error_logging']['enabled']:
            log_dir = self.config['error_logging']['log_directory']
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'sensor_errors.log')
            logging.basicConfig(
                filename=log_file,
                level=logging.ERROR,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def _initialize_temperature_sensors(self) -> Dict[str, W1ThermSensor]:
        sensors = {}
        temp_sensors = self.config['sensors']['temperature']['displays']
        for key, sensor_info in temp_sensors.items():
            if key != 'H':  # 'H' is reserved for time display
                try:
                    sensors[sensor_info['name']] = W1ThermSensor(sensor_id=sensor_info['id'])
                except NoSensorFoundError as e:
                    error_msg = f"Error initializing temperature sensor {key}: {e}"
                    print(error_msg)
                    logging.error(error_msg)
        return sensors

    def _initialize_light_sensor(self):
        light_config = self.config['sensors']['light']
        return {
            'device': light_config['device_address'],
            'mode': light_config['mode'],
            'bus': smbus.SMBus(light_config['bus_number'])
        }

    def get_temperature_data(self) -> Dict[str, float]:
        temp_data = {}
        for name, sensor in self.temperature_sensors.items():
            try:
                temp_data[name] = sensor.get_temperature()
            except NoSensorFoundError as e:
                error_msg = f"Error reading temperature data for {name}: {e}"
                print(error_msg)
                logging.error(error_msg)
                temp_data[name] = None
        return temp_data

    def convert_to_number(self, data):
        try:
            return (data[1] + (256 * data[0])) / 1.2
        except IndexError as e:
            error_msg = f"Error converting light data: {e}"
            print(error_msg)
            logging.error(error_msg)
            return None

    def get_light_level(self):
        try:
            data = self.light_sensor['bus'].read_i2c_block_data(int(self.light_sensor['device'], 16), int(self.light_sensor['mode'], 16))
            return self.convert_to_number(data)
        except IOError as e:
            error_msg = f"Error reading light level: {e}"
            print(error_msg)
            logging.error(error_msg)
            return None

    def sensor_loop(self):
        while True:
            temp_data = self.get_temperature_data()
            light_level = self.get_light_level()
            sensor_data = {**temp_data, 'light': light_level}
            print(sensor_data)  # You can replace this with your desired data handling
            time.sleep(self.config['sensors']['temperature']['update_interval'])

def main():
    try:
        config = load_config('config.json')
        sensor_manager = SensorManager(config)
        sensor_manager.sensor_loop()
    except ConfigError as e:
        print(f"Configuration error: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.exception("An unexpected error occurred")

if __name__ == "__main__":
    main()