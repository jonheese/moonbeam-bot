#!/usr/local/bin/python3

from plugins.autoscoogle import AutoScooglePlugin
from plugins.command import CommandPlugin
from plugins.covid import COVIDPlugin
from plugins.dbstore import DBStorePlugin
from plugins.dice import DicePlugin
from plugins.help import HelpPlugin
from plugins.moonbeam import MoonbeamPlugin
from plugins.quotable import QuotablePlugin
from plugins.trigger import TriggerPlugin

from slack import RTMClient
from slack.errors import SlackApiError

import json
import logging
import os
from time import sleep

class Moonbeam:
    def __init__(self, *, plugins: list=list(), no_bot_plugins: list=list()):
        self.__plugins = plugins
        self.__no_bot_plugins = no_bot_plugins
        logging.basicConfig(
            level=os.environ.get("LOGLEVEL", "DEBUG"),
            format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
        )
        self.__log = logging.getLogger(type(self).__name__)
        self.__log.info("Starting moonbeam")
        with open('/usr/local/moonbeam-bot/config.json', 'r') as f:
            self.__config = json.load(f)
        rtm_client = RTMClient(
            token=self.__config.get("BOT_TOKEN"),
        )
        rtm_client.run_on(event='message')(self.__process_message)
        rtm_client.start()


    def __post_message(self, response):
        channel = response.get('channel')
        text = response.get('text')
        attachments = response.get('attachments')
        as_user = response.get('as_user')
        self.__log.info(f"posting message in channel {channel} (as_user={as_user}):")
        try:
            slack_response = self.__web_client.chat_postMessage(
                channel=channel,
                text=text,
                attachments=attachments,
                as_user=as_user,
            )
        except SlackApiError as e:
            self.__log.exception(f"Encountered a Slack API Error posting message: {e.response['error']}")


    def __plugin_message(self, request, plugins):
        for plugin in plugins:
            try:
                for response in plugin.receive(request):
                    self.__post_message(response)
            except Exception as e:
                self.__log.exception(f"Encountered an exception responding to message: {e}")


    def __process_message(self, **payload):
        message = payload['data']
        self.__web_client = payload['web_client']
        if message and 'text' in message.keys() and not message.get('is_ephemeral'):
            self.__log.info(json.dumps(message, indent=2))
            if message.get('bot_id') != self.__config.get("BOT_ID") and message.get('username') != "slackbot":
                self.__plugin_message(message, self.__no_bot_plugins)
            self.__plugin_message(message, self.__plugins)
        else:
            self.__log.debug("Not responding to message:")
            self.__log.debug(json.dumps(message, indent=2))


if __name__ == "__main__":
    moonbeam = Moonbeam(
        plugins={
            DBStorePlugin(),
        },
        no_bot_plugins={
            AutoScooglePlugin(),
            CommandPlugin(),
            COVIDPlugin(),
            DicePlugin(),
            HelpPlugin(),
            MoonbeamPlugin(),
            QuotablePlugin(),
            TriggerPlugin(),
        },
    )
