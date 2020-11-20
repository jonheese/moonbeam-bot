from . import plugin
from datetime import datetime, timedelta

import json
import math
import re
import requests

class WeatherPlugin(plugin.NoBotPlugin):
    def get_forecast(self, days, datecode, zipcode):
        forecast = []
        api_key = self._config.get('WT360_API_KEY')
        if not api_key:
            return forecast
        url = f"http://api.wt360business.com/API/weather/daily/%7BZU{zipcode}%7D?" + \
               f"apiKey={api_key}&fmt=json&func=getSummaryInfo&calendar=julian&" + \
               f"cnt={days}&units=f&sd={datecode}&avgTemp=1&prcp=1&maxTemp=1&minTemp=1"
        data = requests.get(url).json()
        if data.get("status") != "success":
            return self.get_forecast(days, datecode, '92328')
        weather_info = data.get('weatherInfo').get(f'ZU{zipcode}')
        forecast.append(f"Forecast for {weather_info.get('name')}:")
        forecast.append('```')
        for day in weather_info.get('wxInfo'):
            date = datetime.strptime(day.get('utcDate')[:10], '%Y-%m-%d').strftime('%A (%m/%d)')
            max_temp = day.get('maxTemp')
            min_temp = day.get('minTemp')
            prcp = day.get('prcp')
            date_padding = (17 - len(date)) * " "
            high_padding = (4 - len(max_temp)) * " "
            low_padding = (4 - len(min_temp)) * " "
            forecast.append(f"{date}:{date_padding} High: {day.get('maxTemp')}°F, {high_padding}Low: {day.get('minTemp')}°F,{low_padding} Precipitation: {day.get('prcp')}\"")
        forecast.append('```')
        if days > 0:
            return forecast
        else:
            return []


    def get_zipcode(self, command):
        for token in command:
            if re.search('\d{5}', token) and "." not in token:
                return token
        return '18104'


    def get_days(self, command):
        numbered = {
            "hours": 1/24,
            "days": 1,
            "weeks": 7,
            "fortnights": 14,
            "months": 30,
            "quarters": 90,
            "years": 365,
        }
        standalone = {
            "today": 1,
        }
        index = 0
        for token in command:
            if token in standalone.keys():
                return standalone[token]
            if token in numbered.keys() or f"{token}s" in numbered.keys():
                try:
                    number = float(command[index-1])
                except Exception:
                    number = 1
                if token in numbered.keys():
                    return math.ceil(number * numbered[token])
                else:
                    return math.ceil(number * numbered[token+"s"])
            index += 1
        return 5


    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if request['text'].lower().startswith("moonbeam weather"):
            self._log.debug(f"Got weather request: {request['text']}")
            command = request['text'].split()
            days = self.get_days(command)
            zipcode = self.get_zipcode(command)
            if int(days) < 0:
                datecode = (datetime.now() + timedelta(days=days)).strftime('%Y%m%d000000')
                days = days * -1
            else:
                datecode = datetime.now().strftime('%Y%m%d000000')
            forecast = self.get_forecast(days, datecode, zipcode)
            if len(forecast) > 0:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': "\n".join(forecast),
                    }
                )
            else:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': "Sorry, I wasn't able to get any data for that request :shrug:",
                    }
                )
        return responses
