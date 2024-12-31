# Pulse Monitor

A data logging and visualization application for the Pulse Pro

## Setup

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Node.js dependencies:
   ```bash
   cd web
   npm init -y
   npm install express sqlite3
   ```
4. Copy `.env.example` to `.env` and update with your credentials

## Configuration

Edit `.env` file with your settings:
- `PULSE_DEVICE_ID`: Your Pulse device ID
- `PULSE_API_KEY`: Your API key

## Running the Application

1. Start the Python data collector:
   ```bash
   cd server
   python3 pulse_monitor.py
   ```
2. In a new terminal, start the web server:
   ```bash
   cd web
   node server.js
   ```
3. Visit `http://localhost:3000` in your browser to view the dashboard

## Data Storage

- Data is stored in SQLite database: `pulse_data.db`

## API Endpoints

- GET `/api/latest` - Get most recent sensor reading
- GET `/api/history` - Get all readings for current day

## Development

To reset the database:
```bash
rm pulse_data.db
```
The database will be automatically recreated when the application starts.