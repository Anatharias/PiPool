# thingsboard.py

import time
import json
from tb_device_mqtt import TBDeviceMqttClient, TBPublishInfo

# Configuration des identifiants et du serveur de ThingsBoard
THINGSBOARD_HOST = '192.168.2.99:8765'  # Remplacez par l'adresse de votre serveur ThingsBoard
ACCESS_TOKEN = 'your-access-token'  # Remplacez par le jeton d'accès de votre appareil

client = TBDeviceMqttClient(THINGSBOARD_HOST, ACCESS_TOKEN)
client.connect()

def send_telemetry(data):
    result = client.send_telemetry(json.dumps(data))
    success = result.get() == TBPublishInfo.TB_ERR_SUCCESS
    if success:
        print(f"Télémetrie envoyée: {data}")
    else:
        print(f"Erreur lors de l'envoi de la télémetrie: {data}")

def thingsboard_loop():
    try:
        while True:
            # Exemple de données à envoyer à ThingsBoard
            data = {
                "temperature_E": 23.5,
                "temperature_A": 24.0,
                "temperature_S": 22.8,
                "light": 350
            }
            send_telemetry(data)
            time.sleep(5)  # Attendre 5 secondes avant d'envoyer les prochaines données
    except KeyboardInterrupt:
        client.disconnect()

if __name__ == "__main__":
    thingsboard_loop()
