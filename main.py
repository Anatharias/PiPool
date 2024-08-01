import time
import threading
import logging
import RPi.GPIO as GPIO
from lcd_display import LCDManager
from light import LightSensor
from temperature import TempSensor
from typing import Dict, Any

def load_config(file_path: str) -> Dict[str, Any]:
    import json
    with open(file_path, 'r') as f:
        return json.load(f)

def write_config(config: Dict[str, Any], file_path: str) -> None:
    import json
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=2)

class PoolControlSystem:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = load_config(config_file)
        self.lcd_manager = LCDManager(self.config)
        self.light_sensor = LightSensor(self.config)
        self.temp_sensor_E = TempSensor(self.config['sensors']['temperature']['displays']['E']['id'], self.config['temp_delta_threshold'])
        self.temp_sensor_S = TempSensor(self.config['sensors']['temperature']['displays']['S']['id'], self.config['temp_delta_threshold'])
        self.temp_sensor_A = TempSensor(self.config['sensors']['temperature']['displays']['A']['id'], self.config['temp_delta_threshold'])
        self.running = True
        self.pump_running = False
        self.last_action_reason = "System initialized"
        self.analysis_start_time = 0
        self.water_replace_start_time = 0
        self.setup_logging()
        self.setup_gpio()

    def setup_logging(self):
        logging.basicConfig(
            filename='pool_control.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.config['gpio']['button_b1_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.config['gpio']['button_b2_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.config['gpio']['pump_relay_pin'], GPIO.OUT)

    def initial_pump_run(self):
        logging.info("Starting initial pump run.")
        self.start_pump("Initial pump run")
        time.sleep(self.config['water_replace_time'])
        self.stop_pump("Initial pump run completed")

    def start_pump(self, reason: str):
        self.pump_running = True
        GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.HIGH)
        self.last_action_reason = reason
        self.config['last_pump_start_time'] = time.time()
        logging.info(f"Pump started: {reason}")

    def stop_pump(self, reason: str):
        self.pump_running = False
        GPIO.output(self.config['gpio']['pump_relay_pin'], GPIO.LOW)
        self.last_action_reason = reason
        logging.info(f"Pump stopped: {reason}")

    def button_handler(self):
        while self.running:
            if GPIO.input(self.config['gpio']['button_b1_pin']) == GPIO.LOW:
                self.button_b1_action()
                time.sleep(0.3)  # Debounce delay
            elif GPIO.input(self.config['gpio']['button_b2_pin']) == GPIO.LOW:
                self.button_b2_action()
                time.sleep(0.3)  # Debounce delay

    def button_b1_action(self):
        logging.info("B1 pressed: Starting initial pump run")
        self.initial_pump_run()

    def button_b2_action(self):
        logging.info("B2 pressed: Stopping pump and scheduling next run")
        self.stop_pump("B2 pressed")
        # Schedule next run for 10 AM tomorrow
        next_run_time = time.time() + (24 * 60 * 60)  # 24 hours from now
        next_run_time -= next_run_time % (24 * 60 * 60)  # Round down to midnight
        next_run_time += 10 * 60 * 60  # Add 10 hours (10 AM)
        self.config['next_scheduled_run'] = next_run_time
        write_config(self.config, self.config_file)

    def check_scheduled_run(self):
        if 'next_scheduled_run' in self.config:
            if time.time() >= self.config['next_scheduled_run']:
                logging.info("Executing scheduled pump run")
                self.initial_pump_run()
                del self.config['next_scheduled_run']
                write_config(self.config, self.config_file)

    def check_pump_conditions(self):
        temp_E = self.temp_sensor_E.get_temperature()
        temp_S = self.temp_sensor_S.get_temperature()
        temp_A = self.temp_sensor_A.get_temperature()
        
        is_temp_below_threshold, is_ambient_above_temp_E = self.temp_sensor_E.is_temp_above_threshold(temp_E, temp_S, temp_A)
        
        is_light_sufficient = self.light_sensor.is_average_light_sufficient()

        self.log_status(temp_E, temp_S, temp_A, is_light_sufficient, is_temp_below_threshold, is_ambient_above_temp_E)

        current_time = time.time()

        if is_ambient_above_temp_E:
            if self.analysis_start_time == 0:
                self.stop_pump("Starting analysis period")
                self.analysis_start_time = current_time
            elif current_time - self.analysis_start_time >= self.config['analysis_interval']:
                if self.water_replace_start_time == 0:
                    self.start_pump("Analysis period completed, starting water replacement")
                    self.water_replace_start_time = current_time
                elif current_time - self.water_replace_start_time >= self.config['water_replace_time']:
                    self.stop_pump("Water replace time completed")
                    self.water_replace_start_time = 0
                    self.analysis_start_time = 0
        else:
            if self.pump_running:
                self.stop_pump("Ambient temperature not above pool temperature")
            self.water_replace_start_time = 0
            self.analysis_start_time = 0

        if is_light_sufficient and not self.pump_running and self.analysis_start_time == 0:
            self.start_pump("Light conditions met")

        if not self.pump_running and current_time - self.config['last_pump_start_time'] >= self.config['analysis_interval']:
            self.initial_pump_run()

    def log_status(self, temp_E, temp_S, temp_A, is_light_sufficient, is_temp_below_threshold, is_ambient_above_temp_E):
        current_time = time.time()
        status = f"""
        Status Update:
        Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
        Pump Running: {self.pump_running}
        Last Action: {self.last_action_reason}
        Temperatures:
            E (Pool Water): {temp_E:.2f}°C
            S (Solar Collector): {temp_S:.2f}°C
            A (Ambient): {temp_A:.2f}°C
        Average Light Sufficient: {is_light_sufficient}
        Temperature Conditions:
            E Below S - Threshold: {is_temp_below_threshold}
            A Above E: {is_ambient_above_temp_E}
        Time since last pump start: {current_time - self.config['last_pump_start_time']:.2f} seconds
        Analysis period: {"In progress" if self.analysis_start_time > 0 else "Not active"}
        Water replacement: {"In progress" if self.water_replace_start_time > 0 else "Not active"}
        """
        logging.info(status)
        print(status)  # Also print to console for real-time monitoring


    def update_lcd(self):
        while self.running:
            temps = {
                'pool_water': self.temp_sensor_E.get_temperature(),
                'solar_collector_output': self.temp_sensor_S.get_temperature(),
                'ambient': self.temp_sensor_A.get_temperature()
            }
            self.lcd_manager.update_displays(temps)
            time.sleep(self.config['sensors']['temperature']['update_interval'])

    def run(self):
        self.initial_pump_run()
        
        threads = [
            threading.Thread(target=self.button_handler),
            threading.Thread(target=self.update_lcd)
        ]
        
        for thread in threads:
            thread.start()

        try:
            while self.running:
                self.check_scheduled_run()
                self.check_pump_conditions()
                time.sleep(self.config['log_interval'])
        except KeyboardInterrupt:
            self.running = False
            logging.info("System shutdown initiated by user")
        finally:
            for thread in threads:
                thread.join()
            GPIO.cleanup()
            logging.info("System shutdown complete")

if __name__ == "__main__":
    pool_control = PoolControlSystem('config.json')
    pool_control.run()