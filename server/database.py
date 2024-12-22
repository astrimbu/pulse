import sqlite3
import logging
from datetime import datetime
from typing import Dict, List
import os

class Database:
    def __init__(self, db_path: str = "../pulse_data.db"):
        self.logger = logging.getLogger('database')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        
        self.db_path = db_path
        self.logger.info(f"Initializing database at: {os.path.abspath(db_path)}")
        self.init_db()
    
    def init_db(self):
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            self.logger.info(f"Loading schema from: {schema_path}")
            
            with open(schema_path) as f:
                schema = f.read()
                self.logger.debug(f"Schema contents: {schema}")
            
            with sqlite3.connect(self.db_path) as conn:
                self.logger.info("Executing schema...")
                conn.executescript(schema)
                self.logger.info("Schema executed successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def save_reading(self, data: Dict):
        try:
            query = """
            INSERT INTO readings (
                temperature_c, humidity_rh, co2, vpd,
                air_pressure, dew_point_c, created_at, device_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.logger.debug(f"Saving reading: {data}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (
                    data['temperatureC'],
                    data['humidityRh'],
                    data['co2'],
                    data['vpd'],
                    data['airPressure'],
                    data['dpC'],
                    data['createdAt'],
                    data['deviceId']
                ))
                self.logger.info("Reading saved successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to save reading: {str(e)}")
            self.logger.error(f"Data: {data}")
            raise
    
    def get_latest(self) -> Dict:
        query = "SELECT * FROM readings ORDER BY created_at DESC LIMIT 1"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_daily_readings(self) -> List[Dict]:
        query = """
        SELECT * FROM readings 
        WHERE date(created_at) = date('now')
        ORDER BY created_at
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()] 