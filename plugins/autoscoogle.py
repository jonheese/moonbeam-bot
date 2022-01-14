from . import plugin
from googleapiclient.discovery import build
from urllib.parse import quote

import json
import requests

class AutoScooglePlugin(plugin.NoBotPlugin):
    def __google_search(self, search_term):
        service = build("customsearch", "v1", developerKey=self._config.get('AUTOSCOOGLE_API_KEY'))
        res = service.cse().list(q=search_term, cx=self._config.get('AUTOSCOOGLE_CSE_ID'), num=1).execute()
        return res['items'][0]

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
            result = self.__google_search(
                search_term=subject,
            )
            url = result.get('formattedUrl')
            if url:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': f"I Auto-Scoogled that for you:\n{url}",
                    }
                )
        return responses
