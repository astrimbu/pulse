import serial
import json
import logging
from typing import Dict
import time
import sqlite3
from datetime import datetime
import sys

class ArduinoController:
    def __init__(self, port=None, baud_rate=9600, db_path='../pulse_data.db'):
        self.logger = logging.getLogger('arduino_controller')
        
        # Auto-detect Arduino port if none specified
        if port is None:
            port = self._find_arduino_port()
            if port is None:
                error_msg = (
                    "No Arduino found. Please check:\n"
                    "1. Arduino is properly connected via USB\n"
                    "2. No other program is using the serial port\n"
                    "3. You have sufficient permissions to access the port\n"
                    "4. The correct Arduino drivers are installed"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        try:
            self.logger.info(f"Connecting to Arduino on port {port}")
            self.serial = serial.Serial(port, baud_rate, timeout=1)
            self.db_path = db_path
            time.sleep(2)  # Wait for Arduino to reset
        except PermissionError:
            error_msg = (
                f"Permission denied accessing port {port}. "
                "Please check if another program is using the port "
                "or try running with administrator privileges."
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Failed to connect to Arduino on port {port}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _find_arduino_port(self):
        """Auto-detect the Arduino port"""
        import serial.tools.list_ports
        
        self.logger.info("Searching for Arduino...")
        ports = list(serial.tools.list_ports.comports())
        self.logger.info(f"Found {len(ports)} ports:")
        
        for port in ports:
            self.logger.info(f"  - {port.device}: {port.description}")
            
            # On Windows, Arduino usually shows up as "USB Serial Device"
            if sys.platform.startswith('win'):
                if "USB Serial" in port.description:
                    self.logger.info(f"Found likely Arduino on {port.device}")
                    
                    # Try multiple times to connect
                    for attempt in range(3):
                        try:
                            self.logger.info(f"Attempt {attempt + 1} to connect to {port.device}")
                            s = serial.Serial(port.device, 9600, timeout=2)
                            time.sleep(2)  # Wait for Arduino reset
                            
                            # Try to read the "READY" message
                            start_time = time.time()
                            while time.time() - start_time < 5:  # Wait up to 5 seconds
                                if s.in_waiting:
                                    msg = s.readline().decode('ascii').strip()
                                    self.logger.info(f"Received: {msg}")
                                    if msg == "READY":
                                        s.close()
                                        return port.device
                                time.sleep(0.1)
                            
                            s.close()
                        except PermissionError:
                            self.logger.warning(
                                f"Permission denied for {port.device}. "
                                "Make sure no other program is using the port "
                                "and you have sufficient permissions."
                            )
                            time.sleep(1)  # Wait before retry
                        except Exception as e:
                            self.logger.warning(f"Failed to connect to {port.device}: {str(e)}")
                            break  # Don't retry for other errors
            else:
                # On Linux/Mac, look for ACM or USB devices
                if "ACM" in port.device or "USB" in port.device:
                    try:
                        s = serial.Serial(port.device, 9600, timeout=2)
                        s.close()
                        return port.device
                    except:
                        continue
        
        self.logger.error("No Arduino found on any port")
        return None

    def save_moisture_readings(self, readings: Dict):
        """Save moisture sensor readings and float sensor data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Log all incoming readings
                self.logger.info(f"Processing readings for save: {readings}")
                
                for sensor, value in readings.items():
                    # Handle float sensors
                    if sensor.startswith('F'):
                        sensor_num = int(sensor[1:])
                        # Skip if the value is NC (Not Connected)
                        if value == 'NC':
                            self.logger.warning(f"Float sensor {sensor_num} reported NC, skipping")
                            continue
                            
                        try:
                            # Value is already an integer, no need to parse
                            status = value  # Remove the split() and float() conversion
                            self.logger.info(f"Saving float sensor {sensor_num} - Status: {status}")
                            
                            conn.execute(
                                """INSERT INTO float_sensor_readings 
                                   (sensor_number, status, created_at) 
                                   VALUES (?, ?, datetime('now'))""",
                                (sensor_num, status)
                            )
                        except Exception as e:
                            self.logger.error(f"Error saving float sensor {sensor_num}: {str(e)}")
                    
                    # Handle moisture sensors
                    elif sensor.startswith('M') and not sensor.endswith('_raw'):
                        sensor_num = int(sensor[1:])
                        raw_value = readings.get(f"{sensor}_raw")
                        
                        if value != 'NC':
                            conn.execute(
                                """INSERT INTO moisture_readings 
                                   (sensor_number, moisture_level, raw_value, created_at) 
                                   VALUES (?, ?, ?, datetime('now'))""",
                                (sensor_num, float(value), raw_value)
                            )
                            self.logger.info(f"Saved moisture reading for sensor {sensor_num}: {value}% (raw: {raw_value})")
                
                self.logger.info("Database save completed")
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")

    def save_watering_event(self, pump_number: int, duration_ms: int):
        """Log watering event to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO watering_events (pump_number, duration_ms, created_at) VALUES (?, ?, ?)",
                    (pump_number, duration_ms, datetime.now().isoformat())
                )
            self.logger.info(f"Logged watering event: Pump {pump_number} for {duration_ms}ms")
        except Exception as e:
            self.logger.error(f"Error logging watering event: {str(e)}")

    def get_sensor_data(self) -> Dict:
        """Read latest sensor data from Arduino"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Check if port is still valid
                if not self.serial.is_open:
                    self.logger.warning("Serial port was closed, attempting to reopen...")
                    self.serial.open()
                    time.sleep(2)  # Wait for Arduino reset
                
                # Clear any stale data
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                
                self.logger.info("Waiting for BEGIN marker...")
                start_data = self.serial.read_until(b'BEGIN>')
                self.logger.debug(f"Received start marker data: {start_data}")
                
                if b'BEGIN>' not in start_data:
                    raise TimeoutError("Never received BEGIN marker")
                
                # Read until end marker
                data = self.serial.read_until(b'<END').decode('ascii').strip()
                self.logger.info(f"Raw Arduino data: {data}")
                
                readings = {}
                
                # First split by comma and clean up each segment
                segments = [seg.strip() for seg in data.split(',')]
                self.logger.info(f"Split segments: {segments}")
                
                # Process each segment
                for segment in segments:
                    self.logger.debug(f"Processing segment: {segment}")
                    
                    # Handle moisture readings
                    if 'M' in segment and '|' in segment:
                        # Find the position of M and extract from there
                        moisture_start = segment.find('M')
                        reading_part = segment[moisture_start:]
                        
                        try:
                            sensor, value = reading_part.split(':', 1)
                            sensor = sensor.strip()
                            
                            if '|' in value:
                                moisture_value, raw_value = value.split('|')
                                try:
                                    readings[sensor] = float(moisture_value)
                                    readings[f"{sensor}_raw"] = int(raw_value)
                                    self.logger.info(f"Parsed {sensor}: {readings[sensor]}% (raw: {raw_value})")
                                except ValueError:
                                    self.logger.warning(f"Invalid moisture reading: {value}")
                                    readings[sensor] = 'NC'
                                    readings[f"{sensor}_raw"] = None
                        except Exception as e:
                            self.logger.warning(f"Error parsing moisture reading: {reading_part}, error: {str(e)}")
                            continue
                    
                    # Handle float sensors
                    elif segment.startswith('F'):
                        self.logger.info(f"Found float sensor data: {segment}")
                        try:
                            sensor, value = segment.split(':', 1)
                            sensor = sensor.strip()
                            value = value.split('(')[0].strip()  # Remove debug info in parentheses
                            
                            try:
                                parsed_value = int(float(value))
                                readings[sensor] = parsed_value
                                self.logger.info(f"Float sensor {sensor} - Raw value: {value}, Parsed value: {parsed_value}")
                            except ValueError:
                                readings[sensor] = 'NC'
                                self.logger.warning(f"Invalid float sensor value - Raw: {value}")
                        except Exception as e:
                            self.logger.error(f"Error parsing float segment '{segment}': {str(e)}")
                            continue
                
                self.logger.info(f"Final readings dictionary: {readings}")
                
                # Save readings to database
                if readings:
                    self.save_moisture_readings(readings)
                    self.logger.info("Saved readings to database")
                else:
                    self.logger.warning("No readings to save to database")
                    
                return readings
                
            except Exception as e:
                self.logger.error(f"Error in get_sensor_data: {str(e)}")
                return None

    def control_pump(self, pump_number: int, duration_ms: int):
        """Control a specific water pump"""
        try:
            command = f"PUMP:{pump_number}:{duration_ms}\n"
            self.serial.write(command.encode())
            self.logger.info(f"Sent pump command: {command.strip()}")
        except Exception as e:
            self.logger.error(f"Error controlling pump: {str(e)}")

    def reset_connection(self):
        """Reset the serial connection to the Arduino"""
        self.logger.info("Resetting Arduino connection...")
        try:
            if self.serial.is_open:
                self.serial.close()
            time.sleep(1)
            self.serial = serial.Serial(self.serial.port, self.serial.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            self.logger.info("Successfully reset Arduino connection")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset Arduino connection: {str(e)}")
            return False