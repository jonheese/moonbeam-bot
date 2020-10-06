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
        try:
            with open('/usr/local/moonbeam-bot/config.json', 'r') as f:
                self._config = json.load(f)
        except:
            self._config = {}

    def _load_config_vars(self, names):
        for name in names:
            if self._config.get(name) is None:
                try:
                    self._config[name] = json.loads(os.environ.get(name, ""))
                except json.decoder.JSONDecodeError:
                    self._config[name] = os.environ.get(name, "")

    def receive(self, message):
        pass
