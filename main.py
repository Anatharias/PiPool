# main.py

import threading
from control import control_loop
from sensor import sensor_loop
from lcd_display import lcd_display_loop

def main():
    temperatures = {'temp_E': 25.0, 'temp_A': 26.0, 'temp_S': 27.0, 'light': 0.0}

    control_thread = threading.Thread(target=control_loop)
    sensor_thread = threading.Thread(target=sensor_loop, args=(temperatures,))
    lcd_display_thread = threading.Thread(target=lcd_display_loop, args=(temperatures,))

    control_thread.start()
    sensor_thread.start()
    lcd_display_thread.start()

    control_thread.join()
    sensor_thread.join()
    lcd_display_thread.join()

if __name__ == "__main__":
    main()
