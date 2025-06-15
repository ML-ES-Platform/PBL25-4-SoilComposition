# Soil Moisture IoT Dashboard

This project is a complete IoT solution for monitoring soil moisture levels using an ESP32 sensor, an MQTT broker for data transmission, a Flask backend for data processing, and a React frontend for visualization.

![Dashboard Screenshot](https://i.imgur.com/L8zBqfF.png)

---

## Architecture

The system follows a modern, decoupled architecture suitable for IoT applications:

-   **Sensor (Publisher):** An ESP32 microcontroller running C++ code reads moisture data and publishes it to a specific MQTT topic. An emulated sensor script is also provided for testing without hardware.
-   **MQTT Broker (HiveMQ Cloud):** A central, cloud-based broker that receives data from all sensors. This decouples the sensors from the backend.
-   **Backend (Subscriber/API):** A Python Flask application that:
    -   Subscribes to the MQTT broker to receive sensor data in real-time.
    -   Stores the data in a PostgreSQL database.
    -   Provides a REST API for the frontend to fetch historical and predicted data.
-   **Frontend (Client):** A React (TypeScript + Vite) single-page application that:
    -   Provides a real-time dashboard with current readings and historical data graphs.
    -   Dynamically populates a dropdown menu to allow viewing data from multiple sensors.

---

## Features

-   Real-time moisture level display.
-   Historical data visualization (Last 12 hours, Last 24 hours, Last 7 days).
-   Predictive analysis for the next 12 hours.
-   Support for multiple sensors with a dynamic selector.
-   Scalable and robust MQTT-based architecture.
-   Sensor emulator for development and testing.

---

## Setup and Installation

### Prerequisites

-   [Node.js](https://nodejs.org/en/) (v18 or later)
-   [Python](https://www.python.org/downloads/) (v3.9 or later)
-   [PostgreSQL](https://www.postgresql.org/download/)
-   A free [HiveMQ Cloud](https://www.hivemq.com/cloud/) account.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd PBL25-4-SoilComposition
```

### 2. Backend Setup

**a. Navigate to the Backend Directory:**
```bash
cd Backend
```

**b. Create a Virtual Environment (Recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

**c. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**d. Configure Credentials:**
Create a file named `config.py` by copying the provided example file:
```bash
# For Windows
copy config.py.example config.py

# For macOS/Linux
cp config.py.example config.py
```
Now, open `config.py` and fill in your actual credentials for your PostgreSQL database and your HiveMQ Cloud cluster. The `dbname` you choose will be created in the next step.

**e. Setup the Database:**

Once you have configured your `config.py` with your desired database name and superuser credentials (like the default `postgres` user), run the initialization script. This will create the database and the required `moisture_data` table for you.

```bash
# From the /Backend directory
python init_db.py
```

**f. Populate with Sample Data (Optional):**

To see the historical graphs working immediately, you can populate the database with sample data from the last 7 days. Make sure your backend is **not** running, then run the following script:

```bash
# From the /Backend directory
python insert_historical_data.py
```
This will fill your database with realistic historical data.

### 3. Frontend Setup

**a. Navigate to the Frontend Directory:**
```bash
cd ../Frontend 
```

**b. Install Dependencies:**
```bash
npm install
```

---

## Hardware Setup (ESP32 Sensor)

This section details how to set up the physical ESP32 sensor.

### 1. Arduino IDE Setup

a.  Download and install the [Arduino IDE](https://www.arduino.cc/en/software).
b.  Add the ESP32 board manager to the IDE. Go to `File > Preferences` and add the following URL to the "Additional Board Manager URLs" field:
    ```
    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
    ```
c.  Go to `Tools > Board > Boards Manager`, search for "esp32", and install the package by Espressif Systems.
d.  Select your specific ESP32 board from the `Tools > Board` menu (e.g., "ESP32 Dev Module").

### 2. Required Libraries

Install the following libraries from the Arduino IDE's Library Manager (`Tools > Manage Libraries...`):

-   `PubSubClient` by Nick O'Leary
-   `ArduinoJson` by Benoit Blanchon

### 3. Sensor Code

Open the file `SensorHardware/src/main.cpp` in the Arduino IDE or your preferred text editor.

### 4. Update Credentials and Flash

a.  **Fill in your details:** In `SensorHardware/src/main.cpp`, replace the placeholder values for `WIFI_SSID`, `WIFI_PASSWORD`, `MQTT_BROKER`, `MQTT_USERNAME`, and `MQTT_PASSWORD` with your own credentials.
b.  **Set a Unique `DEVICE_ID`:** Give your sensor a unique name, like `"sensor-patio"` or `"sensor-office-plant"`.
c.  **Calibrate Your Sensor:** The line `map(rawValue, 4095, 1500, 0, 100)` is critical. You must test your sensor in completely dry soil and fully saturated soil to find your own `dryValue` and `wetValue` to replace `4095` and `1500` for accurate readings.

Once flashed, your physical sensor will start sending data to the dashboard.

---

## Running the Application

You will need to run three separate processes in three different terminals.

### Terminal 1: Run the Backend

```bash
cd Backend
python app.py
```
The backend server will start and connect to the MQTT broker.

### Terminal 2: Run the Frontend

```bash
cd Frontend
npm run dev
```
The application will be available at `http://localhost:5173` (or the URL provided in the terminal).

### Terminal 3: Run the Emulated Sensor (for testing)

```bash
cd Backend
python emulated_sensor.py <number_of_sensors>
```
For example, to simulate one sensor: `python emulated_sensor.py 1`
To simulate three sensors: `python emulated_sensor.py 3`

You can now view the live data on the dashboard in your browser.
