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

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
}); 