#!env/bin/python3

from . import plugin

import aiocron
import asyncio
import random
import requests


class TheWeekendPlugin(plugin.NoBotPlugin):

    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)

        @aiocron.crontab('00 17 * * FRI')
        @asyncio.coroutine
        def friday():

            result = requests.get(
                self._config.get('GIPHY_API_URL'),
                params={
                    'q': self._config.get('GIPHY_API_QUERY'),
                    'api_key': self._config.get('GIPHY_API_KEY'),
                    'limit': self._config.get('GIPHY_API_LIMIT'),
                }
            )

            choices = [ x['url'] for x in result.json()['data'] ]

            yield from self.__post_message(
                "#random",
                f"Ladies and Gentlemen, the weekend\n{random.choice(choices)}"
            )

    @asyncio.coroutine
    def __post_message(self, channel, text):
        self._log.info(f"posting message in channel {channel}:")
        try:
            slack_response = self._web_client.chat_postMessage(
            channel=channel,
            text=text,
            )
        except SlackApiError as e:
            self._log.exception(f"Encountered a Slack API Error posting message: {e.response['error']}")
