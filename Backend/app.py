import psycopg2
from psycopg2 import sql
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import logging
import os
from datetime import datetime, timedelta
from config import DB_PARAMS, MQTT_PARAMS
import paho.mqtt.client as mqtt
import json
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('flask_errors.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(**DB_PARAMS)

def insert_moisture_data(device_id, moisture_value):
    """Inserts a new moisture reading into the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO moisture_data (device_id, moisture_value) VALUES (%s, %s)"
        cursor.execute(query, (device_id, float(moisture_value)))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Inserted data for device_id: {device_id}, value: {moisture_value}")
    except psycopg2.Error as e:
        logger.error(f"Database insert error: {e}")
    except Exception as e:
        logger.error(f"Error inserting data: {e}")

# --- MQTT Client Setup ---
def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
        client.subscribe(MQTT_PARAMS['topic'])
        logger.info(f"Subscribed to topic: {MQTT_PARAMS['topic']}")
    else:
        logger.error(f"Failed to connect, return code {rc}\n")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the broker."""
    try:
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 3:
            device_id = topic_parts[-1]
            payload = json.loads(msg.payload.decode())
            moisture_value = payload.get('moisture_value')
            
            if moisture_value is not None:
                insert_moisture_data(device_id, moisture_value)
            else:
                logger.warning(f"Message from {device_id} is missing 'moisture_value'")
        else:
            logger.warning(f"Received message on unexpected topic: {msg.topic}")
            
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from topic {msg.topic}: {msg.payload.decode()}")
    except Exception as e:
        logger.error(f"Error processing message from topic {msg.topic}: {e}")

def setup_mqtt_client():
    """Configures and starts the MQTT client."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_PARAMS['username'], MQTT_PARAMS['password'])
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Setup TLS for secure connection
    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
    
    try:
        client.connect(MQTT_PARAMS['broker'], MQTT_PARAMS['port'], 60)
        client.loop_start() # Starts a background thread to handle network traffic
        return client
    except Exception as e:
        logger.error(f"Could not connect to MQTT broker: {e}")
        return None

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """Returns a list of unique sensor IDs that have sent data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT device_id FROM moisture_data ORDER BY device_id")
        sensors = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(sensors)
    except Exception as e:
        logger.error(f"API Error in /api/sensors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/moisture/<device_id>', methods=['GET'])
def get_moisture(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"Fetching current moisture for device_id: {device_id}")
        cursor.execute("""
            SELECT moisture_value, timestamp FROM moisture_data
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (device_id,))
        current = cursor.fetchone()
        current_value = float(current[0]) if current else None
        current_timestamp = current[1] if current else None
        
        logger.info(f"Fetching previous moisture for device_id: {device_id}")
        cursor.execute("""
            SELECT moisture_value FROM moisture_data
            WHERE device_id = %s AND timestamp < %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (device_id, current_timestamp))
        last_hour = cursor.fetchone()
        last_hour_value = float(last_hour[0]) if last_hour else None
        
        if current_timestamp:
            target_hour = current_timestamp.hour
            three_days_ago = current_timestamp - timedelta(days=3)
            logger.info(f"Fetching average for hour {target_hour} over last 3 days for device_id: {device_id}")
            cursor.execute("""
                SELECT AVG(moisture_value) FROM moisture_data
                WHERE device_id = %s
                AND timestamp >= %s
                AND EXTRACT(HOUR FROM timestamp) = %s
            """, (device_id, three_days_ago, target_hour))
            avg_last_3_days = cursor.fetchone()
            avg_last_3_days_value = float(avg_last_3_days[0]) if avg_last_3_days[0] else None
            
            if avg_last_3_days_value and current_value:
                next_hour_value = (avg_last_3_days_value + current_value) / 2
            else:
                next_hour_value = current_value
        else:
            next_hour_value = None
        
        logger.info(f"Returning data for {device_id}: last_hour={last_hour_value}, current={current_value}, next_hour={next_hour_value}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'last_hour': round(last_hour_value, 2) if last_hour_value else None,
            'current': round(current_value, 2) if current_value else None,
            'next_hour': round(next_hour_value, 2) if next_hour_value else None
        })
        
    except psycopg2.Error as e:
        logger.error(f"Database error during fetch: {e}")
        return jsonify({'error': f"Database error: {e}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        return jsonify({'error': f"Error: {e}"}), 500

@app.route('/api/moisture/<device_id>/last12h', methods=['GET'])
def get_last_12h(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(timestamp) FROM moisture_data WHERE device_id = %s", (device_id,))
        latest_timestamp = cursor.fetchone()[0]

        if not latest_timestamp:
            return jsonify([]), 200

        twelve_hours_before_latest = latest_timestamp - timedelta(hours=12)

        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= %s AND timestamp <= %s
            GROUP BY hour_bucket ORDER BY hour_bucket ASC
        """, (device_id, twelve_hours_before_latest, latest_timestamp))
        
        data = cursor.fetchall()
        result = [{'value': round(float(row[0]), 2), 'timestamp': row[1].strftime('%H:%M')} for row in data]
        
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        logger.error(f"API Error in /last12h: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/moisture/<device_id>/last1h', methods=['GET'])
def get_last_1h(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sixty_minutes_ago = datetime.utcnow() - timedelta(hours=1)

        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   DATE_TRUNC('minute', timestamp) as minute_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= %s
            GROUP BY minute_bucket 
            ORDER BY minute_bucket ASC
        """, (device_id, sixty_minutes_ago))
        
        data = cursor.fetchall()
        result = [{'value': round(float(row[0]), 2), 'timestamp': row[1].strftime('%H:%M')} for row in data]
        
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        logger.error(f"API Error in /last1h: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/moisture/<device_id>/last24h', methods=['GET'])
def get_last_24h(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"Fetching last 24 hours data for device_id: {device_id}")

        cursor.execute("SELECT MAX(timestamp) FROM moisture_data WHERE device_id = %s", (device_id,))
        latest_timestamp = cursor.fetchone()[0]

        if not latest_timestamp:
            logger.info(f"No data found for device_id: {device_id}")
            return jsonify([]), 200
        
        twenty_four_hours_ago = latest_timestamp - timedelta(hours=24)
        
        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= %s AND timestamp <= %s
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour_bucket ASC
        """, (device_id, twenty_four_hours_ago, latest_timestamp))
        data = cursor.fetchall()
        
        result = [
            {
                'value': round(float(row[0]), 2) if row[0] is not None else None,
                'timestamp': row[1].strftime('%H:%M')
            } for row in data
        ]
        
        logger.info(f"Returning {len(result)} data points for last 24 hours")
        
        cursor.close()
        conn.close()
        return jsonify(result)
        
    except psycopg2.Error as e:
        logger.error(f"Database error during last 24h fetch: {e}")
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during last 24h fetch: {e}")
        return jsonify({'error': f"Error: {str(e)}"}), 500

@app.route('/api/moisture/<device_id>/last7d', methods=['GET'])
def get_last_7d(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"Fetching last 7 days data for device_id: {device_id}")
        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   DATE(timestamp) as day_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(timestamp)
            ORDER BY day_bucket ASC
        """, (device_id,))
        data = cursor.fetchall()
        
        result = [
            {
                'value': round(float(row[0]), 2) if row[0] is not None else None,
                'timestamp': row[1].strftime('%Y-%m-%d')
            } for row in data
        ]
        
        logger.info(f"Returning {len(result)} data points for last 7 days")
        
        cursor.close()
        conn.close()
        return jsonify(result)
        
    except psycopg2.Error as e:
        logger.error(f"Database error during last 7d fetch: {e}")
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during last 7d fetch: {e}")
        return jsonify({'error': f"Error: {str(e)}"}), 500

@app.route('/api/moisture/<device_id>/next12h', methods=['GET'])
def get_next_12h(device_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"Fetching data for next 12h prediction for device_id: {device_id}")
        cursor.execute("""
            SELECT moisture_value, timestamp FROM moisture_data
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (device_id,))
        current = cursor.fetchone()
        
        if not current:
            return jsonify([]), 200
        
        current_value = float(current[0])
        current_timestamp = current[1]
        
        predictions = []
        for i in range(1, 13):
            target_hour = (current_timestamp + timedelta(hours=i)).hour
            three_days_ago = current_timestamp - timedelta(days=3)
            
            cursor.execute("""
                SELECT AVG(moisture_value) FROM moisture_data
                WHERE device_id = %s
                AND timestamp >= %s
                AND EXTRACT(HOUR FROM timestamp) = %s
            """, (device_id, three_days_ago, target_hour))
            avg_last_3_days = cursor.fetchone()
            
            if avg_last_3_days[0]:
                predicted_value = (float(avg_last_3_days[0]) + current_value) / 2
            else:
                predicted_value = current_value
            
            predictions.append({
                'value': round(predicted_value, 2),
                'timestamp': (current_timestamp + timedelta(hours=i)).strftime('%H:%M')
            })
            current_value = predicted_value

        logger.info(f"Returning {len(predictions)} predicted data points")
        
        cursor.close()
        conn.close()
        return jsonify(predictions)
        
    except psycopg2.Error as e:
        logger.error(f"Database error during next 12h fetch: {e}")
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during next 12h fetch: {e}")
        return jsonify({'error': f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    # Start the MQTT client
    mqtt_client = setup_mqtt_client()
    if not mqtt_client:
        sys.exit("Exiting due to MQTT connection failure.")
        
    # Start the Flask server
    # Note: Flask's development server is not ideal for production.
    # The 'use_reloader=False' is important to prevent running the setup code twice.
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, use_reloader=False) 