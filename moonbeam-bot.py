from time import sleep
from slackclient import SlackClient
from random import randint, seed
from quotes import quotes
from config import BOT_ID, BOT_TOKEN, JHEESE_ID, JHEESE_CHANNEL_ID, MASHAPE_KEY
from lxml import html
from profanity import profanity
import requests, json, re, traceback, string

#             Name              Image URL                                                   Frequency score     Words
moonbeams = [["Moonbeam",       "https://slack-files.com/T0TGU21T2-FFYTWBGA2-4e153c7af7",   3,                  None],
             ["Super Moonbeam", "https://slack-files.com/T0TGU21T2-FFWT7PSF3-b6f941711f",   2,                  None]]

with open('/usr/local/moonbeam-bot/words.json', 'r') as f:
    words = json.load(f)["data"]

with open('/usr/local/moonbeam-bot/pleasantries.json', 'r') as f:
    pleasantries = json.load(f)["data"]

def get_ten_new_words():
    return get_ten_new_words(3)


def get_ten_new_words(frequencyMin):
    count = 0
    words = []
    headers = {'X-Mashape-Key': MASHAPE_KEY}
    while count < 10:
        data = json.loads(requests.get('https://wordsapiv1.p.mashape.com/words/?random=true&hasDetails=frequency&frequencyMin=%s' % frequencyMin, headers=headers).content)
        if "frequency" not in data.keys():
            continue
        frequency = float(data["frequency"])
        word = data["word"]
        if frequency < 3:
            continue
        words.append(word)
        count = count + 1
    print(words)
    return words


def get_ten_new_words_static():
    ten_words = []
    count = 0
    while count < 10:
        seed()
        rand_id = randint(0, len(words)-1)
        ten_words.append(words[rand_id]["word"])
        count = count + 1
    print(ten_words)
    return ten_words


def reset_moonbeam(moonbeam_name=None):
    for moonbeam in moonbeams:
        if moonbeam_name == None or moonbeam[0] == moonbeam_name:
            print("Initializing %s" % moonbeam[0])
            moonbeam[3] = get_ten_new_words(moonbeam[2])


def get_moonbeam_words(moonbeam_name=None):
    message = ""
    for moonbeam in moonbeams:
        if moonbeam_name == None or moonbeam[0] == moonbeam_name:
            message="%s%s: %s\n" % (message, moonbeam[0], ", ".join(moonbeam[3]))
    return message


def get_quote():
    seed()
    quote = quotes[randint(0, 10000) % len(quotes)]
    split_quote = quote.split(" - ")
    split_attribution = split_quote[1].split(",")
    person = split_attribution[0]
    quote = split_quote[0]
    attribution = ", ".join(split_quote[1:])
    return "The Quotable %s\n&gt;%s\n - %s" % (person, quote, attribution)


def roll_dice(number, sides):
    results = []
    if number is None or number == "":
        number = 1
    else:
        number = int(number)
    for x in range(0, number):
        seed()
        results.append(randint(1, sides))
    return results

def check_for_match(word, dictionary):
    for entry in dictionary:
        pattern = re.compile(entry)
        if pattern.search(word):
            return True
    return False


