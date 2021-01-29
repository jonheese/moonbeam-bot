from . import plugin
from profanity import profanity
import json
import os


class GraciousPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        pleasantries_file = self._config.get('PLEASANTRIES_FILE')
        if pleasantries_file:
            with open(os.path.join(os.path.dirname(__file__), "..", pleasantries_file), 'r') as f:
                self.__pleasantries = json.load(f)
        else:
            raise RuntimeError(f"Unable to locate pleasantries file {pleasantries_file}")


    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        request_text = request['text']
        rude = False
        if "moonbeam" in request_text.lower():
            for word in request_text.split():
                if profanity.contains_profanity(word):
                    responses.append(
                        {
                            'channel': request['channel'],
                            'text': f"There's no need to be rude, <@{request['user']}>! :face_with_raised_eyebrow:",
                        }
                    )
                    rude = True
                    break
            if not rude:
                for pleasantry in self.__pleasantries:
                    if pleasantry in request_text.lower():
                        responses.append(
                            {
                                'channel': request['channel'],
                                'text': f"You're welcome, <@{request['user']}>! :grin:",
                                'attachments': [
                                    {
                                      "type": "image",
                                      "title": {
                                        "type": "plain_text",
                                        "text": "Thanks, Moonbeam"
                                      },
                                      "block_id": "image4",
                                      "image_url": "https://slack-files.com/T0TGU21T2-F01LCND36SE-1478259442",
                                      "alt_text": "Thanks, Moonbeam."
                                    }
                                ],
                            }
                        )
                        break
        return responses
