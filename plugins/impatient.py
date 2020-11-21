from . import plugin
from random import randint, seed
from time import time

class ImpatientPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__typing_by_user_channel = {}
        self.__taunts_by_user_channel = {}


    def __get_quip(self, user):
        seed()
        quip = self._config['RESPONSES'][randint(0, 1000) % len(self._config['RESPONSES'])].replace('#USER#', user)
        return quip


    def receive(self, message):
        if 'user' in message.keys() and 'channel' in message.keys():
            self.__typing_by_user_channel[f"{message['user']}_{message['channel']}"] = time()
        return []


    def typing(self, data):
        responses = []
        user = data['user']
        channel = data['channel']
        user_channel = f"{user}_{channel}"
        min = self._config['RESPONSE_THRESHOLD_SECS']
        max = self._config['MAX_THRESHOLD_SECS']
        cooldown = self._config['COOLDOWN_SECS']
        now = time()
        last_taunt = self.__taunts_by_user_channel.get(user_channel, 0)
        if now - last_taunt > cooldown:
            last_typing_start = self.__typing_by_user_channel.get(user_channel, 0)
            interval = now - last_typing_start
            if interval > max:
                self.__typing_by_user_channel[user_channel] = now
                self._log.debug(f"Setting typing start timestamp for user {user} in {channel} to now because {interval} is greater than {max}")
            elif interval > min:
                self._log.debug(f"Taunting user {user} in channel {channel} because {interval} is between {min} and {max}")
                seed()
                # Only actually taunt 1 time out of 10
                if randint(0, 9) == 0:
                    responses.append(
                        {
                            'channel': channel,
                            'text': self.__get_quip(user),
                        }
                    )
                # But still reset timers anyway
                self.__typing_by_user_channel[user_channel] = 0
                self.__taunts_by_user_channel[user_channel] = now
            else:
                self._log.debug(f"Not taunting user {user} because {interval} is not between {min} and {max}")
        else:
            self._log.debug(f"Not taunting user {user} because {now - last_taunt} is less than {cooldown}")
        return responses
