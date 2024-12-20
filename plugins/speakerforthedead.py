#!env/bin/python3

from . import plugin

import aiocron
import asyncio

import arrow
import feedparser
import re

class SpeakerForTheDeadPlugin(plugin.NoBotPlugin):

    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)

        self.last_checked = arrow.now()

        @aiocron.crontab('00 * * * *')  # Hourly at the top of the hour
        @asyncio.coroutine
        def check_feed():
            self._log.info("SpeakerForTheDead hourly TMZ check")
            news = feedparser.parse(self._config.get("TMZ_RSS_URI"))

            for entry in news.entries:
                self._log.info(f"Checking entry {entry.title}")
                for trigger in self._config.get("TRIGGERS"):
                    if re.compile(r'\b({0})\b'.format(re.escape(trigger)), flags=re.IGNORECASE).search(entry.title) and \
                            arrow.get(entry.updated) > self.last_checked:
                        yield from self.__post_message(
                            "#random",
                            f"*Speaker For The Dead:*\n{entry.title}\n{entry.link}"
                        )
                        break

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
