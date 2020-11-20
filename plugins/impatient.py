from . import plugin
from random import randint, seed
from time import time

class ImpatientPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__typing_by_user = {}
        self.__taunts_by_user = {}


    def __get_quip(self, user):
        seed()
        quip = self._config['RESPONSES'][randint(0, 1000) % len(self._config['RESPONSES'])].replace('#USER#', user)
        return quip


    def receive(self, message):
        if 'user' in message.keys():
            self.__typing_by_user[message['user']] = time()
        return []


    def typing(self, data):
        responses = []
        user = data['user']
        min = self._config['RESPONSE_THRESHOLD_SECS']
        max = self._config['MAX_THRESHOLD_SECS']
        cooldown = self._config['COOLDOWN_SECS']
        now = time()
        last_taunt = self.__taunts_by_user.get(user, 0)
        if now - last_taunt > cooldown:
            last_typing_start = self.__typing_by_user.get(user, 0)
            interval = now - last_typing_start
            if interval > max:
                self.__typing_by_user[user] = now
                self._log.debug(f"Setting typing_by_user for user {user} to now because {interval} is greater than {max}")
            elif interval > min:
                self._log.debug(f"Taunting user {user} because {interval} is between {min} and {max}")
                responses.append(
                    {
                        'channel': data['channel'],
                        'text': self.__get_quip(user),
                    }
                )
                self.__typing_by_user[user] = 0
                self.__taunts_by_user[user] = now
            else:
                self._log.debug(f"Not taunting user {user} because {interval} is not between {min} and {max}")
        else:
            self._log.debug(f"Not taunting user {user} because {now - last_taunt} is less than {cooldown}")
        return responses
