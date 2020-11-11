from . import plugin
from urllib.parse import quote

import json

class AutoScooglePlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        user = request['user']
        if user in self._config.get("AUTOSCOOGLE_USERS"):
            # Potential auto-scoogle request
            subject = None
            text = request.get('text', '')
            for trigger in self._config['AUTOSCOOGLE_TRIGGERS']:
                if trigger in text.lower():
                    subject = text.split(trigger)[1]
                    if "?" in subject:
                        subject = subject.split("?")[0]
                    break
            if subject:
                scoogle = f"I Auto-Scoogled that for you:\nhttp://www.google.com/search?q={quote(subject)}"
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': scoogle,
                    }
                )
        return responses
