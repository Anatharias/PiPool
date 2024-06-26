import json
import os
import time
import threading
import logging
import RPi.GPIO as GPIO
from typing import Dict, Any
from sensor import SensorManager, load_config
from lcd_display import LCDManager

class ConfigError(Exception):
    pass

def write_config(config: Dict[str, Any], file_path: str) -> None:
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=2)

class PoolControlSystem:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = load_config(config_file)
        self.temperatures = {'temp_E': 0.0, 'temp_A': 0.0, 'temp_S': 0.0, 'light': 0.0}
        self.history = []
        self.countdown_active = True
        self.countdown_start_time = time.time()
        self.last_button_pressed = None
        self.last_action_reason = "System initialized"
        self.lcd_manager = LCDManager(self.config)
        self.sensor_manager = SensorManager(self.config)
        self.running = True

        self.setup_logging()
        self.setup_gpio()

    def setup_logging(self):
        log_output = self.config.get('log_output', 'file')
        
        if log_output == 'file' and self.config['error_logging']['enabled']:
            log_dir = self.config['error_logging']['log_directory']
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'pool_control.log')
            logging.basicConfig(
                filename=log_file,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        elif log_output == 'terminal':
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        else:
            raise ConfigError("Invalid log_output value. It should be either 'file' or 'terminal'.")

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.config['gpio']['button_b1_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.config['gpio']['button_b2_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.config['gpio']['pump_relay_pin'], GPIO.OUT)

        if self.config['relay_state'] == "ON":
            GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.HIGH)
        else:
            GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)

    def log_status(self):
        while self.running:
            try:
                logging.info("Logging status thread is running")
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.history.append(self.temperatures.copy())

                if len(self.history) > self.config['average_samples']:
                    self.history.pop(0)

                avg_temps = {key: sum(h[key] for h in self.history) / len(self.history) for key in self.temperatures if key != 'temp_A'}
                delta_temp = self.temperatures['temp_S'] - self.temperatures['temp_E']

                log_message = (
                    f"{timestamp} | RELAY: {self.config['relay_state']} - [Reason: {self.last_action_reason}] "
                    f"| Temp. Entrée: {self.temperatures['temp_E']:.2f} - Moyenne: {avg_temps['temp_E']:.2f} "
                    f"| Temp. Sortie: {self.temperatures['temp_S']:.2f} - Moyenne: {avg_temps['temp_S']:.2f} "
                    f"| Delta Temp: {delta_temp:.2f} "
                    f"| Temp. Air: {self.temperatures['temp_A']:.2f} "
                    f"| Luminosité: {self.temperatures['light']:.2f} - Moyenne: {avg_temps['light']:.2f} "
                    f"| Last Button Pressed: {self.last_button_pressed}"
                )
                logging.info(log_message)
                print(log_message)

                if self.countdown_active:
                    time_left = self.config['water_replace_time'] - (time.time() - self.countdown_start_time)
                    if time_left > 0:
                        logging.info(f"Water Replace Time Left: {time_left:.2f} seconds")
                    else:
                        self.countdown_active = False
                        self.last_action_reason = "Water replacement time ended. Switching to normal control logic."
                        logging.info(self.last_action_reason)

                if self.config['relay_state'] == "ON":
                    if self.last_button_pressed == "B1":
                        self.last_action_reason = "Pump started by Button B1"
                    elif self.last_button_pressed == "B2":
                        self.last_action_reason = "Pump stopped by Button B2"
                elif self.config['relay_state'] == "OFF":
                    self.last_action_reason = "Pump stopped (automatic control)"
                
                time.sleep(self.config['log_interval'])

            except KeyError as e:
                logging.error(f"Missing key in temperatures or config: {e}")
            except Exception as e:
                logging.error(f"Error in log_status: {e}")

    def button_b1_action(self):
        self.last_button_pressed = "B1"
        self.config['relay_state'] = "ON"
        self.config['last_pump_start_time'] = time.time()
        self.config['button_b1_last_pressed'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_config(self.config, self.config_file)
        GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.HIGH)
        self.countdown_active = True
        self.countdown_start_time = time.time()
        self.last_action_reason = "Button B1 pressed"
        logging.info("Pump started/restarted by B1")

    def button_b2_action(self):
        self.last_button_pressed = "B2"
        self.config['relay_state'] = "OFF"
        self.config['button_b2_last_pressed'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_config(self.config, self.config_file)
        GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)
        self.countdown_active = False
        self.last_action_reason = "Button B2 pressed"
        logging.info("Pump stopped by B2")

    def button_handler(self, button_pin, action):
        while self.running:
            if GPIO.input(button_pin) == GPIO.LOW:
                action()
                time.sleep(0.3)  # Debounce delay

    def sensor_loop(self):
        while self.running:
            try:
                temp_data = self.sensor_manager.get_temperature_data()
                light_level = self.sensor_manager.get_light_level()
                self.temperatures.update(temp_data)
                self.temperatures['light'] = light_level
                self.lcd_manager.update_displays(self.temperatures)

                # Ajouter un print pour vérifier les données des capteurs
                print(f"Températures: {self.temperatures}, Niveau de lumière: {light_level}")

            except Exception as e:
                logging.error(f"Error reading sensor data: {e}")
            time.sleep(self.config['sensors']['temperature']['update_interval'])

    def control_loop(self):
        while self.running:
            try:
                if not self.countdown_active:
                    delta_temp = self.temperatures['temp_S'] - self.temperatures['temp_E']
                    
                    if self.last_button_pressed == "B2":
                        if self.config['relay_state'] != "OFF":
                            self.config['relay_state'] = "OFF"
                            GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)
                            self.last_action_reason = "Pump stopped by B2 (overrides all other conditions)"
                            logging.info(self.last_action_reason)
                    elif self.temperatures['light'] >= self.config['light_threshold']:
                        if delta_temp >= self.config['temp_delta_threshold']:
                            if self.config['relay_state'] != "ON":
                                self.config['relay_state'] = "ON"
                                GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.HIGH)
                                self.last_action_reason = f"Pump started: Light level ({self.temperatures['light']:.2f}) above threshold and delta temperature ({delta_temp:.2f}) above threshold"
                                logging.info(self.last_action_reason)
                        else:
                            if self.config['relay_state'] != "OFF":
                                self.config['relay_state'] = "OFF"
                                GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)
                                self.last_action_reason = f"Pump stopped: Light level ({self.temperatures['light']:.2f}) above threshold but delta temperature ({delta_temp:.2f}) below threshold"
                                logging.info(self.last_action_reason)
                    else:
                        if self.config['relay_state'] != "OFF":
                            self.config['relay_state'] = "OFF"
                            GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)
                            self.last_action_reason = f"Pump stopped: Light level ({self.temperatures['light']:.2f}) below threshold"
                            logging.info(self.last_action_reason)
                    
                    write_config(self.config, self.config_file)
                else:
                    self.last_action_reason = "Water replacement in progress"
            except Exception as e:
                logging.error(f"Error in control_loop: {e}")
            
            time.sleep(10)

    def run(self):
        """Run the pool control system."""
        threads = [
            threading.Thread(target=self.sensor_loop),
            threading.Thread(target=self.control_loop),
            threading.Thread(target=self.button_handler, args=(self.config['gpio']['button_b1_pin'], self.button_b1_action)),
            threading.Thread(target=self.button_handler, args=(self.config['gpio']['button_b2_pin'], self.button_b2_action)),
            threading.Thread(target=self.log_status)
        ]

        for thread in threads:
            thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            self.running = False

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
        if GPIO.getmode() is not None:
            GPIO.cleanup()

if __name__ == "__main__":
    main()