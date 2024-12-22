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