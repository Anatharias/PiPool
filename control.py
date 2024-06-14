from gpiozero import LED, Button

class Control:
    def __init__(self, sensor):
        self.relay = LED(17)
        self.button1 = Button(2)
        self.button2 = Button(3)
        self.button3 = Button(4)
        self.button4 = Button(5)
        self.sensor = sensor

        self.button1.when_pressed = self.handle_button1_press
        self.button2.when_pressed = self.handle_button2_press
        self.button3.when_pressed = self.handle_button3_press
        self.button4.when_pressed = self.handle_button4_press

    def handle_button1_press(self):
        if not self.relay.is_active:
            self.start_system()
        else:
            self.stop_pump()

    def handle_button2_press(self):
        if not self.relay.is_active and not self.has_sunlight():
            self.run_pump_for(5)
            self.evaluate_conditions()

    def handle_button3_press(self):
        self.stop_system()

    def handle_button4_press(self):
        self.transmit_data()

    def start_system(self):
        self.relay.on()
        # Log system start

    def stop_pump(self):
        self.relay.off()
        # Log pump stop

    def stop_system(self):
        self.relay.off()
        # Log system stop
        self.shutdown()

    def run_pump_for(self, minutes):
        self.relay.on()
        time.sleep(minutes * 60)
        self.relay.off()

    def has_sunlight(self):
        data = self.sensor.read_all()
        return data["light_intensity"] > 10000

    def evaluate_conditions(self):
        data = self.sensor.read_all()
        if data["temp_entree"] <= data["temp_air"] + 0.5:
            self.relay.on()
        else:
            self.relay.off()

    def transmit_data(self):
        # Log data transmission
        pass

    def shutdown(self):
        # Perform shutdown tasks
        pass
