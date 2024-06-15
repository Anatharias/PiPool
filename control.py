import RPi.GPIO as GPIO
import time
from collections import deque
from sensor import read_all_temperatures, read_light

# Pin definitions
RELAY_PIN = 18
BUTTON_1_PIN = 27
BUTTON_2_PIN = 22
BUTTON_3_PIN = 23

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(BUTTON_1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initial states
relay_state = GPIO.LOW
previous_button_1_state = GPIO.HIGH
previous_button_2_state = GPIO.HIGH
previous_button_3_state = GPIO.HIGH

# Initialize variables for moving average
lum_values = deque(maxlen=300)  # Store 300 values (5 minutes if read every second)
temp_Sortie_values = deque(maxlen=300)  # Store 300 values for temperature
time_since_last_check = 0

def relay_on():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Relay ON")

def relay_off():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Relay OFF")

def read_buttons():
    global previous_button_1_state, previous_button_2_state, previous_button_3_state, relay_state
    button_1_state = GPIO.input(BUTTON_1_PIN)
    button_2_state = GPIO.input(BUTTON_2_PIN)
    button_3_state = GPIO.input(BUTTON_3_PIN)

    # Button 1: Toggle relay state
    if button_1_state == GPIO.LOW and previous_button_1_state == GPIO.HIGH:
        if relay_state == GPIO.LOW:
            relay_on()
            relay_state = GPIO.HIGH
        else:
            relay_off()
            relay_state = GPIO.LOW
        previous_button_1_state = GPIO.LOW
    elif button_1_state == GPIO.HIGH:
        previous_button_1_state = GPIO.HIGH

    # Button 2: Start pump for 5 minutes if no sunlight
    if button_2_state == GPIO.LOW and previous_button_2_state == GPIO.HIGH:
        if relay_state == GPIO.LOW:
            light_level = read_light()
            if light_level < 10000:  # Define threshold_no_sun appropriately
                relay_on()
                time.sleep(300)  # Run pump for 5 minutes
                relay_off()
        previous_button_2_state = GPIO.LOW
    elif button_2_state == GPIO.HIGH:
        previous_button_2_state = GPIO.HIGH

    # Button 3: Stop the system immediately
    if button_3_state == GPIO.LOW and previous_button_3_state == GPIO.HIGH:
        relay_off()
        relay_state = GPIO.LOW
        previous_button_3_state = GPIO.LOW
    elif button_3_state == GPIO.HIGH:
        previous_button_3_state = GPIO.HIGH

def log_decision(message):
    with open("control_log.txt", "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def control_loop():
    global time_since_last_check
    try:
        while True:
            read_buttons()
            light_level = read_light()
            lum_values.append(light_level)
            time.sleep(1)

            # Update the moving average every second
            moy_lum_5min = sum(lum_values) / len(lum_values)

            # Check conditions every 5 minutes
            time_since_last_check += 1
            if time_since_last_check >= 300:
                temperatures = read_all_temperatures()
                temp_Entree = temperatures.get('temp_E')
                temp_Sortie = temperatures.get('temp_S')
                temp_Air = temperatures.get('temp_A')

                temp_Sortie_values.append(temp_Sortie)
                mean_temp_Sortie_5min = sum(temp_Sortie_values) / len(temp_Sortie_values)

                if moy_lum_5min > 10000:  # Sunshine condition
                    relay_on()
                    log_decision("Sunshine detected, running pump.")
                    time.sleep(360)  # Wait 6 minutes to replace water in collectors
                    temp_Sortie = temperatures.get('temp_S')
                    temp_Entree = temperatures.get('temp_E')
                    temp_diff = mean_temp_Sortie_5min - temp_Entree

                    if temp_Entree <= mean_temp_Sortie_5min + 0.5:
                        relay_on()
                        log_decision("Temperature difference acceptable, keeping pump on.")
                    else:
                        relay_off()
                        log_decision("Temperature difference too high, stopping pump.")
                        if temp_diff <= 0.3:
                            log_decision("Waiting for 10 minutes.")
                            time.sleep(600)  # Wait for 10 minutes
                            relay_on()
                            time.sleep(360)  # Run pump for 6 minutes and check again
                        elif 0.4 <= temp_diff <= 0.5:
                            log_decision("Waiting for 10 minutes.")
                            time.sleep(600)  # Wait for 10 minutes
                            relay_on()
                            time.sleep(300)  # Run pump for 5 minutes and check again

                elif temp_Entree < temp_Air:
                    relay_on()
                    log_decision("Running pump for 5 minutes as temp_Entree < temp_Air.")
                    time.sleep(300)  # Run pump for 5 minutes
                    relay_off()
                    log_decision("Waiting for 60 minutes.")
                    time.sleep(3600)  # Wait for 60 minutes

                else:
                    relay_off()
                    log_decision("Conditions not met, stopping pump.")

                time_since_last_check = 0

    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    control_loop()