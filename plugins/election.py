from . import plugin
from datetime import datetime
from time import sleep
import threading

class ElectionPlugin(plugin.Plugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__web_client = web_client
        self.__prediction = ''
        threading.Thread(target=self.__timer_thread, daemon=True).start()


    def __timer_thread(self):
        while True:
            if datetime.now().strftime("%S") == "00":
                self._log.debug("Grabbing results file...")
                try:
                    with open("/tmp/output.txt", 'r') as fp:
                        prediction = fp.read()
                    if prediction != self.__prediction:
                        self.__prediction = prediction
                        self.__post_message(channel="politics", text=prediction)
                except Exception as e:
                    self._log.exception(f"Encountered a Slack API Error posting message: {e}")
            sleep(1)


    def __post_message(self, channel, text):
        self._log.info(f"posting message in channel {channel}:")
        try:
            slack_response = self.__web_client.chat_postMessage(
                channel=channel,
                text=text,
            )
        except SlackApiError as e:
            self._log.exception(f"Encountered a Slack API Error posting message: {e.response['error']}")