if __name__ == "__main__":
    slack_client = SlackClient(BOT_TOKEN)
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
#    reset_moonbeam()
    while True:
        if slack_client.rtm_connect():
            print("moonbeam-bot connected and running!")
            try:
                while True:
                    output_list = slack_client.rtm_read()
                    if output_list and len(output_list) > 0:
                        for output in output_list:
                            if output and 'text' in output and ('bot_id' not in output or output['bot_id'] != BOT_ID) \
                                    and ('username' not in output or output['username'] != "slackbot") \
                                    and ('is_ephemeral' not in output or output['is_ephemeral'] != "true"):
                                print(json.dumps(output, indent=2))
                                # Control message from jheese
                                if 'channel' in output and output['channel'] == JHEESE_CHANNEL_ID and 'user' in output and output['user'] == JHEESE_ID:
                                    command = output['text']
                                    if command == "words":
                                        slack_client.api_call("chat.postMessage", channel=JHEESE_CHANNEL_ID, text=get_moonbeam_words(), as_user=False)
                                    elif command.startswith("reset"):
                                        if len(command.split(" ")) == 1:
                                            moonbeam_name = None
                                        else:
                                            moonbeam_name = " ".join(command.split(" ")[1:])
                                        reset_moonbeam(moonbeam_name)
                                        slack_client.api_call("chat.postMessage", channel=JHEESE_CHANNEL_ID, text=get_moonbeam_words(moonbeam_name), as_user=False)
                                # Quotable request
                                if "quotable" in output['text'].lower():
                                    slack_client.api_call("chat.postMessage", channel=output['channel'], text=get_quote())
                                # General command request
                                action = ""
                                if output['text'].lower().startswith("moonbeam"):
                                    words = output['text'].lower().split()[1:]
                                    rude = False
                                    pleased = False
                                    dice_pattern = re.compile("\d*d\d+(\+\d)*(-\d)*$")
                                    dices = []
                                    for word in words:
                                        if profanity.contains_profanity(word):
                                            rude = True
                                            break
                                        if word == "roll":
                                            action = word
                                            continue
                                        # Strip the word of punctuation so we can check if it's a dice roll
                                        for c in ".,?!":
                                            word = word.replace(c, "")
                                        if not dice_pattern.match(word):
                                            # if we haven't already been treated courteously, check for pleasantry
                                            if not pleased and check_for_match(word, pleasantries):
                                                pleased = True
                                            # If this word isn't a roll, then skip it
                                            continue
                                        # This word is a dice roll, add it to the dices
                                        dices.append(word)
                                    if rude:
                                        slack_client.api_call("chat.postMessage", channel=output['channel'], \
                                                text="There's no need to be rude, <@%s>! :face_with_raised_eyebrow:" % output['user'])
                                        break
                                    if not pleased:
                                        slack_client.api_call("chat.postMessage", channel=output['channel'], \
                                                text="Ah ah ah, <@%s>, you didn't say the magic word... :face_with_monocle:" % output['user'])
                                        break
                                    if action == "roll":
                                        summary = "*Dice*    \t\t\t\t*Rolls*"
                                        total = 0
                                        max_roll = 0
                                        total_string = ""
                                        for dice in dices:
                                            add = 0
                                            minus = 0
                                            if "+" in dice:
                                                add = int(dice.split("+")[1])
                                                max_roll = max_roll + 1
                                                dice = dice.split("+")[0]
                                            elif "-" in dice:
                                                minus = int(dice.split("-")[1])
                                                max_roll = max_roll - 1
                                                dice = dice.split("-")[0]
                                            split_dice = dice.split("d")
                                            results = roll_dice(split_dice[0], int(split_dice[1]))
                                            dice_results = ""
                                            for result in results:
                                                dice_results = "%s %s" % (dice_results, result)
                                                total_string = "%s + %s" % (total_string, result)
                                                total = total + int(result)
                                                max_roll = max_roll + int(split_dice[1])
                                            if add != 0:
                                                total = total + add
                                                total_string = "%s + %s" % (total_string, add)
                                            if minus != 0:
                                                total = total - minus
                                                total_string = "%s - %s" % (total_string, minus)
                                            if total_string.startswith(" ") or total_string.startswith("+") or total_string.startswith("-"):
                                                total_string = " ".join(total_string.split()[1:])
                                            padding = ""
                                            for x in range(0, (5-len(dice))*2):
                                                padding = padding + " "
                                            if add != 0: dice = "%s+%s" % (dice, add)
                                            if minus != 0: dice = "%s-%s" % (dice, minus)
                                            if dice.startswith("d"): dice = "1%s" % dice
                                            summary = "%s\n%s%s\t\t\t\t%s" % (summary, dice, padding, dice_results)
                                        if " " in total_string:
                                            total_string = "%s = %s" % (total_string, total)
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
                                        attachments = {"text":"<@%s> rolled a *%s*\n%s" % (output['user'], total_string, summary), "color":color}
                                        if image_url:
                                            attachments['image_url'] = "https://slack-files.com/T0TGU21T2-FMLC3CUFL-04242147ee"
                                        slack_client.api_call("chat.postMessage", channel=output['channel'], attachments=[attachments])
                                    else:
                                        print("action was %s" % action)
                                        slack_client.api_call("chat.postMessage", channel=output['channel'], \
                                                text="<@%s>, I'm not really sure what \"%s\" means..." % (output['user'], output['text']))
                                    break
                                # Check for moonbeam words
                                for moonbeam in moonbeams:
                                    message_words = output['text'].lower().split(" ")
                                    if moonbeam[3]:
                                        for word in moonbeam[3]:
                                            for message_word in message_words:
                                                message_word = "".join([i for i in str(message_word) if i.isalpha()])
                                                if word == message_word:
                                                    print(json.dumps(output, indent=2))
                                                    slack_client.api_call("chat.postMessage", channel=output['channel'], \
                                                            text="%s because: *%s*\n%s" % (moonbeam[0], word, moonbeam[1]))
                                                    reset_moonbeam(moonbeam[0])
                                                    break
                    sleep(READ_WEBSOCKET_DELAY)
            except Exception as e:
                traceback.print_exc()
        else:
            print("Connection failed. Invalid Slack token or bot ID?")
