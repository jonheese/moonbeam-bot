from . import plugin
from random import randint, seed
from traceback import print_stack
import json
import re

class TriggerPlugin(plugin.Plugin):
    def __init__(self):
        super().__init__()
        self.__triggers = self.__read_triggers()
        self.__confirmations = {}


    def __read_triggers(self):
        with open(self._config.get('TRIGGERS_FILE'), 'r') as f:
            return json.load(f)


    def __add_trigger(self, trigger, reply, check_for_dupe=True):
        self.__triggers = self.__read_triggers()
        self._log.debug(f"Adding trigger: {trigger} => {reply}")
        if check_for_dupe and trigger in self.__triggers.keys() and reply in self.__triggers[trigger]:
            return trigger
        else:
            if trigger not in self.__triggers.keys():
                self.__triggers[trigger] = [reply]
            else:
                self.__triggers[trigger].append(reply)
            with open(self._config.get('TRIGGERS_FILE'), 'w') as f:
                json.dump(self.__triggers, f, indent=2)
            return


    def __get_trigger(self, message, channel):
        responses = []
        for trigger in self.__triggers:
            if re.search(fr'\b{trigger}\b', message, flags=re.IGNORECASE):
                replies = self.__triggers[trigger]
                seed()
                reply = replies[randint(0, 1000) % len(replies)]
                responses.append(
                    self.__build_message(
                        text=reply,
                        channel=channel,
                    )
                )
        return responses


    def __build_message(self, text, channel):
        return {
            'channel': channel,
            'text': text,
        }


    def __show_usage(self, request):
        text = f"<@{request['user']}>, to add a trigger to my database, your message must follow the format: `Moonbeam add-trigger <trigger> - <reply>`"
        return self.__build_message(text, request['channel'])


    def __add_success(self, request, trigger, reply, responses):
        responses.append(
            self.__build_message(
                text=f"Okay, <@{request['user']}>, I added the following trigger to my database:",
                channel=request['channel'],
            )
        )
        responses.append(
            self.__build_message(
                text=f'"{trigger}" => "{reply}"',
                channel=request['channel'],
            )
        )
        return responses


    def receive(self, request):
        responses = []
        text = request['text']
        channel = request['channel']
        user = request['user']
        if text.lower().startswith('moonbeam') and "add-trigger" in request['text'].lower():
            command_index = -1
            index = -1
            words = text.split()
            for word in words:
                index += 1
                if word == "add-trigger":
                    command_index = index
                    break
            if command_index >= 0:
                try:
                    trigger_and_reply = " ".join(words[command_index+1:])
                    trigger = trigger_and_reply.split(' - ')[0]
                    reply = trigger_and_reply.split(' - ')[1]
                    dupe_trigger = self.__add_trigger(trigger, reply)
                    if not dupe_trigger:
                        responses = self.__add_success(request, trigger, reply, responses)
                    else:
                        responses.append(self.__build_message(f"Sorry, <@{user}>, but that trigger/reply looks very similar to this one, which is already in my database:", channel))
                        responses.append(
                            self.__build_message(
                                text=f'"{dupe_trigger}" => "{reply}"',
                                channel=channel,
                            )
                        )
                        responses.append(self.__build_message(f"If you are sure you still want to add it, send me a DM saying \"add trigger\" and I'll take care of it for you. :thumbsup:\n" + \
                                         "Otherwise, you can send me a DM saying \"cancel trigger\" and we'll forget this ever happened. :wink:", channel))
                        self.__confirmations[user] = (trigger, reply)
                except Exception as e:
                    self._log.exception(e)
                    responses.append(self.__show_usage(request))
            else:
                responses.append(self.__show_usage(request))
        if text.lower() == "add trigger" or text.lower() == "cancel trigger":
            if user in self.__confirmations.keys():
                if text.lower() == "add trigger":
                    (trigger, reply) = self.__confirmations[user]
                    self.__add_trigger(
                        trigger=trigger,
                        reply=reply,
                        check_for_dupe=False
                    )
                    responses = self.__add_success(request, trigger, reply, responses)
                    self._log.debug(f"Removing quote confirmation for user {user}: {trigger} => {reply}")
                    self.__confirmations.pop(user)
                else:
                    self.__confirmations.pop(user)
                    responses.append(self.__build_message("Okay, request cancelled. :speak_no_evil:", channel))
            else:
                responses.append(self.__build_message(f":thinking_face: Ummm... I don't think there's any trigger to {text.lower().split()[0]}...", channel))
        if not responses:
            responses = self.__get_trigger(text, channel)
        return responses
