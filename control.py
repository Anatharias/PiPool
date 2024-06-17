import time
from gpiozero import OutputDevice
from sensor import get_temperature_data, get_light_level

# Pin definition for the relay controlling the pump
PUMP_RELAY_PIN = 18
pump_relay = OutputDevice(PUMP_RELAY_PIN)

# Threshold values
LIGHT_THRESHOLD = 10000
TEMP_DELTA_THRESHOLD = 0.5

# Global variables to track time-based conditions
light_below_threshold_start_time = None
light_above_threshold_start_time = None
last_temp_check_time = 0
last_ambient_check_time = 0

def should_pump_run(temperatures, current_time):
    global light_below_threshold_start_time, light_above_threshold_start_time
    global last_temp_check_time, last_ambient_check_time

    light_level = get_light_level()
    pool_temp = temperatures['temp_E']
    ambient_temp = temperatures['temp_A']
    solar_collector_temp = temperatures['temp_S']

    # Check light level
    if light_level < LIGHT_THRESHOLD:
        if light_below_threshold_start_time is None:
            light_below_threshold_start_time = current_time
        elif current_time - light_below_threshold_start_time >= 300:  # 5 minutes
            light_above_threshold_start_time = None  # Reset the above threshold timer
            return False
    else:
        light_below_threshold_start_time = None
        if light_above_threshold_start_time is None:
            light_above_threshold_start_time = current_time
        elif current_time - light_above_threshold_start_time >= 300:  # 5 minutes
            if current_time - last_temp_check_time >= 600:  # 10 minutes interval
                pump_relay.on()
                time.sleep(300)  # Run pump for 5 minutes to check temp
                temperatures.update(get_temperature_data())
                solar_collector_temp = temperatures['temp_S']
                last_temp_check_time = current_time

            if (solar_collector_temp - pool_temp) > TEMP_DELTA_THRESHOLD:
                return True
            return False

    # Check ambient temperature
    if ambient_temp > pool_temp and light_level < LIGHT_THRESHOLD:
        if current_time - last_ambient_check_time >= 1200:  # 20 minutes
            pump_relay.on()
            time.sleep(300)  # Run pump for 5 minutes
            last_ambient_check_time = current_time
            return False  # Ensure pump is off after running for 5 minutes

    return False

def control_loop(temperatures, control_state):
    while True:
        if control_state['running']:
            current_time = time.time()
            if should_pump_run(temperatures, current_time):
                pump_relay.on()
            else:
                pump_relay.off()
        time.sleep(60)  # Check every minute
