import paho.mqtt.client as mqtt
import time
import json
import threading
import random
import sys
import argparse
from config import MQTT_PARAMS

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
            # Simulate a plausible moisture range, e.g., 20% to 80%
            # with occasional spikes to test boundaries (0-100%).
            if random.random() < 0.05:  # 5% chance of an extreme value
                moisture_value = round(random.uniform(0, 100), 2)
            else:
                moisture_value = round(random.uniform(20, 80), 2)
            
            payload = json.dumps({"moisture_value": moisture_value})
            
            # Publish with the retain flag set to True
            result = client.publish(topic, payload, retain=True)
            status = result[0]
            if status == 0:
                print(f"[Sensor {device_id}]: Sent `{payload}` to topic `{topic}` (Retained)")
            else:
                print(f"[Sensor {device_id}]: Failed to send message to topic `{topic}`")

            # Send data at a random interval
            time.sleep(random.randint(8, 15))

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
    parser = argparse.ArgumentParser(
        description="Emulated IoT Sensor",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Usage examples:
  # Start 2 emulated sensors (default)
  python emulated_sensor.py

  # Start 5 emulated sensors
  python emulated_sensor.py 5
"""
    )
    parser.add_argument(
        "number_of_sensors", 
        type=int, 
        nargs="?", 
        default=2, 
        help="Number of sensors to simulate (default: 2)"
    )
    args = parser.parse_args()

    num_sensors = args.number_of_sensors
    if num_sensors <= 0:
        print("Invalid argument. Please provide a positive integer for the number of sensors.")
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
        # Threads are daemons, so they will exit automatically
        sys.exit(0) 