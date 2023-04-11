from . import plugin
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from urllib.parse import quote

import json
import moonbeam_utils
import requests

class AutoScooglePlugin(plugin.NoBotPlugin):
    def __google_search(self, search_term):
        service = build("customsearch", "v1", developerKey=self._config.get('AUTOSCOOGLE_API_KEY'))
        res = service.cse().list(q=search_term, cx=self._config.get('AUTOSCOOGLE_CSE_ID'), num=1).execute()
        if 'items' in res.keys():
            return res['items'][0]
        self._log.debug(f"Google Search result: {json.dumps(res, indent=2)}")
        return None

    def __get_page_description(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        og_desc = soup.find("meta", property="og:description")
        twitter_desc = soup.find("meta", property="twitter:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"]
        if twitter_desc and twitter_desc.get("content"):
            return twitter_desc["content"]
        return None

    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        subject = None
        text = request.get('text', '').lower()

        if "<" in text or ">" in text or "@" in text:
            for word in text.split():
                if "<" in word or ">" in word or "@" in word:
                    text = text.replace(word, "")

        for trigger in self._config['AUTOSCOOGLE_TRIGGERS']:
            if trigger in text.lower():
                if trigger.startswith("what"):
                    subject = text
                elif trigger.startswith("who") or trigger.startswith("autoscoogle"):
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
            if result is None:
                return []
            url = result.get('link', result.get('formattedUrl'))
            if not url:
                return []
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

            snippet = self.__get_page_description(url)
            if not snippet and ("htmlSnippet" in result.keys() or "snippet" in result.keys()):
                snippet = moonbeam_utils.html_to_markdown(result.get("htmlSnippet", result.get("snippet")))

            if snippet:
                attachments.append(
                    {
                        "mrkdwn_in": ["text"],
                        "text": snippet,
                    }
                )

            responses.append(
                {
                    'channel': request['channel'],
                    'text': 'I Auto-Scoogled that for you:',
                    'attachments': attachments,
                }
            )
        return responses
