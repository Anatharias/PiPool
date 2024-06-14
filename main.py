#will be used to store the main component of the pipool script
import time
from sensor import Sensor
from control import Control
from thingsboard import ThingsBoard
from error_handler import ErrorHandler

def main():
    sensor = Sensor()
    control = Control(sensor)
    thingsboard = ThingsBoard()
    error_handler = ErrorHandler()

    try:
        while True:
            try:
                # Read sensor data
                sensor_data = sensor.read_all()
                # Log sensor data to ThingsBoard
                thingsboard.log_data(sensor_data)
                # Perform control logic
                control.evaluate_conditions()
                # Sleep for 15 seconds before the next loop
                time.sleep(15)
            except Exception as e:
                error_handler.handle_error(e)
    except KeyboardInterrupt:
        print("System shutdown initiated.")
        control.shutdown()

if __name__ == "__main__":
    main()
