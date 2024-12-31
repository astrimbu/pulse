from arduino_controller import ArduinoController
import time
import logging
import sqlite3

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database():
    """Check the most recent moisture readings in the database"""
    try:
        with sqlite3.connect('../pulse_data.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sensor_number, moisture_level, raw_value, created_at 
                FROM moisture_readings 
                WHERE created_at >= datetime('now', '-5 minutes')
                ORDER BY created_at DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            logger.info("Recent moisture readings in database:")
            for row in rows:
                logger.info(f"Sensor {row[0]}: {row[1]}% (raw: {row[2]}) at {row[3]}")
            
            if not rows:
                logger.warning("No recent moisture readings found in database!")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")

def main():
    try:
        logger.info("Initializing Arduino controller...")
        controller = ArduinoController()
        
        logger.info("Reading sensor data for 30 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 30:
            logger.info("Getting sensor data...")
            readings = controller.get_sensor_data()
            logger.info(f"Received readings: {readings}")
            time.sleep(1)
            
        logger.info("Checking database for saved readings...")
        check_database()
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 