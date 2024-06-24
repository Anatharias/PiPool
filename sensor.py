import time
from w1thermsensor import W1ThermSensor, NoSensorFoundError
import smbus

# Initialize temperature sensors
try:
    sensor_E = W1ThermSensor(sensor_id="0000006bbe43")
    sensor_A = W1ThermSensor(sensor_id="0000006b6275")
    sensor_S = W1ThermSensor(sensor_id="00000069d1fe")
except NoSensorFoundError as e:
    print(f"Error initializing temperature sensors: {e}")
    exit(1)

# Initialize light sensor
DEVICE = 0x23  # I2C address of BH1750
ONE_TIME_HIGH_RES_MODE_1 = 0x20  # Command for BH1750
bus = smbus.SMBus(1)  # Use 0 for Raspberry Pi Rev 1

# Get temperature data
def get_temperature_data():
    try:
        temp_E = sensor_E.get_temperature()
        temp_A = sensor_A.get_temperature()
        temp_S = sensor_S.get_temperature()
    except NoSensorFoundError as e:
        print(f"Error reading temperature data: {e}")
        return {'temp_E': None, 'temp_A': None, 'temp_S': None}
    return {'temp_E': temp_E, 'temp_A': temp_A, 'temp_S': temp_S}

# Convert raw data to lux
def convert_to_number(data):
    try:
        result = (data[1] + (256 * data[0])) / 1.2
    except IndexError as e:
        print(f"Error converting light data: {e}")
        return None
    return result

# Read light level from BH1750
def get_light_level(addr=DEVICE):
    try:
        data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
    except IOError as e:
        print(f"Error reading light level: {e}")
        return None
    return convert_to_number(data)

def sensor_loop(temperatures):
    while True:
        temp_data = get_temperature_data()
        light_level = get_light_level()
        temperatures.update(temp_data)
        temperatures['light'] = light_level
        time.sleep(1)  # Update sensor data every second

# Example usage
if __name__ == "__main__":
    temperatures = {}
    sensor_loop(temperatures)
