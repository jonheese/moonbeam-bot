from . import plugin
import json


class CommandPlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        conditionals = {}
        # Check for master command
        if self._config.get('OPEN_COMMAND') is True or \
                (request.get('channel') == self._config.get("MASTER_CHANNEL_ID") and \
                request.get('user') == self._config.get("MASTER_ID")):
            command = request['text']
            self._log.info(f'Got potential command: {command}')
            command_list = command.split()
            if len(command_list) > 1 and command_list[0].lower() == "moonbeam" and \
                    command_list[1].lower() == "post":
                room_name = command_list[2]
                message = command.replace(command_list[0], '').replace(command_list[1], '').replace(room_name, '')
                responses.append(
                    {
                        'channel': room_name,
                        'text': message,
                    }
                )
                self._log.info(json.dumps(responses[0], indent=2))
                conditionals = {
                    True: {
                        'channel': request.get('channel'),
                        'text': f"Okay, I've posted \"{message}\" for you in <#@CHANNEL@> :thumbsup:",
                        'mappings': {
                            '@CHANNEL@': room_name,
                        }
                    },
                    False: {
                        'channel': request.get('channel'),
                        'text': "I'm sorry, I had trouble posting this message for you: ```@ERROR@```",
                    },
                }
        return [responses, conditionals]

    def get_trigger_words(self):
        return [ "post" ]
