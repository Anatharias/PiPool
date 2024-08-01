from w1thermsensor import W1ThermSensor

class TempSensor:
    def __init__(self, sensor_id, temp_delta_threshold):
        self.sensor = W1ThermSensor(sensor_id=sensor_id)
        self.temp_delta_threshold = temp_delta_threshold

    def get_temperature(self):
        try:
            return self.sensor.get_temperature()
        except Exception as e:
            return None

    def is_temp_above_threshold(self, temp_E, temp_S, temp_A):
        """
        Vérifie les conditions suivantes :
        - La température d'entrée (temp_E) est-elle inférieure à la température de sortie (temp_S) diminuée de temp_delta_threshold ?
        - La température ambiante (temp_A) est-elle supérieure à la température d'entrée (temp_E) ?
        """
        if temp_E is None or temp_S is None or temp_A is None:
            return None, None

        is_below_threshold = temp_E < (temp_S - self.temp_delta_threshold)
        is_above_temp_E = temp_A > temp_E
        
        return is_below_threshold, is_above_temp_E