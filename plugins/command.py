from . import plugin
import json


class CommandPlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        # Check for master command
        if request.get('channel') == self._config.get("MASTER_CHANNEL_ID") and \
                request.get('user') == self._config.get("MASTER_ID"):
            command = request['text']
            if command.split()[0] == "post":
                room_name = command.split()[1]
                message = " ".join(command.split()[2:])
                responses.append(
                    {
                        'channel': room_name,
                        'text': message,
                    }
                )
        return responses
