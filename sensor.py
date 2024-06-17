# sensor.py
#BH1750 for sun brightness
#DS18B20 for temperature

import time
from w1thermsensor import W1ThermSensor
from bh1750 import BH1750

# Initialize temperature sensors
sensor_E = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "0000006bbe43")
sensor_A = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "0000006b6275")
sensor_S = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "00000069d1fe")

# Initialize light sensor
light_sensor = BH1750()

def get_temperature_data():
    temp_E = sensor_E.get_temperature()
    temp_A = sensor_A.get_temperature()
    temp_S = sensor_S.get_temperature()
    return {'temp_E': temp_E, 'temp_A': temp_A, 'temp_S': temp_S}

def get_light_level():
    return light_sensor.luminance(BH1750.ONCE_HIRES_1)

def sensor_loop(temperatures):
    while True:
        temp_data = get_temperature_data()
        light_level = get_light_level()
        temperatures.update(temp_data)
        temperatures['light'] = light_level
        time.sleep(1)  # Update sensor data every second
