# SensorServer

## Example Post

curl -X POST http://localhost:6660/sensor -H "Content-Type: application/json" -d '{
    "sensorId": 1,
    "humidity": 50.2,
    "temperature": 25.5,
    "pressure": 1013.25,
    "gas": 450,
    "color": "#FFAABB",
    "alpha": 255
}'


## Example Get last_values for all sensors
curl -X GET http://localhost:6660/last_values
