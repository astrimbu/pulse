import serial
import serial.tools.list_ports
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_arduino_connection():
    # List all available ports
    ports = list(serial.tools.list_ports.comports())
    logger.info(f"Found {len(ports)} ports:")
    for port in ports:
        logger.info(f"  - {port.device}: {port.description}")
        
        if "USB Serial" in port.description:
            logger.info(f"\nTesting connection to {port.device}...")
            try:
                # Open connection
                ser = serial.Serial(port.device, 9600, timeout=2)
                time.sleep(2)  # Wait for Arduino reset
                
                # Clear any pending data
                ser.reset_input_buffer()
                
                logger.info("Waiting for READY message...")
                start_time = time.time()
                
                while time.time() - start_time < 5:  # Wait up to 5 seconds
                    if ser.in_waiting:
                        msg = ser.readline().decode('ascii').strip()
                        logger.info(f"Received: {msg}")
                        if msg == "READY":
                            logger.info("Successfully connected to Arduino!")
                            ser.close()
                            return True
                    time.sleep(0.1)
                
                ser.close()
                logger.warning("Didn't receive READY message")
                
            except Exception as e:
                logger.error(f"Error testing {port.device}: {str(e)}")
    
    return False

if __name__ == "__main__":
    test_arduino_connection() 