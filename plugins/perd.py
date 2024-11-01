from . import plugin
from random import randint, seed
import os
import json
import time


class PerdHapleyPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        with open(os.path.join(os.path.dirname(__file__), '..', self._config.get('PERDS_FILE')), 'r') as f:
            self.__perds = json.load(f)
        self.__perd_image_url = self._config['PERD_IMAGE_URL']
        self.__random_size = self._config.get('RANDOM_SIZE', 20)
        self.__in_cooldown = False
        self.__cooldown_timer = 0

    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if self.__in_cooldown:
            if self.__cooldown_timer < self.__random_size:
                self.__cooldown_timer += 1
                return responses
            self.__cooldown_timer = 0
            self.__in_cooldown = False
        seed()
        # Roll d20 to see if we're Perding
        if randint(1, self.__random_size) == self.__random_size:
            self.__in_cooldown = True
            self.__cooldown_timer = 0
            now = time.strftime('%I:%M %p').lower()
            if now.startswith("0"):
                now = now[1:]
            quote = self.__perds[randint(0, len(self.__perds)-1)].replace(
                '@NAME@',
                self._get_real_name_by_user_id(request.get('user'))
            ).replace(
                '@TIME@',
                now
            )
            responses.append(
                {
                    'channel': request['channel'],
                    'text': quote,
                    'emojify': False,
                    'attachments': [
                         {
                           "type": "image",
                           "title": {
                             "type": "plain_text",
                             "text": "I'm Perd Hapley",
                           },
                           "block_id": "image4",
                           "image_url": self.__perd_image_url,
                           "alt_text": "I'm Perd Hapley",
                         }
                     ],
                }
            )
        return responses
