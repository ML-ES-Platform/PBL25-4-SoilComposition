import paho.mqtt.client as mqtt
import time
import json
import threading
import random
import sys
from config import MQTT_PARAMS

# --- Sensor Simulation ---

def create_emulated_sensor(device_id: str):
    """
    Simulates a single IoT sensor that connects to the MQTT broker and sends data.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sensor-{device_id}")
    client.username_pw_set(MQTT_PARAMS['username'], MQTT_PARAMS['password'])
    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[Sensor {device_id}]: Connected to MQTT Broker.")
        else:
            print(f"[Sensor {device_id}]: Failed to connect, return code {rc}")

    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_PARAMS['broker'], MQTT_PARAMS['port'], 60)
    except Exception as e:
        print(f"[Sensor {device_id}]: Could not connect to MQTT broker: {e}")
        return

    client.loop_start()

    # Publishing loop
    topic = f"sensors/moisture/{device_id}"
    while True:
        try:
            moisture_value = round(random.uniform(25.0, 75.0), 2)
            payload = json.dumps({"moisture_value": moisture_value})
            
            # Publish with the retain flag set to True
            result = client.publish(topic, payload, retain=True)
            status = result[0]
            if status == 0:
                print(f"[Sensor {device_id}]: Sent `{payload}` to topic `{topic}` (Retained)")
            else:
                print(f"[Sensor {device_id}]: Failed to send message to topic `{topic}`")

            time.sleep(random.randint(8, 15)) # Send data at a random interval

        except KeyboardInterrupt:
            print(f"[Sensor {device_id}]: Simulation stopped.")
            break
        except Exception as e:
            print(f"[Sensor {device_id}]: An error occurred: {e}")
            break
            
    client.loop_stop()
    client.disconnect()


# --- Main Execution ---

if __name__ == "__main__":
    num_sensors = 2  # Default number of sensors to simulate
    if len(sys.argv) > 1:
        try:
            num_sensors = int(sys.argv[1])
            if num_sensors <= 0:
                raise ValueError()
        except (ValueError, IndexError):
            print("Invalid argument. Please provide a positive integer for the number of sensors.")
            print("Usage: python emulated_sensor.py <number_of_sensors>")
            sys.exit(1)

    print(f"Starting {num_sensors} emulated sensor(s)...")

    threads = []
    for i in range(1, num_sensors + 1):
        device_id = f"sim{i:03d}"  # e.g., sim001, sim002
        thread = threading.Thread(target=create_emulated_sensor, args=(device_id,), daemon=True)
        threads.append(thread)
        thread.start()
        time.sleep(1) # Stagger the start times slightly

    print("All sensor threads started. Press Ctrl+C to stop.")
    
    try:
        # Keep the main thread alive to listen for Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all sensors.")
        sys.exit(0) 