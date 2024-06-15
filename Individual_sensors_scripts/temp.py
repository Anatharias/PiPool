from w1thermsensor import W1ThermSensor, SensorNotReadyError, NoSensorFoundError

def read_all_temperatures():
    try:
        sensors = W1ThermSensor.get_available_sensors()
        for sensor in sensors:
            try:
                temperature_celsius = sensor.get_temperature()
                print(f"Température du capteur {sensor.id}: {temperature_celsius:.2f}°C")
            except SensorNotReadyError as e:
                print(f"Erreur lors de la lecture de la température depuis le capteur {sensor.id}: {e}")
    except NoSensorFoundError as e:
        print(f"Aucun capteur trouvé: {e}")

if __name__ == "__main__":
    read_all_temperatures()