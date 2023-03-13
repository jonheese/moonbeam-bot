from . import plugin
from datetime import datetime, timedelta
from pyzipcode import ZipCodeDatabase

import json
import math
import numpy
import pgeocode
import re
import requests
import simplejson
import traceback

class WeatherPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__zcdb = ZipCodeDatabase()


    def __get_daily_weather_data(self, days, datecode, zipcode):
        api_key = self._config.get('RAPIDAPI_API_KEY')
        api_host = self._config.get('RAPIDAPI_API_HOST')
        url = f'https://{api_host}/forecast/daily'
        if not api_key:
            self._log.debug("Didn't find a RapidAPI API key")
            return []
        if not api_host:
            self._log.debug("Didn't find a RapidAPI API host")
            return []
        (lat, lon) = self.__get_latlon_from_zipcode(zipcode)
        if not lat or not lon:
            return []
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api_host,
        }
        params = {
            "lat": lat,
            "lon": lon,
            "units": "imperial",
            "lang":"en",
            "days": days,
        }
        try:
            response = requests.request("GET", url, headers=headers, params=params).json()
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
            'period': 'daily',
        }


    def __get_latlon_from_zipcode(self, zipcode):
        data = pgeocode.Nominatim('us').query_postal_code(zipcode)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if numpy.isnan(latitude):
            latitude = False
        if numpy.isnan(longitude):
            longitude = False
        return (latitude, longitude)


    def __get_hourly_weather_data(self, hours, datecode, zipcode):
        api_key = self._config.get('RAPIDAPI_API_KEY')
        api_host = self._config.get('RAPIDAPI_API_HOST')
        url = f'https://{api_host}/forecast/hourly'
        if not api_key:
            self._log.debug("Didn't find a RapidAPI API key")
            return []
        if not api_host:
            self._log.debug("Didn't find a RapidAPI API host")
            return []
        (lat, lon) = self.__get_latlon_from_zipcode(zipcode)
        if not lat or not lon:
            return []
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api_host,
        }
        params = {
            "lat": lat,
            "lon": lon,
            "units": "imperial",
            "lang":"en",
            "hours": hours,
        }
        try:
            response = requests.request("GET", url, headers=headers, params=params).json()
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
            'period': 'hourly',
        }

    def __get_forecast_table(self, forecast, weather_info):
        if not weather_info:
            return forecast
        snow_found = False
        for day in weather_info.get('wxInfo'):
            if day.get('snow') and float(day.get('snow')) > 0.0:
                snow_found = True
                break
        hourly = weather_info.get('period') == 'hourly'
        block = []
        block.append('```')
        if hourly:
            block.append('Hour     Temp   Feels   Rain%    Wind (Gust)       Summary')
            block.append('=================================================================')
        elif snow_found:
            block.append('Date       High    Low    Rain  Snow    Wind (Gust)      Summary')
            block.append('=======================================================================')
        else:
            block.append('Date       High    Low    Rain    Wind (Gust)      Summary')
            block.append('=================================================================')
        for day in weather_info.get('wxInfo'):
            self._log.debug(json.dumps(day, indent=2))
            wind_spd = "{:03.1f}".format(float(day.get('wind_spd')))
            wind_cdir = str(day.get('wind_cdir'))
            wind_gust_spd = "{:03.1f}".format(float(day.get('wind_gust_spd')))
            wind_padding = (5 - len(wind_spd)) * " "
            cdir_padding = (3 - len(wind_cdir)) * " "
            gust_padding = (4 - len(wind_gust_spd)) * " "
            summary_padding = (13 - len(
                wind_padding + wind_spd + cdir_padding +
                wind_cdir + gust_padding + wind_gust_spd
            )) * " "
            if hourly:
                hod = datetime.fromtimestamp(day.get('ts')).strftime('%H:00')
                temp = "{:-03.1f}".format(float(day.get('temp')))
                app_temp = "{:-03.1f}".format(float(day.get('app_temp')))
                precip_prob = day.get('precip_prob')
                if not precip_prob or float(precip_prob) == 0.0:
                    precip_prob = '  ---'
                else:
                    precip_prob = '{:4d}%'.format(int(float(precip_prob) * 100))
                summary = day.get("weather").get("description")
                summary_padding = (6 - (len(wind_spd))) * " "
                block.append(f"{hod}:  {temp}°F " +
                    f" {app_temp}°F  {precip_prob} " +
                    f" {wind_padding}{wind_spd} {cdir_padding}{wind_cdir}" +
                    f" {gust_padding}({wind_gust_spd}) {summary_padding}{summary}")
            else:
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
                summary = day.get("weather").get("description")
                high_padding = (5 - len(max_temp)) * " "
                low_padding = (5 - len(min_temp)) * " "
                prcp_padding = (4 - len(prcp)) * " "
                if snow_found:
                    snow_padding = (6 - len(snow)) * " "
                    block.append(f"{dow}: {high_padding}{max_temp}°F " +
                        f"{low_padding}{min_temp}°F  {prcp_padding}{prcp} " +
                        f"{snow_padding}{snow}" +
                        f" {wind_padding}{wind_spd} {cdir_padding}{wind_cdir}" +
                        f" {gust_padding}({wind_gust_spd}) {summary_padding}{summary}")
                else:
                    block.append(f"{dow}: {high_padding}{max_temp}°F " +
                        f"{low_padding}{min_temp}°F  {prcp_padding}{prcp}" +
                        f" {wind_padding}{wind_spd} {cdir_padding}{wind_cdir}" +
                        f" {gust_padding}({wind_gust_spd}) {summary_padding}{summary}")
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
        hourly = False
        if days > 1:
            weather_info = self.__get_daily_weather_data(int(days), datecode, zipcode)
        else:
            hourly = True
            weather_info = self.__get_hourly_weather_data(days * 24, datecode, zipcode)
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
        if table or hourly:
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
        str_command = " ".join(command).lower()
        return "notable" in str_command or "no table" in str_command


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
                    if token == "hours":
                        return number * numbered[token]
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
            if days > 16:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': f"I'm sorry <@{request['user']}>, " +
                            "16 days is the longest forecast I can make.",
                    }
                )
                days = 16
            zipcode = self.__get_zipcode(command)
            if days < 0:
                datecode = (
                    datetime.now() + timedelta(days=days)
                ).strftime('%Y%m%d000000')
                days = days * -1
            else:
                datecode = datetime.now().strftime('%Y%m%d000000')
            try:
                table = True
                if self.__is_notable_request(command):
                    table = False
                elif self.__is_table_request(command):
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
                            'emojify': False,
                        }
                    )
                else:
                    response = {
                        'channel': request['channel'],
                        'blocks': forecast,
                        'emojify': False,
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
