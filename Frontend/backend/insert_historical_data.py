import psycopg2
from datetime import datetime, timedelta
import random
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Database connection parameters
db_params = {
    'host': 'localhost',
    'user': 'postgres',
    'password': '123qweASDZXC',
    'port': 5432,
    'database': 'iot_data'
}

def insert_historical_data():
    try:
        # Connect to the database
        logger.info("Connecting to 'iot_data' database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Define time range: past week (June 6 to June 13, 2025)
        end_time = datetime(2025, 6, 13, 18, 30, 0)  # June 13, 00:00:00
        start_time = end_time - timedelta(days=7)  # June 6, 00:00:00
        device_id = 'sensor1'

        # Generate hourly data
        current_time = start_time
        moisture_value = 45.0  # Starting moisture value
        while current_time <= end_time:
            # Add slight random variation to moisture value (between 30.0 and 60.0)
            moisture_value += random.uniform(-2.0, 2.0)
            moisture_value = max(30.0, min(60.0, moisture_value))  # Keep within bounds
            moisture_value = round(moisture_value, 2)

            # Insert data
            insert_query = """
            INSERT INTO moisture_data (device_id, moisture_value, timestamp)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (device_id, moisture_value, current_time))
            logger.info(f"Inserted: device_id={device_id}, moisture_value={moisture_value}, timestamp={current_time}")

            # Move to next hour
            current_time += timedelta(hours=1)

        # Commit and close
        conn.commit()
        logger.info("All data inserted successfully!")
        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == '__main__':
    insert_historical_data()