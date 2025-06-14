import psycopg2
from psycopg2 import sql
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import logging
import os
from datetime import datetime, timedelta
from config import DB_PARAMS

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

@app.route('/moisture', methods=['POST'])
def insert_moisture():
    try:
        data = request.json
        device_id = data.get('device_id')
        moisture_value = data.get('moisture_value')
        timestamp = data.get('timestamp')
        
        if not device_id or moisture_value is None:
            logger.warning("Missing device_id or moisture_value in request")
            return jsonify({'error': 'Missing device_id or moisture_value'}), 400
        
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        if timestamp:
            insert_query = """
            INSERT INTO moisture_data (device_id, moisture_value, timestamp)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (device_id, moisture_value, timestamp))
            logger.info(f"Inserted data with timestamp: {device_id}, {moisture_value}, {timestamp}")
        else:
            insert_query = """
            INSERT INTO moisture_data (device_id, moisture_value)
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (device_id, moisture_value))
            logger.info(f"Inserted data: {device_id}, {moisture_value}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Data inserted successfully'}), 201
        
    except psycopg2.Error as e:
        logger.error(f"Database error during insert: {e}")
        return jsonify({'error': f"Database error: {e}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during insert: {e}")
        return jsonify({'error': f"Error: {e}"}), 500

@app.route('/api/moisture/<device_id>', methods=['GET'])
def get_moisture(device_id):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
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
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        logger.info(f"Fetching last 12 hours data for device_id: {device_id}")

        # Find the latest timestamp for the device
        cursor.execute("""
            SELECT MAX(timestamp) FROM moisture_data WHERE device_id = %s
        """, (device_id,))
        latest_timestamp = cursor.fetchone()[0]

        if not latest_timestamp:
            logger.warning(f"No data found for device_id: {device_id}")
            return jsonify([]), 200

        # Calculate the 12-hour window before the latest timestamp
        twelve_hours_before_latest = latest_timestamp - timedelta(hours=12)

        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value,
                   DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= %s AND timestamp <= %s
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour_bucket ASC
        """, (device_id, twelve_hours_before_latest, latest_timestamp))
        data = cursor.fetchall()
        
        result = [
            {
                'value': round(float(row[0]), 2) if row[0] is not None else None,
                'timestamp': row[1].strftime('%H:%M')
            } for row in data
        ]
        
        logger.info(f"Returning {len(result)} data points for last 12 hours")
        
        cursor.close()
        conn.close()
        return jsonify(result)
        
    except psycopg2.Error as e:
        logger.error(f"Database error during last 12h fetch: {e}")
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during last 12h fetch: {e}")
        return jsonify({'error': f"Error: {str(e)}"}), 500

@app.route('/api/moisture/<device_id>/last24h', methods=['GET'])
def get_last_24h(device_id):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        logger.info(f"Fetching last 24 hours data for device_id: {device_id}")
        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour_bucket ASC
        """, (device_id,))
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
        conn = psycopg2.connect(**DB_PARAMS)
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
        conn = psycopg2.connect(**DB_PARAMS)
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
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port) 