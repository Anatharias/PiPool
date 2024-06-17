# control.py

import time
import RPi.GPIO as GPIO
from sensor import PUMP_RELAY_PIN

# Pin definitions for buttons
BUTTON_B1_PIN = 5
BUTTON_B2_PIN = 6
BUTTON_B3_PIN = 13

# Initialize buttons
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_B1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_B2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_B3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Define button event callbacks
def button_B1_pressed(channel):
    print("Button B1 pressed")

def button_B2_pressed(channel):
    print("Button B2 pressed")

def button_B3_pressed(channel):
    print("Button B3 pressed")

# Attach button event callbacks
GPIO.add_event_detect(BUTTON_B1_PIN, GPIO.FALLING, callback=button_B1_pressed, bouncetime=200)
GPIO.add_event_detect(BUTTON_B2_PIN, GPIO.FALLING, callback=button_B2_pressed, bouncetime=200)
GPIO.add_event_detect(BUTTON_B3_PIN, GPIO.FALLING, callback=button_B3_pressed, bouncetime=200)
