#!/usr/bin/python3.8

from datetime import datetime, timedelta
import json
import requests

params = {
    "lat": 40.593,
    "lon": -75.6568,
    "model": "gfs",
    "parameters": [
        "temp",
        "precip"
    ],
    "key": "iEb2hMpZP6GwbSvvpvoE2iPl0jRIocQh",
}

header = { "Content-Type": "application/json" }
raw = requests.post("https://api.windy.com/api/point-forecast/v2", json=params, headers=header).json()

data = {}
index = 0
temps = raw.get("temp-surface", [])
precips = raw.get("past3hprecip-surface", [])
for ts in raw.get("ts"):
    temp = round((((float(temps[index]) - 273) * 9) / 5) + 32, 2)
    precip = round(float(precips[index]) * 39.37, 2)
    data[ts/1000] = {
        "temp": temp,
        "precip": precip,
    }
    index += 1

processed_data = {}
target_day = datetime.now()
high_temp = -999
low_temp = 999
total_precip = 0
for ts in data.keys():
    date = datetime.fromtimestamp(ts)
    if date.day != target_day.day or date.month != target_day.month or date.year != target_day.year:
        # store data, reset counters, increment day
        day_data = {
            'precip': total_precip,
            'high_temp': high_temp,
            'low_temp': low_temp,
        }
        processed_data[target_day.isoformat()[:10]] = day_data
        high_temp = -999
        low_temp = 999
        total_precip = 0
        target_day = target_day + timedelta(days=1)
    total_precip += data[ts]['precip']
    if data[ts]['temp'] > high_temp:
        high_temp = data[ts]['temp']
    if data[ts]['temp'] < low_temp:
        low_temp = data[ts]['temp']
day_data = {
    'precip': total_precip,
    'high_temp': high_temp,
    'low_temp': low_temp,
}
processed_data[target_day.isoformat()[:10]] = day_data

for day, day_data in processed_data.items():
    print(f"{day} - high_temp: {day_data['high_temp']} degF, low_temp: {day_data['low_temp']} degF, rain: {day_data['precip']}\"")
