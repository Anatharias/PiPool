import sensor_utils
import time

while True:
    sensor_utils.update_relay()
    sensor_utils.check_button_B1()
    sensor_utils.check_button_B2()
    sensor_utils.check_button_B3()
    sensor_utils.update_web_page()
    time.sleep(1)
