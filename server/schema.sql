CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature_c REAL NOT NULL,
    humidity_rh REAL NOT NULL,
    co2 INTEGER NOT NULL,
    vpd REAL NOT NULL,
    air_pressure REAL NOT NULL,
    dew_point_c REAL NOT NULL,
    created_at TEXT NOT NULL,
    device_id INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_readings_created_at 
ON readings(created_at); 

CREATE TABLE IF NOT EXISTS moisture_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_number INTEGER NOT NULL,
    moisture_level REAL NOT NULL,
    created_at TEXT NOT NULL,
    raw_value INTEGER
);

CREATE TABLE IF NOT EXISTS watering_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pump_number INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS float_sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_number INTEGER NOT NULL,
    status INTEGER NOT NULL,  -- 0 for no water, 1 for water detected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 