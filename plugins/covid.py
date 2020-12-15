import requests
from time import time
from . import plugin

class COVIDPlugin(plugin.NoBotPlugin):
    __covid_stats = {
        'world': {
            'deaths': -1,
            'cases': -1,
            'recovered': -1,
        },
        'us': {
            'deaths': -1,
            'cases': -1,
            'recovered': -1,
        },
        'timestamp': 0,
    }


    def __get_covid_stats(self):
        if self.__covid_stats['timestamp'] + 60 >= time():
            return
        tmpfile = '/tmp/states.csv'
        urls = {
            'world': 'https://www.worldometers.info/coronavirus/',
            'us': 'https://www.worldometers.info/coronavirus/country/us/',
        }

        for scope in urls.keys():
            r = requests.get(urls[scope])
            self.__covid_stats['timestamp'] = time()
            with open(tmpfile, 'wb') as f:
                f.write(r.content)
            with open(tmpfile, 'r') as f:
                lines = f.readlines()
            deaths_found = False
            cases_found = False
            recovered_found = False
            line_count = 0
            for line in lines:
                if not deaths_found and 'Deaths' in line:
                    self.__covid_stats[scope]['deaths'] = line.split()[line.split().index('Deaths') - 1]
                    deaths_found = True
                if not cases_found and 'Cases' in line:
                    self.__covid_stats[scope]['cases'] = line.split()[line.split().index('Cases') - 1]
                    cases_found = True
                if not recovered_found and 'Recovered' in line:
                    self.__covid_stats[scope]['recovered'] = lines[line_count + 2].split('>')[1].split('<')[0]
                    recovered_found = True
                if cases_found and deaths_found and recovered_found:
                    break
                line_count += 1


    def __get_covid_message(self, stat):
        self.__get_covid_stats()
        if stat == 'rates':
            world_pop = 7800000000
            us_pop = 327200000
            world_death_rate = round(float(self.__covid_stats['world']['deaths'].replace(',','')) * 100 / float(self.__covid_stats['world']['cases'].replace(',','')), 2)
            world_recovery_rate = round(float(self.__covid_stats['world']['recovered'].replace(',','')) * 100 / float(self.__covid_stats['world']['cases'].replace(',','')), 2)
            world_case_rate = round(float(self.__covid_stats['world']['cases'].replace(',','')) * 100 / float(world_pop), 4)
            world_death_chance = round(world_death_rate * world_case_rate / 100, 4)
            us_death_rate = round(float(self.__covid_stats['us']['deaths'].replace(',','')) * 100 / float(self.__covid_stats['us']['cases'].replace(',','')), 2)
            us_recovery_rate = round(float(self.__covid_stats['us']['recovered'].replace(',','')) * 100 / float(self.__covid_stats['us']['cases'].replace(',','')), 2)
            us_case_rate = round(float(self.__covid_stats['us']['cases'].replace(',','')) * 100 / float(us_pop), 4)
            us_death_chance = round(us_death_rate * us_case_rate / 100, 4)
            return f"The COVID-19 death rate is *{world_death_rate}%* worldwide, and *{us_death_rate}%* in the US.\n" + \
                f"The COVID-19 recovery rate is *{world_recovery_rate}%* worldwide, and *{us_recovery_rate}%* in the US.\n" + \
                f"The COVID-19 case rate is *{world_case_rate}%* worldwide, and *{us_case_rate}%* in the US.\n" + \
                f"The COVID-19 chance of death is *{world_death_chance}%* worldwide, and *{us_death_chance}%* in the US."
        else:
            percentage = round(float(self.__covid_stats['us'][stat].replace(',','')) * 100 / float(self.__covid_stats['world'][stat].replace(',','')), 2)
            return f"There are currently *{self.__covid_stats['world'][stat]}* COVID-19 {stat} worldwide, with *{self.__covid_stats['us'][stat]} ({percentage}%%)* of those {stat} in the US"


    def receive(self, request):
        if super().receive(request) is False:
            return False
        channel, text = (request['channel'], request['text'])
        messages = []
        if "covid-stats" in text.lower():
            messages.append(self.__get_covid_message(stat='deaths'))
            messages.append(self.__get_covid_message(stat='recovered'))
            messages.append(self.__get_covid_message(stat='cases'))
            messages.append(self.__get_covid_message(stat='rates'))
        if "covid-deaths" in text.lower():
            messages.append(self.__get_covid_message(stat='deaths'))
        if "covid-cases" in text.lower():
            messages.append(self.__get_covid_message(stat='cases'))
        if "covid-recovery" in text.lower():
            messages.append(self.__get_covid_message(stat='recovered'))
        if "covid-rates" in text.lower():
            messages.append(self.__get_covid_message(stat='rates'))
        responses = []
        for message in messages:
            responses.append(
                {
                    'text': message,
                    'channel': channel,
                }
            )
        return responses
