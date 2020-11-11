from . import plugin
from urllib.parse import quote_plus

class ArchivePlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if request['text'].lower().startswith("moonbeam archive"):
            self._log.debug(f"Got archive request: {request['text']}")
            query = quote_plus(" ".join(request['text'].split()[2:]))
            responses.append(
                {
                    'channel': request['channel'],
                    'text': f"Here you go: https://slack-archive.istolethis.com/?q={query}",
                }
            )
            responses.append(
                {
                    'channel': request['channel'],
                    'text': "Remember, the username/password for the site are both `redtube`. :smile:",
                }
            )
        return responses
