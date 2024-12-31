from arduino_controller import ArduinoController
import time
import logging

# Set up more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Initializing Arduino controller...")
        controller = ArduinoController()
        
        logger.info("Reading sensor data for 10 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            logger.info("Getting sensor data...")
            readings = controller.get_sensor_data()
            logger.info(f"Received readings: {readings}")
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.info("\nTIP: Make sure Arduino is connected and no other program is using the serial port")
        logger.info("Available ports:")
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            logger.info(f"  - {port.device} ({port.description})")

if __name__ == "__main__":
    main() 