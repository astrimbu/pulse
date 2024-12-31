const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const port = 3000;

const db = new sqlite3.Database('../pulse_data.db');

app.use(express.static('public'));

app.get('/api/latest', (req, res) => {
    db.get(
        "SELECT * FROM readings ORDER BY created_at DESC LIMIT 1",
        (err, row) => {
            if (err) {
                res.status(500).json({ error: 'Database error' });
                return;
            }
            res.json(row);
        }
    );
});

app.get('/api/history', (req, res) => {
    db.all(
        "SELECT * FROM readings WHERE date(created_at) = date('now') ORDER BY created_at",
        (err, rows) => {
            if (err) {
                res.status(500).json({ error: 'Database error' });
                return;
            }
            res.json(rows);
        }
    );
});

app.post('/api/water/plant/:id', (req, res) => {
    const plantId = parseInt(req.params.id);
    const duration = req.body.duration || 1000; // default 1 second
    
    // Spawn Python script to control Arduino
    const spawn = require('child_process').spawn;
    const pythonProcess = spawn('python3', [
        '../server/control_pump.py',
        '--pump', plantId.toString(),
        '--duration', duration.toString()
    ]);

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            res.status(500).json({ error: 'Failed to control pump' });
            return;
        }
        res.json({ success: true });
    });
});

app.get('/api/moisture', (req, res) => {
    console.log('Fetching moisture readings...');
    
    // First query for moisture readings
    db.all(
        `SELECT sensor_number, moisture_level, raw_value, created_at 
         FROM moisture_readings 
         WHERE created_at >= datetime('now', '-6 seconds')
         GROUP BY sensor_number
         HAVING created_at = (
             SELECT MAX(created_at) 
             FROM moisture_readings m2 
             WHERE m2.sensor_number = moisture_readings.sensor_number
         )
         ORDER BY sensor_number ASC`,
        (err, moistureRows) => {
            if (err) {
                console.error('Database error:', err);
                res.status(500).json({ error: 'Database error' });
                return;
            }
            
            // Then query for float sensor readings
            db.all(
                `SELECT sensor_number, status, created_at 
                 FROM float_sensor_readings 
                 WHERE created_at >= datetime('now', '-6 seconds')
                 GROUP BY sensor_number
                 HAVING created_at = (
                     SELECT MAX(created_at) 
                     FROM float_sensor_readings f2 
                     WHERE f2.sensor_number = float_sensor_readings.sensor_number
                 )
                 ORDER BY sensor_number ASC`,
                (err, floatRows) => {
                    if (err) {
                        console.error('Database error:', err);
                        res.status(500).json({ error: 'Database error' });
                        return;
                    }
                    
                    // Convert float sensor rows to array of boolean values
                    const floatSensors = Array(2).fill(false); // Initialize with 2 sensors
                    floatRows.forEach(row => {
                        if (row.sensor_number >= 1 && row.sensor_number <= 2) {
                            floatSensors[row.sensor_number - 1] = row.status === 1;
                        }
                    });
                    
                    const response = {
                        timestamp: new Date().toISOString(),
                        readings: moistureRows,
                        float_sensors: floatSensors
                    };
                    
                    console.log('Sensor readings found:', response);
                    res.json(response);
                }
            );
        }
    );
});

app.get('/api/moisture/history/:sensorNumber', (req, res) => {
    const sensorNumber = req.params.sensorNumber;
    db.all(
        `SELECT moisture_level, created_at 
         FROM moisture_readings 
         WHERE sensor_number = ? 
         AND created_at >= datetime('now', '-24 hours')
         ORDER BY created_at ASC`,
        [sensorNumber],
        (err, rows) => {
            if (err) {
                console.error('Database error:', err);
                res.status(500).json({ error: 'Database error' });
                return;
            }
            res.json(rows);
        }
    );
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
}); 