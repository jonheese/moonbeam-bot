from . import plugin
from datetime import datetime, timedelta
from pyzipcode import ZipCodeDatabase

import json
import math
import re
import requests
import traceback

class WeatherPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__zcdb = ZipCodeDatabase()


    def __get_weather_data(self, days, datecode, zipcode):
        api_key = self._config.get('WEATHERBIT_API_KEY')
        url = 'https://api.weatherbit.io/v2.0/forecast/daily?' + \
              f'postal_code={zipcode}&days={days}&key={api_key}&units=I'
        if not api_key:
            self._log.debug("Didn't find a weatherbit API key")
            return []
        try:
            response = requests.get(url).json()
        except simplejson.errors.JSONDecodeError:
            self._log.error("Got invalid JSON from API:")
            self._log.error(requests.get(url))
            return []
        if 'data' not in response:
            self._log.debug(
                "Didn't find  the key 'data' in the response: " +
                json.dumps(response, indent=2)
            )
            return []
        return {
            'name': self.__get_citystate_by_zipcode(zipcode),
            'wxInfo': response['data'],
        }


    def __get_forecast_table(self, forecast, weather_info):
        if not weather_info:
            return forecast
        snow_found = False
        for day in weather_info.get('wxInfo'):
            if day.get('snow') and float(day.get('snow')) > 0.0:
                snow_found = True
                break
        block = []
        block.append('```')
        if snow_found:
            block.append('Date       High    Low    Rain  Snow')
            block.append('=====================================')
        else:
            block.append('Date       High    Low    Rain')
            block.append('===============================')
        for day in weather_info.get('wxInfo'):
            date = datetime.strptime(
                day.get('datetime')[:10],
                '%Y-%m-%d'
            )
            dow = f"{date.strftime('%m/%d')} {date.strftime('%a')[0]}"
            max_temp = "{:-03.1f}".format(float(day.get('high_temp')))
            min_temp = "{:-03.1f}".format(float(day.get('low_temp')))
            prcp = day.get('precip')
            if not prcp or float(prcp) == 0.0:
                prcp = '---- '
            else:
                prcp = '{:02.2f}"'.format(float(prcp))
            if snow_found:
                snow = day.get('snow')
                if not snow or float(snow) == 0.0:
                    snow = '---- '
                else:
                    snow = '{:02.2f}"'.format(float(snow))
            high_padding = (5 - len(max_temp)) * " "
            low_padding = (5 - len(min_temp)) * " "
            prcp_padding = (4 - len(prcp)) * " "
            if snow_found:
                snow_padding = (4 - len(snow)) * " "
                block.append(f"{dow}: {high_padding}{max_temp}°F "
                    f"{low_padding}{min_temp}°F  {prcp_padding}{prcp} " +
                    f"{snow_padding}{snow}")
            else:
                block.append(f"{dow}: {high_padding}{max_temp}°F "
                    f"{low_padding}{min_temp}°F  {prcp_padding}{prcp}")
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


    def __get_forecast(self, days, datecode, zipcode, table=False):
        forecast = []
        weather_info = self.__get_weather_data(days, datecode, zipcode)
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
            return self.__get_forecast_table(forecast, weather_info)
        for day in weather_info.get('wxInfo'):
            dow = datetime.strptime(
                day.get('datetime')[:10],
                '%Y-%m-%d'
            ).strftime('%A %B %d, %Y')
            max_temp = "{:-03.1f}".format(
                float(day.get('high_temp'))
            )
            min_temp = "{:-03.1f}".format(
                float(day.get('low_temp'))
            )
            prcp = day.get('precip')
            snow = day.get('snow')
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


    def __get_zipcode(self, command):
        for token in command:
            if re.search('\d{5}', token) and "." not in token:
                return token
        return '18104'


    def __get_citystate_by_zipcode(self, zipcode):
        loc = self.__zcdb[int(zipcode)]
        return f'{loc.city}, {loc.state}'


    def __is_table_request(self, command):
        for word in command:
            if word.lower() == 'table':
                return True
        return False


    def __is_notable_request(self, command):
        for word in command:
            if word.lower() == 'notable':
                return True
        return False


    def __get_days(self, command):
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
            days = self.__get_days(command)
            if days > 30:
                forecast = [
                    f"I'm sorry <@{request['user']}>, " +
                    "I can't make a forecast that long!"
                ]
            else:
                zipcode = self.__get_zipcode(command)
                if int(days) < 0:
                    datecode = (
                        datetime.now() + timedelta(days=days)
                    ).strftime('%Y%m%d000000')
                    days = days * -1
                else:
                    datecode = datetime.now().strftime('%Y%m%d000000')
                try:
                    table = False
                    if self.__is_table_request(command):
                        table = True
                    elif self.__is_notable_request(command):
                        table = False
                    elif days > 7:
                        table = True
                    forecast = self.__get_forecast(days, datecode, zipcode, table)
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

    def get_trigger_words(self):
        return [ "weather" ]
