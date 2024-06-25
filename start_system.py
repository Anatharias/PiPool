import json
import os
import time
import threading
import logging
import RPi.GPIO as GPIO
from typing import Dict, Any
from sensor import SensorManager, load_config
from lcd_display import LCDManager  # Import the LCDManager class

class ConfigError(Exception):
    pass

def write_config(config: Dict[str, Any], file_path: str) -> None:
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=2)

class PoolControlSystem:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = load_config(config_file)
        self.setup_logging()
        self.setup_gpio()
        self.temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0, 'light': 0.0}
        self.history = []
        self.countdown_active = True  # Set countdown active to True at startup
        self.countdown_start_time = time.time()  # Set countdown start time to current time
        self.last_button_pressed = None
        self.lcd_manager = LCDManager(self.config)  # Initialize LCDManager
        self.sensor_manager = SensorManager(self.config)  # Initialize SensorManager

    def setup_logging(self):
        if self.config['error_logging']['enabled']:
            log_dir = self.config['error_logging']['log_directory']
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'pool_control_errors.log')
            logging.basicConfig(
                filename=log_file,
                level=logging.ERROR,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.config['gpio']['button_b1_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.config['gpio']['button_b2_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.config['gpio']['pump_relay_pin'], GPIO.OUT)

        # Set initial relay state
        if self.config['relay_state'] == "ON":
            GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.HIGH)
        else:
            GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)

    def log_status(self):
        while True:
            try:
                self.config = load_config(self.config_file)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.history.append(self.temperatures.copy())

                if len(self.history) > self.config['average_samples']:
                    self.history.pop(0)

                avg_temps = {key: sum(h[key] for h in self.history) / len(self.history) for key in self.temperatures if key != 'temp_A'}
                delta_temp = self.temperatures['temp_S'] - self.temperatures['temp_E']

                log_message = (
                    f"{timestamp} | RELAY: {self.config['relay_state']} - [Reason: {self.last_button_pressed}] "
                    f"| Temp. Entrée: {self.temperatures['temp_E']:.2f} - Moyenne: {avg_temps['temp_E']:.2f} "
                    f"| Temp. Sortie: {self.temperatures['temp_S']:.2f} - Moyenne: {avg_temps['temp_S']:.2f} "
                    f"| Temp. Air: {self.temperatures['temp_A']:.2f} "
                    f"| Delta Temp: {delta_temp:.2f} "
                    f"| Luminosité: {self.temperatures['light']:.2f} - Moyenne: {avg_temps['light']:.2f} "
                    f"| Last Button Pressed: {self.last_button_pressed}"
                )
                print(log_message)

                if self.countdown_active:
                    time_left = self.config['water_replace_time'] - (time.time() - self.countdown_start_time)
                    if time_left > 0:
                        log_message += f" | Water Replace Time Left: {time_left:.2f} seconds"
                        print(log_message)
                    else:
                        self.countdown_active = False

                time.sleep(10)  # Log every 10 seconds
            except Exception as e:
                logging.error(f"Error in log_status: {e}")

    def button_b1_handler(self):
        while True:
            if GPIO.input(self.config['gpio']['button_b1_pin']) == GPIO.LOW:
                try:
                    self.config = load_config(self.config_file)
                    if not self.countdown_active or self.last_button_pressed == "B2":
                        self.last_button_pressed = "B1"
                        self.config['relay_state'] = "ON"
                        self.config['last_pump_start_time'] = time.time()
                        self.config['button_b1_last_pressed'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        write_config(self.config, self.config_file)
                        GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.HIGH)
                        self.countdown_active = True
                        self.countdown_start_time = time.time()
                        print("Pump started/restarted by B1")
                    time.sleep(0.5)  # Debounce delay
                except Exception as e:
                    logging.error(f"Error in button_b1_handler: {e}")
            time.sleep(0.1)

    def button_b2_handler(self):
        while True:
            if GPIO.input(self.config['gpio']['button_b2_pin']) == GPIO.LOW:
                try:
                    self.config = load_config(self.config_file)
                    self.last_button_pressed = "B2"
                    self.config['relay_state'] = "OFF"
                    self.config['button_b2_last_pressed'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    write_config(self.config, self.config_file)
                    GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)
                    self.countdown_active = False
                    print("Pump stopped by B2")
                    time.sleep(0.5)  # Debounce delay
                except Exception as e:
                    logging.error(f"Error in button_b2_handler: {e}")
            time.sleep(0.1)

    def sensor_loop(self):
        while True:
            try:
                temp_data = self.sensor_manager.get_temperature_data()
                light_level = self.sensor_manager.get_light_level()
                self.temperatures.update(temp_data)
                self.temperatures['light'] = light_level
                self.lcd_manager.update_displays(self.temperatures)  # Update LCD displays
            except Exception as e:
                logging.error(f"Error reading sensor data: {e}")
            time.sleep(self.config['sensors']['temperature']['update_interval'])

    def lcd_display_loop(self):
        while True:
            self.lcd_manager.update_displays(self.temperatures)  # Update LCD displays
            time.sleep(self.config['sensors']['temperature']['update_interval'])

    def run(self):
        threads = [
            threading.Thread(target=self.sensor_loop),
            threading.Thread(target=self.button_b1_handler),
            threading.Thread(target=self.button_b2_handler),
            threading.Thread(target=self.log_status)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

def main():
    try:
        pool_control = PoolControlSystem('config.json')
        pool_control.run()
    except ConfigError as e:
        print(f"Configuration error: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.exception("An unexpected error occurred")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()