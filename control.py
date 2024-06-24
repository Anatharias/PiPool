import os
import json
import time
import RPi.GPIO as GPIO
from sensor import get_temperature_data, get_light_level

# Configuration file path
CONFIG_FILE = '/home/anatharias/pipool/config.json'

def read_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file '{CONFIG_FILE}' not found.")
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def write_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

def control_loop(temperatures):
    config = read_config()

    # Initialize GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(config['button_b1_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(config['button_b2_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(config['button_b3_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(config['pump_relay_pin'], GPIO.OUT, initial=GPIO.LOW)

    while True:
        config = read_config()

        # Add your control logic here based on temperature and light conditions
        # For example, check if conditions allow pump operation
        delta_temp = temperatures['temp_S'] - temperatures['temp_E']
        if delta_temp < config['temp_delta_threshold']:
            pump_state = "OFF"
            reason = f"delta temperature ({delta_temp:.2f}) below threshold"
            GPIO.output(config['pump_relay_pin'], GPIO.LOW)
        else:
            pump_state = "ON"
            reason = "acceptable conditions"
            GPIO.output(config['pump_relay_pin'], GPIO.HIGH)

        # Read button states
        if GPIO.input(config['button_b1_pin']) == GPIO.LOW:
            print("Button B1 pressed.")
            config['last_button_pressed'] = "B1"
            config['relay_state'] = "ON"
            config['last_pump_start_time'] = time.time()
            write_config(config)
            time.sleep(config['water_replace_time'])  # Wait for water replacement time
            config = read_config()  # Refresh config after waiting

            # After water replace time, check if B2 was pressed during this time
            if not config['stopped_by_b2']:
                # Add additional logic here if needed
                pass

            config['relay_state'] = "OFF"
            write_config(config)
            print("Pump stopped after water replacement by B1")
            time.sleep(0.5)  # Debounce delay

        elif GPIO.input(config['button_b2_pin']) == GPIO.LOW:
            print("Button B2 pressed.")
            config['last_button_pressed'] = "B2"
            config['relay_state'] = "OFF"
            config['stopped_by_b2'] = True
            write_config(config)
            time.sleep(0.5)  # Debounce delay

        # Add more button handlers if needed (e.g., for Button B3)

        # Print status every 10 seconds
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"{current_time} | Pompe {pump_state} dans {config['water_replace_time']} secondes à cause de {reason}")

        time.sleep(10)  # 10 seconds delay

def main():
    try:
        # Simulated temperature data (replace with actual sensor data)
        temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0, 'light': 0.0}

        control_loop(temperatures)
    except KeyboardInterrupt:
        print("\nExiting control loop.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
