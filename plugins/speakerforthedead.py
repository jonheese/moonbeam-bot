#!env/bin/python3

from . import plugin

import aiocron
import asyncio

import arrow
import feedparser

class SpeakerForTheDeadPlugin(plugin.NoBotPlugin):

    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)

        self.last_checked = arrow.now()

    @aiocron.crontab('00 * * * *')  # Hourly at the top of the hour
    @asyncio.coroutine
    def check_feed():

        news = feedparser.parse(self._config.get("TMZ_RSS_URI"))

        for entry in news.entries:
            if any([trigger in entry.title.lower() for trigger in self._config.get("TRIGGERS")]):
                if arrow.get(entry.updated) > self.last_checked:
                    yield from self.__post_message(
                        "#random",
                        f"{entry.title}\n{entry.link}"
                    )

        self.last_checked = arrow.now()

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
