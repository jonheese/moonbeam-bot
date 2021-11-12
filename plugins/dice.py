from . import plugin
from profanity import profanity
from random import randint, seed
import json
import os
import re


class DicePlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        pleasantries_file = self._config.get('PLEASANTRIES_FILE')
        if pleasantries_file:
            with open(os.path.join(os.path.dirname(__file__), "..", pleasantries_file), 'r') as f:
                self.__pleasantries = json.load(f)
        else:
            raise RuntimeError(f"Unable to locate pleasantries file {pleasantries_file}")


    def __roll_dice(self, number, sides):
        results = []
        if number is None or number == "":
            number = 1
        else:
            number = int(number)
        for x in range(0, number):
            seed()
            results.append(randint(1, sides))
        return results


    def __check_for_match(self, word, dictionary):
        for entry in dictionary:
            pattern = re.compile(entry)
            if pattern.search(word):
                return True
        return False


    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if request['text'].lower().startswith("moonbeam") and "roll" in request['text'].split():
            orig_words = request['text'].split()[1:]
            words = request['text'].lower().split()[1:]
            rude = False
            pleased = False
            dice_pattern = re.compile("\d*d\d+(\+\d)*(-\d)*$")
            dices = []
            for word in words:
                if profanity.contains_profanity(word):
                    rude = True
                    continue
                # Strip all punctuation from the word so we can check if it's a dice roll
                for c in ".,?!":
                    word = word.replace(c, "")
                if not dice_pattern.match(word):
                    # if we haven't already been treated courteously, check for pleasantry
                    if not pleased and self.__check_for_match(word, self.__pleasantries):
                        pleased = True
                    # This word isn't a dice notation, so skip it
                    continue
                    # This word is a dice notation, add it to the dices
                dices.append(word)
            if rude:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': f"There's no need to be rude, <@{request['user']}>! :face_with_raised_eyebrow:",
                    }
                )
                return responses
            if not pleased:
                responses.append(
                    {
                        'channel': request['channel'],
                        'text': f"Ah ah ah, <@{request['user']}>, you didn't say the magic word... :face_with_monocle:",
                    }
                )
                return responses
            summary = "*Dice*    \t\t\t\t*Rolls*"
            total = 0
            max_roll = 0
            total_string = ""
            for dice in dices:
                add = 0
                minus = 0
                # Calculate max_roll adjustment for any modifiers
                if "+" in dice:
                    add = int(dice.split("+")[1])
                    max_roll = max_roll + 1
                    dice = dice.split("+")[0]
                elif "-" in dice:
                    minus = int(dice.split("-")[1])
                    max_roll = max_roll - 1
                    dice = dice.split("-")[0]
                split_dice = dice.split("d")
                results = self.__roll_dice(split_dice[0], int(split_dice[1]))
                dice_results = ""
                for result in results:
                    dice_results = f"{dice_results} {result}"
                    total_string = f"{total_string} + {result}"
                    total = total + int(result)
                    max_roll = max_roll + int(split_dice[1])
                if add != 0:
                    total = total + add
                    total_string = f"{total_string} + {add}"
                if minus != 0:
                    total = total - minus
                    total_string = f"{total_string} - {minux}"
                if total_string.startswith(" ") or total_string.startswith("+") or total_string.startswith("-"):
                    total_string = " ".join(total_string.split()[1:])
                padding = ""
                for x in range(0, (5-len(dice))*2):
                    padding = padding + " "
                if add != 0: dice = f"{dice}+{add}"
                if minus != 0: dice = f"{dice}-{minus}"
                if dice.startswith("d"): dice = f"1{dice}"
                summary = f"{summary}\n{dice}{padding}\t\t\t\t{dice_results}"
            if " " in total_string:
                total_string = f"{total_string} = {total}"
            else:
                total_string = str(total)

            image_url = None
            if total <= int(max_roll * 0.3):
                color = "danger"
                image_url = "https://slack-files.com/T0TGU21T2-FMLC3CUFL-04242147ee"
            elif total <= int(max_roll * 0.6):
                color = "warning"
            else:
                color = "good"
            attachments = {
                "text": f"<@{request['user']}> rolled a *{total_string}*\n{summary}",
                "color":color,
            }
            if image_url:
                attachments['image_url'] = "https://slack-files.com/T0TGU21T2-FMLC3CUFL-04242147ee"
            responses.append(
                {
                    'channel': request['channel'],
                    'text': '',
                    'attachments': [attachments],
                }
            )
        return responses

    def get_trigger_words(self):
        return [ "roll" ]
