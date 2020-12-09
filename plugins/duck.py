from . import plugin

class DuckPlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if "duck" in request['text'].lower():
            self._log.debug(f"Saw duckable message: {request['text']}")
            responses.append(
                {
                    'timestamp': request['ts'],
                    'channel': request['channel'],
                    'name': 'duck'
                }
            )
        return responses
