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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6660)


'''
curl -X POST http://localhost:5000/sensor -H "Content-Type: application/json" -d '{
    "sensorId": 1,
    "humidity": 50.2,
    "temperature": 25.5,
    "pressure": 1013.25,
    "gas": 450,
    "color": "#FFAABB",
    "alpha": 255
}'
'''