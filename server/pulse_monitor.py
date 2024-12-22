import requests
import json
import time
import logging
from datetime import datetime
import os
from typing import Optional
from dotenv import load_dotenv
from database import Database

class PulseMonitor:
    def __init__(self):
        # Set up logging
        self.log_file = os.getenv('LOG_FILE', 'pulse_api.log')
        self.setup_logging()
        
        # Load environment variables
        load_dotenv()
        
        # Debug logging for environment variables
        self.logger.info("Environment variables after loading:")
        self.logger.info(f"PULSE_DEVICE_ID: {os.getenv('PULSE_DEVICE_ID')}")
        self.logger.info(f"PULSE_API_KEY: {'*' * len(os.getenv('PULSE_API_KEY', ''))} (masked)")
        
        # Initialize database connection
        self.db = Database()
        
        # Get configuration from environment
        self.device_id = os.getenv('PULSE_DEVICE_ID')
        api_key = os.getenv('PULSE_API_KEY')
        self.fetch_interval = int(os.getenv('FETCH_INTERVAL', 60))
        
        if not self.device_id or not api_key:
            raise ValueError("PULSE_DEVICE_ID and PULSE_API_KEY must be set in .env file")

        self.base_url = f"https://api.pulsegrow.com/devices/{self.device_id}/recent-data"
        self.headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }

    def setup_logging(self):
        # Configure logging for API interactions
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler for API logs
        api_handler = logging.FileHandler(self.log_file)
        api_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Set up loggers
        self.logger = logging.getLogger('pulse_monitor')
        self.logger.addHandler(api_handler)
        
        # Also log database operations
        db_logger = logging.getLogger('database')
        db_logger.addHandler(api_handler)

    def fetch_data(self) -> Optional[dict]:
        try:
            # Log the complete request details
            self.logger.info(f"Making request to: {self.base_url}")
            self.logger.info(f"Headers: {json.dumps({k: v if k != 'Authorization' else '[MASKED]' for k, v in self.headers.items()})}")
            
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            # Log the response
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response body: {response.text}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return None

    def save_data(self, data: dict):
        if not data:
            return
        try:
            self.db.save_reading(data)
            self.logger.info("Data saved to database")
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")

    def run(self):
        self.logger.info("Starting Pulse monitoring")
        
        while True:
            data = self.fetch_data()
            self.save_data(data)
            
            # Use configured fetch interval
            time.sleep(self.fetch_interval)

if __name__ == "__main__":
    monitor = PulseMonitor()
    monitor.run()