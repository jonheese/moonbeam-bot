import json
import logging
import os


class Plugin:
    def __init__(self, web_client, plugin_config):
        logging.basicConfig(
            level=os.environ.get("LOGLEVEL", "DEBUG"),
            format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
        )
        self._log = logging.getLogger(type(self).__name__)
        if plugin_config:
            self._config = plugin_config
        else:
            self._config = {}
        self._web_client = web_client


    def receive(self, message):
        pass


    def typing(self, data):
        pass


class NoBotPlugin(Plugin):
    def receive(self, message):
        # We want to ignore all ephemeral/empty messages and all messages from ourselves and Slackbot
        if message and 'text' in message.keys() and not message.get('is_ephemeral') and \
                message.get('bot_id') != self._config.get("BOT_ID") and message.get('username') != "slackbot":
            return True
        else:
            return False
