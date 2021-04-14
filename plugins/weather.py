from . import plugin
from datetime import datetime, timedelta
#from uszipcode import SearchEngine

import json
import math
import re
import requests
import traceback

class WeatherPlugin(plugin.NoBotPlugin):
    fields = {
        'wt360': {
            'date': 'utcDate',
            'max_temp': 'maxTemp',
            'min_temp': 'minTemp',
            'snow': 'snow',
            'prcp': 'prcp',
        },
        'weatherbit' : {
            'date': 'datetime',
            'max_temp': 'high_temp',
            'min_temp': 'low_temp',
            'snow': 'snow',
            'prcp': 'precip',
        }
    }

    def get_weather_data(self, days, datecode, zipcode):
        if self.source == 'weatherbit':
            api_key = self._config.get('WEATHERBIT_API_KEY')
            url = 'https://api.weatherbit.io/v2.0/forecast/daily?' + \
                  f'postal_code={zipcode}&days={days}&key={api_key}&units=I'
        else:
            api_key = self._config.get('WT360_API_KEY')
            url = "http://api.wt360business.com/API/weather/daily/" + \
                  f"%7BZU{zipcode}%7D?apiKey={api_key}&fmt=json&" + \
                  f"func=getSummaryInfo&calendar=julian&cnt={days}&units=f&" + \
                  f"sd={datecode}&avgTemp=1&prcp=1&maxTemp=1&minTemp=1&snow=1"
        if not api_key:
            self._log.debug(f"Didn't find an API key for source {self.source}")
            return []
        try:
            response = requests.get(url).json()
        except simplejson.errors.JSONDecodeError:
            self._log.error("Got invalid JSON from API:")
            self._log.error(requests.get(url))
            return []
        if self.source == 'weatherbit':
            if 'data' not in response:
                self._log.debug(
                    "Didn't find  the key 'data' in the response: " +
                    json.dumps(response, indent=2)
                )
                return []
            return {
                'name': response.get('city_name') + ", " + \
                        response.get('state_code'),
                'wxInfo': response['data'],
            }
        else:
            if response.get("status") != "success":
                return self.get_weather_data(days, datecode, '92328')
            return response.get('weatherInfo').get(f'ZU{zipcode}')

    def get_forecast_table(self, forecast, weather_info):
        if not weather_info:
            return forecast
        block = []
        block.append('```')
        block.append('Date       High    Low    Rain  Snow')
        block.append('=====================================')
        for day in weather_info.get('wxInfo'):
            date = datetime.strptime(
                day.get(
                    self.fields.get(self.source).get('date')
                )[:10],
                '%Y-%m-%d'
            )
            dow = f"{date.strftime('%m/%d')} {date.strftime('%a')[0]}"
            max_temp = "{:-03.1f}".format(
                float(day.get(
                    self.fields.get(self.source).get('max_temp')
                ))
            )
            min_temp = "{:-03.1f}".format(
                float(day.get(
                    self.fields.get(self.source).get('min_temp')
                ))
            )
            prcp = day.get(self.fields.get(self.source).get('prcp'))
            snow = day.get(self.fields.get(self.source).get('snow'))
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
                block.append(f"{dow}: {high_padding}{max_temp}°F "
                    f"{low_padding}{min_temp}°F  {prcp_padding}{prcp} " +
                    f"{snow_padding}{snow}")
            else:
                block.append(f"{dow}: {high_padding}{max_temp}°F "
                    f"{low_padding}{min_temp}°F {prcp_padding}{prcp}")
        block.append('```')
        forecast.append(
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': "\n".join(block),
                }
            }
        )
        if len(forecast) > 0:
            return forecast
        else:
            return []


    def get_forecast(self, days, datecode, zipcode, table=False):
        forecast = []
        weather_info = self.get_weather_data(days, datecode, zipcode)
        if not weather_info:
            return forecast
        forecast.append(
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"Forecast for {weather_info.get('name')}:",
                }
            }
        )
        if table:
            return self.get_forecast_table(forecast, weather_info)
        for day in weather_info.get('wxInfo'):
            dow = datetime.strptime(
                day.get(
                    self.fields.get(self.source).get('date')
                )[:10],
                '%Y-%m-%d'
            ).strftime('%A %B %d, %Y')
            max_temp = "{:-03.1f}".format(
                float(day.get(
                    self.fields.get(self.source).get('max_temp')
                ))
            )
            min_temp = "{:-03.1f}".format(
                float(day.get(
                    self.fields.get(self.source).get('min_temp')
                ))
            )
            prcp = day.get(self.fields.get(self.source).get('prcp'))
            snow = day.get(self.fields.get(self.source).get('snow'))
            if not prcp or float(prcp) == 0.0:
                prcp = None
            else:
                prcp = '{:02.2f}"'.format(float(prcp))
            if not snow or float(snow) == 0.0 or float(snow) == -999.99:
                snow = None
            else:
                snow = '{:02.2f}"'.format(float(snow))
            text = f"*{dow}:*\n_Temperature:_ {min_temp}°F - {max_temp}°F"
            if prcp:
                text += f"\n_Rain:_ {prcp}"
            if snow:
                text += f"\n_Snow:_ {snow}"
            forecast.append(
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': text,
                    },
                }
            )
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


    def get_source(self, command):
        for word in command:
            if word.lower() == 'weatherbit' or word.lower() == 'wt360':
                return word.lower()
        return self._config.get('SOURCE', 'wt360')


    def is_table_request(self, command):
        for word in command:
            if word.lower() == 'table':
                return True
        return False

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
            command = request['text'].replace('<tel:', '').replace('>', '').split()
            days = self.get_days(command)
            self.source = self.get_source(command)
            if days > 30:
                forecast = [
                    f"I'm sorry <@{request['user']}>, " +
                    "I can't make a forecast that long!"
                ]
            else:
                zipcode = self.get_zipcode(command)
                if int(days) < 0:
                    datecode = (
                        datetime.now() + timedelta(days=days)
                    ).strftime('%Y%m%d000000')
                    days = days * -1
                else:
                    datecode = datetime.now().strftime('%Y%m%d000000')
                try:
                    forecast = self.get_forecast(days, datecode, zipcode, table=self.is_table_request(command))
                except Exception as e:
                    self._log.error(traceback.format_exc())
                    forecast = [
                        "I'm sorry, there was a problem getting the " +
                        f"forecast you requested, <@{request['user']}>"
                    ]
            if len(forecast) > 0:
                if isinstance(forecast[0], str):
                    responses.append(
                        {
                            'channel': request['channel'],
                            'text': "\n".join(forecast),
                        }
                    )
                else:
                    response = {
                        'channel': request['channel'],
                        'blocks': forecast,
                    }
                    responses.append(response)
            else:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': f"Sorry, <@{request['user']}> -- I wasn't " +
                            "able to get any data for that request :shrug:",
                    }
                )
        return responses
