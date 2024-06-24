import json
import os
import time
import threading
import RPi.GPIO as GPIO
from control import control_loop
from sensor import sensor_loop
from lcd_display import lcd_display_loop

# Configuration file path
CONFIG_FILE = '/home/anatharias/pipool/config.json'

def read_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "relay_state": "OFF",
            "last_button_pressed": "None",
            "last_pump_start_time": None,
            "stopped_by_b2": False,
            "button_b1_pin": 5,
            "button_b2_pin": 6,
            "button_b3_pin": 13,
            "pump_relay_pin": 17,
            "light_threshold": 10000,
            "temp_delta_threshold": 0.5,
            "water_replace_time": 300,
            "analysis_interval": 600,
            "average_samples": 30
        }
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def write_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

# Read configurations from config.json
config = read_config()
BUTTON_B1_PIN = config['button_b1_pin']
BUTTON_B2_PIN = config['button_b2_pin']
BUTTON_B3_PIN = config['button_b3_pin']
PUMP_RELAY_PIN = config['pump_relay_pin']
LIGHT_THRESHOLD = config['light_threshold']
TEMP_DELTA_THRESHOLD = config['temp_delta_threshold']
WATER_REPLACE_TIME = config['water_replace_time']
ANALYSIS_INTERVAL = config['analysis_interval']
AVERAGE_SAMPLES = config['average_samples']

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)  # Ignore GPIO warnings
GPIO.setup(BUTTON_B1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_B2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_B3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PUMP_RELAY_PIN, GPIO.OUT)

def log_status(temperatures):
    history = []
    while True:
        config = read_config()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        history.append(temperatures.copy())

        if len(history) > AVERAGE_SAMPLES:
            history.pop(0)

        avg_temp_E = sum([t['temp_E'] for t in history]) / len(history)
        avg_temp_S = sum([t['temp_S'] for t in history]) / len(history)
        avg_temp_A = sum([t['temp_A'] for t in history]) / len(history)
        avg_light = sum([t['light'] for t in history]) / len(history)

        log_message = (
            f"{timestamp} | RELAY: {config['relay_state']} - [Reason: {config['last_button_pressed']}] "
            f"| Moy. Temp. Entrée: {temperatures['temp_E']:.2f} - Moyenne: {avg_temp_E:.2f} "
            f"| Moy. Temp. Sortie: {temperatures['temp_S']:.2f} - Moyenne: {avg_temp_S:.2f} "
            f"| Moy. Temp. Air: {temperatures['temp_A']:.2f} - Moyenne: {avg_temp_A:.2f} "
            f"| Moy. Luminosité: {temperatures['light']:.2f} - Moyenne: {avg_light:.2f} "
            f"| Last Button Pressed: {config['last_button_pressed']}"
        )
        print(log_message)
        time.sleep(10)  # Log every 10 seconds

def button_b1_handler():
    while True:
        if GPIO.input(BUTTON_B1_PIN) == GPIO.LOW:
            config = read_config()
            config['last_button_pressed'] = "B1"
            config['relay_state'] = "ON"
            config['last_pump_start_time'] = time.time()
            write_config(config)
            GPIO.output(PUMP_RELAY_PIN, GPIO.HIGH)
            print("System and pump started by B1")
            time.sleep(WATER_REPLACE_TIME)  # Wait for water replacement time

            # After water replace time, check if B2 was pressed during this time
            if not config['stopped_by_b2']:
                # Add additional logic here if needed
                pass

            GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)  # Stop pump
            config['relay_state'] = "OFF"
            write_config(config)
            print("Pump stopped after water replacement by B1")
            time.sleep(0.5)  # Debounce delay

        time.sleep(0.1)  # Short delay to avoid excessive CPU usage

def button_b2_handler():
    while True:
        if GPIO.input(BUTTON_B2_PIN) == GPIO.LOW:
            config = read_config()
            config['last_button_pressed'] = "B2"
            config['relay_state'] = "OFF"
            config['stopped_by_b2'] = True
            write_config(config)
            GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)
            print("Pump stopped by B2")
            time.sleep(0.5)  # Debounce delay

        time.sleep(0.1)  # Short delay to avoid excessive CPU usage

def button_b3_handler():
    while True:
        if GPIO.input(BUTTON_B3_PIN) == GPIO.LOW:
            config = read_config()
            config['last_button_pressed'] = "B3"
            config['relay_state'] = "OFF"
            write_config(config)
            GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)
            print("System stopped by B3")
            time.sleep(0.5)  # Debounce delay

        time.sleep(0.1)  # Short delay to avoid excessive CPU usage

def main():
    temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0, 'light': 0.0}

    # Read initial configuration
    config = read_config()
    if config['relay_state'] == "ON":
        GPIO.output(PUMP_RELAY_PIN, GPIO.HIGH)
    else:
        GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)

    # Start threads
    sensor_thread = threading.Thread(target=sensor_loop, args=(temperatures,))
    lcd_display_thread = threading.Thread(target=lcd_display_loop, args=(temperatures,))
    control_thread = threading.Thread(target=control_loop, args=(temperatures,))
    button_b1_thread = threading.Thread(target=button_b1_handler)
    button_b2_thread = threading.Thread(target=button_b2_handler)
    button_b3_thread = threading.Thread(target=button_b3_handler)
    log_thread = threading.Thread(target=log_status, args=(temperatures,))

    # Start threads
    sensor_thread.start()
    lcd_display_thread.start()
    control_thread.start()
    button_b1_thread.start()
    button_b2_thread.start()
    button_b3_thread.start()
    log_thread.start()

    # Join threads
    sensor_thread.join()
    lcd_display_thread.join()
    control_thread.join()
    button_b1_thread.join()
    button_b2_thread.join()
    button_b3_thread.join()
    log_thread.join()

if __name__ == "__main__":
    main()
