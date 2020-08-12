from . import plugin
from random import randint, seed
import os
import json


class MoonbeamPlugin(plugin.Plugin):
    __moonbeams = [
        {
            "name": "Moonbeam",
            "image_url": "https://slack-files.com/T0TGU21T2-FFYTWBGA2-4e153c7af7",
            "frequency_score": 3,
            "words": None
        },
        {
            "name": "Super Moonbeam",
            "image_url": "https://slack-files.com/T0TGU21T2-FFWT7PSF3-b6f941711f",
            "freqency_score": 2,
            "words": None
        },
    ]


    def __init__(self):
        super().__init__()
        with open(self._config.get('WORDS_FILE'), 'r') as f:
            self.__words = json.load(f)
        self.__reset_moonbeam()


    def __reset_moonbeam(self, moonbeam_name=None):
        for moonbeam in self.__moonbeams:
            if moonbeam_name == None or moonbeam['name'] == moonbeam_name:
                self._log.info(f"Initializing {moonbeam['name']}")
                moonbeam['words'] = self.__get_ten_new_words()


    def __get_moonbeam_words(self, moonbeam_name=None):
        message = ""
        for moonbeam in self.__moonbeams:
            if moonbeam_name == None or moonbeam['name'] == moonbeam_name:
                message = f"{message}{moonbeam['name']}: {', '.join(moonbeam['words'])}\n"
        return message[:-1]


    def __get_ten_new_words(self):
        ten_words = []
        count = 0
        while count < 10:
            seed()
            rand_id = randint(0, len(self.__words)-1)
            ten_words.append(self.__words[rand_id]["word"])
            count = count + 1
        self._log.debug(ten_words)
        return ten_words


    def receive(self, request):
        responses = []
        # Check for master command
        if request.get('channel') == self._config.get("MASTER_CHANNEL_ID") and \
                request.get('user') == self._config.get("MASTER_ID"):
            command = request['text']
            moonbeam_name = None
            if command.startswith("reset"):
                if len(command.split(" ")) > 1:
                    moonbeam_name = " ".join(command.split(" ")[1:])
                self.__reset_moonbeam(moonbeam_name)
            if command == "words" or command.startswith("reset"):
                responses.append(
                    {
                        'channel': self._config.get("MASTER_CHANNEL_ID"),
                        'text': self.__get_moonbeam_words(moonbeam_name),
                        'as_user': False
                    }
                )
        # Check for moonbeam words
        for moonbeam in self.__moonbeams:
            message_words = request['text'].lower().split(" ")
            if not moonbeam['words']:
                reset_moonnbeam(moonbeam['name'])
            for word in moonbeam['words']:
                for message_word in message_words:
                    # Strip off all non-alpha chars (eg. punctuation)
                    message_word = "".join([i for i in str(message_word) if i.isalpha()])
                    if word == message_word:
                        self._log.debug(json.dumps(request, indent=2))
                        responses.append(
                            {
                                'channel': request['channel'],
                                'text': f"{moonbeam['name']} because: *{word}*\n{moonbeam['image_url']}",
                            }
                        )
                        self.__reset_moonbeam(moonbeam['name'])
                        break
            if responses:
                break
        return responses
