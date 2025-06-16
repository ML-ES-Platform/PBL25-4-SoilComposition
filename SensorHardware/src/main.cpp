#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WiFiClientSecure.h>

// --- WIFI & MQTT Configuration ---
// Wifi
#define WIFI_SSID "YOUR_WIFI_SSID"
// For open networks (no password), leave WIFI_PASSWORD as an empty string: ""
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// MQTT Broker
#define MQTT_BROKER "9e862c744fbd4909800bc2d576a7fd78.s1.eu.hivemq.cloud"
#define MQTT_PORT 8883
#define MQTT_USER "alexandrina"
#define MQTT_PASSWORD "PBL_iot_223"

// --- SENSOR Configuration ---
#define DEVICE_ID "real001" // Unique ID for this sensor
#define SOIL_MOISTURE_PIN 36
#define MQTT_TOPIC "sensors/moisture/" DEVICE_ID

// --- Global Objects ---
WiFiClientSecure espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_PUBLISH_INTERVAL 10000 // 10 seconds

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(DEVICE_ID, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  
  setup_wifi();
  
  // Point espClient to the MQTT broker
  espClient.setInsecure(); // For simplicity. For production, use certificates.
  client.setServer(MQTT_BROKER, MQTT_PORT);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > MSG_PUBLISH_INTERVAL) {
    lastMsg = now;

    // Read raw sensor value (0-4095)
    int rawValue = analogRead(SOIL_MOISTURE_PIN);
    
    // Map the raw value to a percentage (0-100%)
    // Assuming 4095 is dry and 0 is wet. You might need to calibrate these values.
    int moisturePercent = map(rawValue, 4095, 0, 0, 100);

    Serial.print("Raw Value: ");
    Serial.print(rawValue);
    Serial.print(" -> Moisture: ");
    Serial.print(moisturePercent);
    Serial.println("%");

    // Create JSON payload
    StaticJsonDocument<128> doc;
    doc["moisture_value"] = moisturePercent;

    char buffer[128];
    serializeJson(doc, buffer);

    // Publish to MQTT topic
    client.publish(MQTT_TOPIC, buffer);
    Serial.print("Published message to ");
    Serial.println(MQTT_TOPIC);
  }
}
