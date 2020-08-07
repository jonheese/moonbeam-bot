import logging
import os
import json


class Plugin:
    def __init__(self):
        logging.basicConfig(
            level=os.environ.get("LOGLEVEL", "DEBUG"),
            format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
        )
        self._log = logging.getLogger(type(self).__name__)
        with open('/usr/local/moonbeam-bot/config.json', 'r') as f:
            self._config = json.load(f)


    def receive(self, message):
        pass

