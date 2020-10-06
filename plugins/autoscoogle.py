from . import plugin
from urllib.parse import quote

import json

class AutoScooglePlugin(plugin.Plugin):
    def __init__(self):
        super().__init__()
        self._load_config_vars(['AUTOSCOOGLE_USERS', 'AUTOSCOOGLE_TRIGGERS'])

    def receive(self, request):
        responses = []
        user = request['user']
        if user in self._config.get("AUTOSCOOGLE_USERS"):
            # Potential auto-scoogle request
            subject = None
            text = request.get('text', '')
            for trigger in self._config['AUTOSCOOGLE_TRIGGERS']:
                if trigger in text.lower():
                    subject = text.split(trigger)[1].split("?")[0]
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
