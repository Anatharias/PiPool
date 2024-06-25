import os
import json
import time
import logging
import RPi.GPIO as GPIO
from typing import Dict, Any
from sensor import SensorManager, load_config

class ConfigError(Exception):
    pass

def write_config(config: Dict[str, Any], file_path: str) -> None:
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=2)

def setup_logging(config: Dict[str, Any]):
    if config['error_logging']['enabled']:
        log_dir = config['error_logging']['log_directory']
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'control_errors.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

def control_loop(temperatures: Dict[str, float]):
    try:
        config = load_config('config.json')
        setup_logging(config)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(config['gpio']['button_b1_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(config['gpio']['button_b2_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(config['gpio']['pump_relay_pin'], GPIO.OUT, initial=GPIO.LOW)

        sensor_manager = SensorManager(config)

        start_time = time.time()
        water_replace_time = config['water_replace_time']

        while True:
            config = load_config('config.json')
            current_time = time.time()

            if current_time - start_time < water_replace_time - 5:
                pump_state = config['relay_state']
                reason = f"Waiting for {water_replace_time} seconds after start"
            else:
                temp_data = sensor_manager.get_temperature_data()
                light_level = sensor_manager.get_light_level()
                temperatures.update(temp_data)
                temperatures['light'] = light_level

                temp_E = temperatures['temp_E']
                temp_S = temperatures['temp_S']
                delta_temp = temp_S - temp_E

                logging.info(f"Sensor Data: {temperatures}")
                logging.info(f"Temp. Entrée: {temp_E:.2f} | Temp. Sortie: {temp_S:.2f} | Delta Temp: {delta_temp:.2f}")

                if delta_temp < config['temp_delta_threshold']:
                    pump_state = "OFF"
                    reason = f"delta temperature ({delta_temp:.2f}) lower than threshold"
                    GPIO.output(config['gpio']['pump_relay_pin'], GPIO.LOW)
                else:
                    pump_state = "ON"
                    reason = f"delta temperature ({delta_temp:.2f}) above threshold"
                    GPIO.output(config['gpio']['pump_relay_pin'], GPIO.HIGH)

            if GPIO.input(config['gpio']['button_b1_pin']) == GPIO.LOW:
                logging.info("Button B1 pressed.")
                config['last_button_pressed'] = "B1"
                config['relay_state'] = "ON"
                config['last_pump_start_time'] = time.time()
                config['button_b1_last_pressed'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                write_config(config, 'config.json')
                GPIO.output(config['gpio']['pump_relay_pin'], GPIO.HIGH)
                time.sleep(config['water_replace_time'])
                config = load_config('config.json')

                if not config.get('stopped_by_b2', False):
                    config['relay_state'] = "OFF"
                    write_config(config, 'config.json')
                    GPIO.output(config['gpio']['pump_relay_pin'], GPIO.LOW)
                logging.info("Pump stopped after water replacement by B1")
                time.sleep(0.5)

            elif GPIO.input(config['gpio']['button_b2_pin']) == GPIO.LOW:
                logging.info("Button B2 pressed.")
                config['last_button_pressed'] = "B2"
                config['relay_state'] = "OFF"
                config['stopped_by_b2'] = True
                config['button_b2_last_pressed'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                write_config(config, 'config.json')
                GPIO.output(config['gpio']['pump_relay_pin'], GPIO.LOW)
                time.sleep(0.5)

            current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            log_message = f"{current_time_str} | RELAY: {pump_state} - [Reason: {reason}] | Temp. Entrée: {temp_E:.2f} | Temp. Sortie: {temp_S:.2f} | Delta Temp: {delta_temp:.2f} | Luminosité: {temperatures['light']:.2f} | Last Button Pressed: {config.get('last_button_pressed', 'None')}"
            print(log_message)
            logging.info(log_message)

            time.sleep(10)

    except Exception as e:
        logging.error(f"Error in control loop: {e}")
        raise

def main():
    try:
        temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0, 'light': 0.0}
        control_loop(temperatures)
    except KeyboardInterrupt:
        print("\nExiting control loop.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.exception("An unexpected error occurred")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()