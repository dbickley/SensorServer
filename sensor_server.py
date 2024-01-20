#sudo apt-get install sqlite3
#!pip install flask
#!pip install plotly

import sqlite3
import time
import plotly.express as px
import pandas as pd
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta


app = Flask(__name__, template_folder='templates')

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


@app.route('/current_time', methods=['GET'])
def get_current_time():
    epoch_time = int(time.time())  # Get Unix epoch time as an integer
    return  str(epoch_time)  # Return it as a JSON response


def print_hourly_data(hourly_data, num_rows=5):
    print(f"Sample rows from hourly_data:")
    for sensor_id, data in list(hourly_data.items())[:num_rows]:
        print(f"Sensor ID: {sensor_id}")
        print("Hourly Data:")
        for row in data:
            print(row)  # Print each hourly data row
        print()  # Add an empty line between sensors

def fetch_data_per_sensor(data_type, time_interval):
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()

    # Indexing the timestamp column
    cursor.execute('CREATE INDEX IF NOT EXISTS timestamp_index ON sensor_data(timestamp)')

    interval_format = {
        'hourly': '%Y-%m-%d %H:00',
        'minutely': '%Y-%m-%d %H:%M'
    }

    if time_interval not in interval_format:
        raise ValueError("Invalid time interval specified")

    # Calculate the timestamp for the specified interval
    time_format = interval_format[time_interval]
    time_ago = datetime.now() - timedelta(hours=24) if time_interval == 'hourly' else datetime.now() - timedelta(minutes=1440)
    
    query = f"""
        SELECT sensorId, time_group, AVG({data_type}) AS data_type
        FROM (
            SELECT sensorId, strftime('{time_format}', timestamp) AS time_group, {data_type}
            FROM sensor_data
            WHERE timestamp >= ?
        ) AS subquery
        GROUP BY sensorId, time_group
        ORDER BY sensorId, time_group
    """

    cursor.execute(query, (time_ago,))
    data = cursor.fetchall()

    sensor_data = {}
    for row in data:
        sensor_id = row[0]
        time_group = row[1]
        avg_value = row[2]

        if sensor_id not in sensor_data:
            sensor_data[sensor_id] = []
        sensor_data[sensor_id].append({time_interval: time_group, f'avg_{data_type}': avg_value})

    return sensor_data


def generate_combined_chart(sensor_data, data_type, time_interval):
    time_labels = {
        'hourly': 'Hour',
        'minutely': 'Minute'
    }

    fig = px.line(title=f'{time_interval.capitalize()} {data_type.capitalize()} for All Sensors')

    for sensor_id, data in sensor_data.items():
        time_groups = [row[time_interval] for row in data]
        values = [row[f'avg_{data_type}'] for row in data]

        fig.add_scatter(x=time_groups, y=values, mode='lines', name=f'Sensor {sensor_id}')

    fig.update_layout(xaxis_title=time_labels.get(time_interval, ''), yaxis_title=data_type.capitalize())
    fig_div = fig.to_html(full_html=False)

    return fig_div


@app.route('/')
def index():
    sensor_data_types = ['humidity', 'temperature', 'pressure', 'gas', 'color', 'alpha']
    time_intervals = ['minutely']  # Add more intervals if needed //'hourly',
    combined_charts = {}

    for data_type in sensor_data_types:
        for interval in time_intervals:
            data = fetch_data_per_sensor(data_type, interval)
            print_hourly_data(data, num_rows=5)
            combined_charts[f'{data_type}_{interval}'] = generate_combined_chart(data, data_type, interval)

    return render_template('index.html', combined_charts=combined_charts)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6660)

