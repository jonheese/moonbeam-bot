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
            self._log.info(f'Got command: {command}')
            if command.split()[1] == "post":
                room_name = command.split()[2]
                message = " ".join(command.split()[3:])
                responses.append(
                    {
                        'channel': room_name,
                        'text': message,
                    }
                )
                self._log.info(json.dumps(responses[0], indent=2))
        return responses
