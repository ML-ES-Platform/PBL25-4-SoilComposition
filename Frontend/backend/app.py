import psycopg2
from psycopg2 import sql
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import logging
import os
from datetime import datetime, timedelta

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

db_params = {
    'host': 'localhost',
    'user': 'postgres',
    'password': '123qweASDZXC',
    'port': 5432,
    'database': 'iot_data'
}

def init_database():
    database_name = 'iot_data'
    try:
        logger.info("Attempting to connect to 'postgres' database...")
        conn = psycopg2.connect(database='postgres', **{k: v for k, v in db_params.items() if k != 'database'})
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info(f"Checking if database '{database_name}' exists...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{database_name}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
            logger.info(f"Database '{database_name}' created successfully!")
        else:
            logger.info(f"Database '{database_name}' already exists.")
        
        cursor.close()
        conn.close()
        
        logger.info(f"Connecting to '{database_name}' database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info("Creating 'moisture_data' table if not exists...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS moisture_data (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            moisture_value DECIMAL(5,2) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("Table 'moisture_data' created successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

try:
    logger.info("Initializing database...")
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    sys.exit(1)

@app.route('/api/moisture', methods=['POST'])
def insert_moisture():
    try:
        data = request.json
        device_id = data.get('device_id')
        moisture_value = data.get('moisture_value')
        timestamp = data.get('timestamp')
        
        if not device_id or moisture_value is None:
            logger.warning("Missing device_id or moisture_value in request")
            return jsonify({'error': 'Missing device_id or moisture_value'}), 400
        
        conn = psycopg2.connect(**db_params)
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
        conn = psycopg2.connect(**db_params)
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
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info(f"Fetching last 12 hours data for device_id: {device_id}")
        cursor.execute("""
            SELECT COUNT(*) FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '12 hours'
        """, (device_id,))
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} records for device_id: {device_id} in last 12 hours")
        
        if count == 0:
            logger.warning(f"No data found for device_id: {device_id} in last 12 hours")
            return jsonify([]), 200
        
        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '12 hours'
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
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info(f"Fetching last 24 hours data for device_id: {device_id}")
        cursor.execute("""
            SELECT COUNT(*) FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '24 hours'
        """, (device_id,))
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} records for device_id: {device_id} in last 24 hours")
        
        if count == 0:
            logger.warning(f"No data found for device_id: {device_id} in last 24 hours")
            return jsonify([]), 200
        
        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   FLOOR(EXTRACT(EPOCH FROM timestamp) / 7200)::INTEGER * 7200 as time_bucket
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY FLOOR(EXTRACT(EPOCH FROM timestamp) / 7200)
            ORDER BY time_bucket ASC
        """, (device_id,))
        data = cursor.fetchall()
        
        result = [
            {
                'value': round(float(row[0]), 2) if row[0] is not None else None,
                'timestamp': datetime.fromtimestamp(int(row[1])).strftime('%H:%M')
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
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info(f"Fetching last 7 days data for device_id: {device_id}")
        cursor.execute("""
            SELECT AVG(moisture_value) as avg_value, 
                   DATE_TRUNC('day', timestamp) as day
            FROM moisture_data
            WHERE device_id = %s AND timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY day ASC
        """, (device_id,))
        data = cursor.fetchall()
        
        result = [
            {
                'value': round(float(row[0]), 2),
                'timestamp': row[1].strftime('%Y-%m-%d')
            } for row in data
        ]
        
        cursor.close()
        conn.close()
        return jsonify(result)
        
    except psycopg2.Error as e:
        logger.error(f"Database error during last 7d fetch: {e}")
        return jsonify({'error': f"Database error: {e}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during last 7d fetch: {e}")
        return jsonify({'error': f"Error: {e}"}), 500

@app.route('/api/moisture/<device_id>/next12h', methods=['GET'])
def get_next_12h(device_id):
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info(f"Fetching next 12 hours prediction for device_id: {device_id}")
        current_time = datetime.now()
        result = []
        
        for hour_offset in range(12):
            target_hour = (current_time.hour + hour_offset) % 24
            cursor.execute("""
                SELECT AVG(moisture_value)
                FROM moisture_data
                WHERE device_id = %s
                AND timestamp >= NOW() - INTERVAL '3 days'
                AND EXTRACT(HOUR FROM timestamp) = %s
            """, (device_id, target_hour))
            avg_value = cursor.fetchone()
            value = round(float(avg_value[0]), 2) if avg_value[0] else None
            future_time = (current_time + timedelta(hours=hour_offset)).strftime('%H:%M')
            result.append({'value': value, 'timestamp': future_time})
        
        cursor.close()
        conn.close()
        return jsonify(result)
        
    except psycopg2.Error as e:
        logger.error(f"Database error during next 12h fetch: {e}")
        return jsonify({'error': f"Database error: {e}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during next 12h fetch: {e}")
        return jsonify({'error': f"Error: {e}"}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    logger.info(f"Starting Flask server on port {port}...")
    try:
        app.run(debug=True, port=port)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        sys.exit(1)