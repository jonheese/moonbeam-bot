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

    def _get_real_name_by_user_id(self, user_id):
        info = self._web_client.users_info(user=user_id)
        real_name = None
        if info.get('user'):
            real_name = info.get('user').get('real_name')
        return real_name

    def receive(self, message):
        pass

    def typing(self, data):
        pass

    def get_trigger_words(self):
        return []

    def store_global_trigger_words(self, words):
        pass


class NoBotPlugin(Plugin):
    def receive(self, message):
        # We want to ignore all ephemeral/empty messages and all messages from ourselves and Slackbot
        if message and 'text' in message.keys() and not message.get('is_ephemeral') and \
                message.get('bot_id') != self._config.get("BOT_ID") and message.get('username') != "slackbot":
            return True
        else:
            return False
