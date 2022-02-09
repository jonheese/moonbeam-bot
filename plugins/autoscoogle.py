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
            self._log.debug(json.dumps(result, indent=2))
            url = result.get('link', result.get('formattedUrl'))
            attachments = [
                {
                    "mrkdwn_in": ["text"],
                    "text": url,
                }
            ]
            if "pagemap" in result.keys():
                pagemap = result["pagemap"]
                image_url = None
                if "cse_thumbnail" in pagemap.keys() and "src" in pagemap["cse_thumbnail"][0].keys():
                    image_url = pagemap["cse_thumbnail"][0]["src"]
                elif "cse_image" in pagemap.keys() and "src" in pagemap["cse_image"][0].keys():
                    image_url = pagemap["cse_image"][0]["src"]
                if image_url:
                    attachments[0]["image_url"] = image_url
                if "metatags" in pagemap and "og:title" in pagemap["metatags"][0].keys():
                    attachments[0]["title"] = pagemap["metatags"][0]["og:title"]
                elif result.get("title"):
                    attachments[0]["title"] = result["title"]
            if url:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': 'I Auto-Scoogled that for you:',
                        'attachments': attachments,
                    }
                )
        return responses
