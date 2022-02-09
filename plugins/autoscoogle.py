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
                if trigger.startswith("what"):
                    subject = text
                elif trigger.startswith("who"):
                    subject = text.replace(trigger, "")
                else:
                    subject = "what is " + text.replace(trigger, "")
                if "?" in subject:
                    subject = subject.split("?")[0]
                self._log.debug(f"################## Subject is {subject}")
                break
        if subject:
            result = self.__google_search(
                search_term=subject,
            )
            url = result.get('link', result.get('formattedUrl'))
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"I Auto-Scoogled that for you:\n{url}",
                    }
                }
            ]
            if "pagemap" in result.keys():
                image_url = None
                if "cse_thumbnail" in result["pagemap"].keys() and "src" in result["pagemap"]["cse_thumbnail"][0].keys():
                    image_url = result["pagemap"]["cse_thumbnail"][0]["src"]
                elif "cse_image" in result["pagemap"].keys() and "src" in result["pagemap"]["cse_image"][0].keys():
                    image_url = result["pagemap"]["cse_image"][0]["src"]
                if image_url:
                    blocks[0]["accessory"] = {
                        "type": "image",
                        "image_url": image_url,
                        "alt_text": result.get("title"),
                    }
            if url:
                responses.append(
                    {
                        'channel': request['channel'],
                        'blocks': blocks,
                    }
                )
        return responses
