import time
import threading
from gpiozero import Button, OutputDevice
from control import PUMP_RELAY_PIN

# Pin definitions for buttons
BUTTON_B1_PIN = 5
BUTTON_B2_PIN = 6
BUTTON_B3_PIN = 13

# Initialize buttons
button_B1 = Button(BUTTON_B1_PIN)
button_B2 = Button(BUTTON_B2_PIN)
button_B3 = Button(BUTTON_B3_PIN)

# Initialize pump relay
pump_relay = OutputDevice(PUMP_RELAY_PIN)

# State tracking
button_B1_state = False
button_B1_disabled = False
button_B2_pressed_time = None

def button_control_loop(control_state):
    global button_B1_state, button_B1_disabled, button_B2_pressed_time

    while True:
        if button_B1.is_pressed:
            if not button_B1_state:
                if not button_B1_disabled:
                    control_state['running'] = not control_state['running']
                    if control_state['running']:
                        print("System started")
                    else:
                        pump_relay.off()
                        print("Pump stopped")
                    button_B1_state = True
                else:
                    print("Button B1 is disabled until B3 is pressed")
            else:
                button_B1_state = False

        if button_B2.is_pressed:
            if not control_state['running']:
                if button_B2_pressed_time is None:
                    button_B2_pressed_time = time.time()
                if time.time() - button_B2_pressed_time >= 300:  # 5 minutes
                    pump_relay.on()
                    time.sleep(300)  # Run pump for 5 minutes
                    pump_relay.off()
                    control_state['running'] = should_pump_run(temperatures, time.time())
                    button_B2_pressed_time = None

        if button_B3.is_pressed:
            control_state['running'] = False
            pump_relay.off()
            print("System stopped by B3")
            button_B1_disabled = False  # Re-enable B1 after B3 is pressed
            time.sleep(0.5)  # Debounce delay

        time.sleep(0.1)  # Short delay to avoid excessive CPU usage
