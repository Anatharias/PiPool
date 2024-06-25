import time
import tm1637
import json
import logging
import os
from typing import Dict, Any

def load_config(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ConfigError(f"Error loading configuration: {e}")

class ConfigError(Exception):
    pass

class LCDManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        self.displays = self._initialize_displays()
        self.display_settings = {
            "update_interval": self.config['sensors']['temperature'].get('update_interval', 1),
            "temperature_format": "{:.1f}",
            "time_format": "%H%M"
        }

    def setup_logging(self):
        if self.config['error_logging']['enabled']:
            log_dir = self.config['error_logging']['log_directory']
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'lcd_errors.log')
            logging.basicConfig(
                filename=log_file,
                level=logging.ERROR,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def _initialize_displays(self) -> Dict[str, tm1637.TM1637]:
        displays = {}
        temp_displays = self.config['sensors']['temperature']['displays']
        for key, display_info in temp_displays.items():
            try:
                displays[key] = tm1637.TM1637(
                    clk=display_info['clk_pin'],
                    dio=display_info['dio_pin']
                )
            except Exception as e:
                logging.error(f"Error initializing display {key}: {e}")
        return displays

    def display_temperature(self, display_key: str, temp: float) -> None:
        try:
            temp_str = self.display_settings['temperature_format'].format(temp)
            int_part, frac_part = temp_str.split(".")
            display_str = f"{int_part[:2]} {frac_part[0]}"
            self.displays[display_key].show(display_str)
        except (ValueError, TypeError, KeyError) as e:
            error_msg = f"Error displaying temperature on {display_key}: {e}"
            print(error_msg)
            if self.config['error_logging']['enabled']:
                logging.error(error_msg)

    def display_time(self) -> None:
        current_time = time.strftime(self.display_settings['time_format'])
        self.displays['H'].show(current_time, colon=True)

    def update_displays(self, temperatures: Dict[str, float]) -> None:
        temp_displays = self.config['sensors']['temperature']['displays']
        for key, display_info in temp_displays.items():
            if key != 'H':  # 'H' is reserved for time display
                sensor_name = display_info['name']
                if sensor_name in temperatures:
                    self.display_temperature(key, temperatures[sensor_name])
                else:
                    logging.error(f"Temperature for '{sensor_name}' not found in provided temperatures.")
        self.display_time()

def main():
    try:
        config = load_config('config.json')
        lcd_manager = LCDManager(config)
        while True:
            # Simulate temperature readings (replace with actual data source)
            temperatures = {
                'pool_water': 19.5,
                'solar_collector_output': 30.3,
                'ambient': 23.3
            }
            lcd_manager.update_displays(temperatures)
            time.sleep(lcd_manager.display_settings['update_interval'])
    except ConfigError as e:
        print(f"Configuration error: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if config['error_logging']['enabled']:
            logging.exception("An unexpected error occurred")

if __name__ == "__main__":
    main()