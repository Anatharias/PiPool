# sensor.py
# BH1750 for sun brightness
# DS18B20 for temperature

import time
from w1thermsensor import W1ThermSensor
import smbus

# Initialize temperature sensors
sensor_E = W1ThermSensor("0000006bbe43")
sensor_A = W1ThermSensor("0000006b6275")
sensor_S = W1ThermSensor("00000069d1fe")

# Initialize light sensor
DEVICE = 0x23  # I2C address of BH1750
ONE_TIME_HIGH_RES_MODE_1 = 0x20  # Command for BH1750
bus = smbus.SMBus(1)  # Use 0 for Raspberry Pi Rev 1

# Get temperature data
def get_temperature_data():
    temp_E = sensor_E.get_temperature()
    temp_A = sensor_A.get_temperature()
    temp_S = sensor_S.get_temperature()
    return {'temp_E': temp_E, 'temp_A': temp_A, 'temp_S': temp_S}

# Convert raw data to lux
def convert_to_number(data):
    result = (data[1] + (256 * data[0])) / 1.2
    return result

# Read light level from BH1750
def get_light_level(addr=DEVICE):
    data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
    return convert_to_number(data)

def sensor_loop(temperatures):
    while True:
        temp_data = get_temperature_data()
        light_level = get_light_level()
        temperatures.update(temp_data)
        temperatures['light'] = light_level
        time.sleep(1)  # Update sensor data every second
