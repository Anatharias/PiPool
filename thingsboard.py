import paho.mqtt.client as mqtt

class ThingsBoard:
    def __init__(self):
        self.THINGSBOARD_HOST = 'YOUR_THINGSBOARD_HOST'
        self.ACCESS_TOKEN = 'YOUR_DEVICE_ACCESS_TOKEN'
        self.client = mqtt.Client()
        self.client.username_pw_set(self.ACCESS_TOKEN)
        self.client.connect(self.THINGSBOARD_HOST, 1883, 60)
        self.client.loop_start()

    def log_data(self, data):
        self.client.publish('v1/devices/me/telemetry', data)
