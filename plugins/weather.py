from . import plugin
from datetime import datetime, timedelta
#from uszipcode import SearchEngine

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
               f"cnt={days}&units=f&sd={datecode}&avgTemp=1&prcp=1&maxTemp=1&minTemp=1" + \
               "&snow=1"
        data = requests.get(url).json()
        if data.get("status") != "success":
            return self.get_forecast(days, datecode, '92328')
        weather_info = data.get('weatherInfo').get(f'ZU{zipcode}')
        forecast.append(f"Forecast for {weather_info.get('name')}:")
        forecast.append('```')
        forecast.append('Day     High     Low     Rain   Snow')
        forecast.append('=====================================')
        for day in weather_info.get('wxInfo'):
            dow = datetime.strptime(day.get('utcDate')[:10], '%Y-%m-%d').strftime('%a')
            max_temp = "{:-03.1f}".format(float(day.get('maxTemp')))
            min_temp = "{:-03.1f}".format(float(day.get('minTemp')))
            prcp = day.get('prcp')
            snow = day.get('snow')
            if not prcp or float(prcp) == 0.0:
                prcp = '---- '
            else:
                prcp = '{:02.2f}"'.format(float(prcp))
            if not snow or float(snow) == 0.0:
                snow = '---- '
            else:
                snow = '{:02.2f}"'.format(float(snow))
            high_padding = (5 - len(max_temp)) * " "
            low_padding = (5 - len(min_temp)) * " "
            prcp_padding = (4 - len(prcp)) * " "
            snow_padding = (4 - len(snow)) * " "
            if snow:
                forecast.append(f"{dow}:  {high_padding}{max_temp}°F  "
                                f"{low_padding}{min_temp}°F {prcp_padding}  {prcp}" +
                                f"{snow_padding}  {snow}")
            else:
                forecast.append(f"{dow}:  {high_padding}{max_temp}°F  "
                                f"{low_padding} {min_temp}°F {prcp_padding}  {prcp}")
        forecast.append('```')
        if days > 0:
            return forecast
        else:
            return []


    def get_zipcode(self, command):
        for token in command:
            if re.search('\d{5}', token) and "." not in token:
                return token
        #city_state = re.search('(\w+, \w+)', " ".join(command))
        #if city_state:
        #    [city, state] = city_state.groups(0)[0].split(', ')
        #    zipcode = self.search_for_city(city, state)
        #    if zipcode:
        #        return zipcode
        #else:
        #    for token in command:
        #        if token.lower() not in ['moonbeam', 'weather', 'days']:
        #            zipcode = self.search_for_city(token, None)
        #            if zipcode:
        #                return zipcode
        return '18104'


    #def search_for_city(self, city, state):
    #    search = SearchEngine(simple_zipcode=True)
    #    results = search.by_city_and_state(city, state)
    #    if results:
    #        return results[0].zipcode
    #    return None


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
            if days > 30:
                forecast = [f"I'm sorry <@{request['user']}>, I can't make a forecast that long!"]
            else:
                zipcode = self.get_zipcode(command)
                if int(days) < 0:
                    datecode = (datetime.now() + timedelta(days=days)).strftime('%Y%m%d000000')
                    days = days * -1
                else:
                    datecode = datetime.now().strftime('%Y%m%d000000')
                try:
                    forecast = self.get_forecast(days, datecode, zipcode)
                except Exception as e:
                    forecast = [f"I'm sorry, there was a problem getting the forecast you requested, <@{request['user']}>"]
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
                        'text': f"Sorry, <@{request['user']}> -- I wasn't able to get any data for that request :shrug:",
                    }
                )
        return responses
