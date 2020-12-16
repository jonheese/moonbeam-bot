from . import plugin
from urllib.parse import quote

import json
import requests

class AutoScooglePlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        user = request['user']
        subject = None
        text = request.get('text', '').lower()
        for trigger in self._config['AUTOSCOOGLE_TRIGGERS']:
            if trigger in text.lower():
                if trigger.startswith("who"):
                    subject = " ".join(text.split(trigger)[1:])
                else:
                    subject = trigger.join(text.split(trigger)[1:])
                if "?" in subject:
                    subject = subject.split("?")[0]
                self._log.debug(f"################## Subject is {subject}")
                break
        if subject:
            res = requests.get(f'https://www.google.com/search?q={quote(subject)}&btnI')
            res.raise_for_status()
            if res.url.startswith('https://www.google.com/url?q='):
                url = "=".join(res.url.split('=')[1:])
            else:
                url = res.url
            responses.append(
                {
                    'channel': request['channel'],
                    'text': f"I Auto-Scoogled that for you:\n{url}",
                }
            )
        return responses
