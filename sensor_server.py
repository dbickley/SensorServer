#sudo apt-get install sqlite3
#!pip install flask

from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Create a SQLite database and a table to store sensor data
conn = sqlite3.connect('sensor_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensorId INTEGER,
        timestamp DATETIME,
        humidity REAL,
        temperature REAL,
        pressure REAL,
        gas REAL,
        color INTEGER,
        alpha INTEGER
    )
''')
conn.commit()

def is_hex_color(s):
    if s.startswith('#') and len(s) in (4, 7):
        try:
            int(s[1:], 16)
            return True
        except ValueError:
            pass
    return False

def convert_hex_to_int(hex_color):
    return int(hex_color.lstrip('#'), 16)

@app.route('/sensor', methods=['POST'])
def sensor_data():
    try:
        data = request.get_json()  # Get JSON data sent by the sensor
        sensor_id = data.get('sensorId')
        humidity = data.get('humidity')
        temperature = data.get('temperature')
        pressure = data.get('pressure')
        gas = data.get('gas')
        color = data.get('color')
        alpha = data.get('alpha')

        timestamp = datetime.now()

        # Convert color to integer if it's a valid hex color
        if is_hex_color(color):
            color = convert_hex_to_int(color)
        else:
            color = None  # Set to None if not a valid hex color

        # Store data in the SQLite database
        cursor.execute('''
            INSERT INTO sensor_data 
            (sensorId, timestamp, humidity, temperature, pressure, gas, color, alpha) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sensor_id, timestamp, humidity, temperature, pressure, gas, color, alpha))
        conn.commit()

        print("Received sensor data:", data)
        return jsonify({"message": "Data received and stored successfully"})
    except Exception as e:
        print("Error storing sensor data:", e)
        return jsonify({"message": "Error storing sensor data"}), 500  # Return 500 for internal server error

# Endpoint to get the last recorded values for each sensor
@app.route('/last_values', methods=['GET'])
def get_last_values():
    try:
        cursor.execute('''
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY sensorId ORDER BY timestamp DESC) AS rn
                FROM sensor_data
            ) WHERE rn = 1
        ''')
        data = cursor.fetchall()

        # Format data into dictionary with sensorId as keys
        last_values = {}
        for row in data:
            sensor_id = row[1]
            last_values[sensor_id] = {
                "timestamp": row[2],
                "humidity": row[3],
                "temperature": row[4],
                "pressure": row[5],
                "gas": row[6],
                "color": row[7],
                "alpha": row[8]
            }

        return jsonify(last_values)
    except Exception as e:
        print("Error fetching last values:", e)
        return jsonify({"message": "Error fetching last values"}), 500  # Return 500 for internal server error



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6660)

