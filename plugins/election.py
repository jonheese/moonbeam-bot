from . import plugin
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from time import sleep
from slack_sdk.errors import SlackApiError
import json
import requests


class ElectionPlugin(plugin.NoBotPlugin):

    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__prediction = ''
        self.__url = 'https://www.electionreturns.pa.gov/api/ElectionReturn/GET?' + \
                     'methodName=GetSummaryData&electionid=undefined&' + \
                     'electiontype=undefined&isactive=1'

        self.__prediction_file = '/usr/src/app/prediction.txt'
        try:
            with open(self.__prediction_file, 'r') as fp:
                self.__prediction = fp.read()
        except Exception as e:
            self._log(
                f'Encountered exception {e} trying to load prediction from ' +
                f'file {self.__prediction_file}, probably harmless'
            )

        scheduler = BackgroundScheduler()
        scheduler.add_job(self.__check_feed, 'cron', minute='*')
        scheduler.start()

    def __check_feed(self):
        self._log.info('Election Plugin checking election results')

        data = json.loads(json.loads(requests.get(self.__url).text))

        prediction = 'Current PA election results:```\n'
        for candidate in data['Election']['President of the United States'][0]['Statewide']:
            name_party = f'{candidate["CandidateName"]} ({candidate["PartyName"]}):'
            result = f'{candidate["Percentage"]}% ({candidate["Votes"]} votes)'
            spaces = ' ' * (10 - len(name_party) + len(result))
            prediction += f'{name_party}{spaces}{result}\n'
        prediction += '```'

        try:
            with open(self.__prediction_file, 'w') as fp:
                fp.write(prediction)
        except Exception as e:
            self._log(
                f'Encountered exception {e} trying to save prediction to ' +
                f'file {self.__prediction_file}, please investigate'
            )


        try:
            if prediction != self.__prediction:
                self.__prediction = prediction
                self.__post_message(channel="politics", text=prediction)
        except Exception as e:
            self._log.exception(f"Encountered a Slack API Error posting message: {e}")

    def __post_message(self, channel, text):
        self._log.info(f"posting message in channel {channel}:")
        try:
            slack_response = self._web_client.chat_postMessage(
                channel=channel,
                text=text,
            )
        except SlackApiError as e:
            self._log.exception(f"Encountered a Slack API Error posting message: {e.response['error']}")
