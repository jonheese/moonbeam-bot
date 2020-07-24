import json
import logging
import mysql.connector
import os
import re
import requests
import traceback
from mysql.connector import Error
from time import sleep, time
from slackclient import SlackClient
from random import randint, seed
from profanity import profanity
import urllib

#             Name              Image URL                                                   Frequency score     Words
moonbeams = [["Moonbeam",       "https://slack-files.com/T0TGU21T2-FFYTWBGA2-4e153c7af7",   3,                  None],
             ["Super Moonbeam", "https://slack-files.com/T0TGU21T2-FFWT7PSF3-b6f941711f",   2,                  None]]
covid_stats = {
                'world': {
                            'deaths': -1,
                            'cases': -1,
                            'recovered': -1,
                         },
                'us': {
                            'deaths': -1,
                            'cases': -1,
                            'recovered': -1,
                      },
                'timestamp': 0,
              }

autoscoogle_triggers = [
                        "what is ",
                        "what are ",
                        "wtf is ",
                        "wtf are ",
                       ]

with open('/usr/local/moonbeam-bot/words.json', 'r') as f:
    words = json.load(f)

with open('/usr/local/moonbeam-bot/config.json', 'r') as f:
    config = json.load(f)

with open('/usr/local/moonbeam-bot/pleasantries.json', 'r') as f:
    pleasantries = json.load(f)

with open('/usr/local/moonbeam-bot/quotes.json', 'r') as f:
    quotes = json.load(f)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
log = logging.getLogger("moonbeam-bot")


def get_ten_new_words():
    ten_words = []
    count = 0
    while count < 10:
        seed()
        rand_id = randint(0, len(words)-1)
        ten_words.append(words[rand_id]["word"])
        count = count + 1
    log.debug(ten_words)
    return ten_words


def reset_moonbeam(moonbeam_name=None):
    for moonbeam in moonbeams:
        if moonbeam_name == None or moonbeam[0] == moonbeam_name:
            log.info("Initializing %s" % moonbeam[0])
            moonbeam[3] = get_ten_new_words()


def get_moonbeam_words(moonbeam_name=None):
    message = ""
    for moonbeam in moonbeams:
        if moonbeam_name == None or moonbeam[0] == moonbeam_name:
            message = "%s%s: %s\n" % (message, moonbeam[0], ", ".join(moonbeam[3]))
    return message


def add_quote(quote):
    quotes.append(quote)
    with open('/usr/local/moonbeam-bot/quotes.json', 'w') as f:
        json.dump(quotes, f, indent=2)


def get_quote():
    seed()
    quote = quotes[randint(0, 1000) % len(quotes)]
    return quote


def get_quote_message(quote=None):
    if not quote:
        quote = get_quote()
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


def get_covid_stats():
    global covid_stats
    if covid_stats['timestamp'] + 60 >= time():
        return
    tmpfile = '/tmp/states.csv'
    urls = {
                'world': 'https://www.worldometers.info/coronavirus/',
                'us': 'https://www.worldometers.info/coronavirus/country/us/',
           }
    for scope in urls.keys():
        r = requests.get(urls[scope])
        covid_stats['timestamp'] = time()
        with open(tmpfile, 'wb') as f:
            f.write(r.content)
        with open(tmpfile, 'r') as f:
            lines = f.readlines()
        deaths_found = False
        cases_found = False
        recovered_found = False
        line_count = 0
        for line in lines:
            if not deaths_found and 'Deaths' in line:
                covid_stats[scope]['deaths'] = line.split()[line.split().index('Deaths') - 1]
                deaths_found = True
            if not cases_found and 'Cases' in line:
                covid_stats[scope]['cases'] = line.split()[line.split().index('Cases') - 1]
                cases_found = True
            if not recovered_found and 'Recovered' in line:
                covid_stats[scope]['recovered'] = lines[line_count + 2].split('>')[1].split('<')[0]
                recovered_found = True
            if cases_found and deaths_found and recovered_found:
                break
            line_count += 1


def post_covid(channel, stat, slack_client):
    get_covid_stats()
    global covid_stats
    if stat == 'rates':
        world_pop = 7800000000
        us_pop = 327200000
        world_death_rate = round(float(covid_stats['world']['deaths'].replace(',','')) * 100 / float(covid_stats['world']['cases'].replace(',','')), 2)
        world_recovery_rate = round(float(covid_stats['world']['recovered'].replace(',','')) * 100 / float(covid_stats['world']['cases'].replace(',','')), 2)
        world_case_rate = round(float(covid_stats['world']['cases'].replace(',','')) * 100 / float(world_pop), 4)
        world_death_chance = round(world_death_rate * world_case_rate / 100, 4)
        us_death_rate = round(float(covid_stats['us']['deaths'].replace(',','')) * 100 / float(covid_stats['us']['cases'].replace(',','')), 2)
        us_recovery_rate = round(float(covid_stats['us']['recovered'].replace(',','')) * 100 / float(covid_stats['us']['cases'].replace(',','')), 2)
        us_case_rate = round(float(covid_stats['us']['cases'].replace(',','')) * 100 / float(us_pop), 4)
        us_death_chance = round(us_death_rate * us_case_rate / 100, 4)
        post_message(channel, ("The COVID-19 death rate is *%s%%* worldwide, and *%s%%* in the US.\n" + \
            "The COVID-19 recovery rate is *%s%%* worldwide, and *%s%%* in the US.\n" + \
            "The COVID-19 case rate is *%s%%* worldwide, and *%s%%* in the US.\n" + \
            "The COVID-19 chance of death is *%s%%* worldwide, and *%s%%* in the US.") % \
            (world_death_rate, us_death_rate, world_recovery_rate, us_recovery_rate, world_case_rate, us_case_rate, world_death_chance, us_death_chance),
            slack_client=slack_client)
    else:
        percentage = round(float(covid_stats['us'][stat].replace(',','')) * 100 / float(covid_stats['world'][stat].replace(',','')), 2)
        post_message(channel, "There are currently *%s* COVID-19 %s worldwide, with *%s (%s%%)* of those %s in the US" % \
            (covid_stats['world'][stat], stat, covid_stats['us'][stat], percentage, stat), slack_client=slack_client)


def check_for_match(word, dictionary):
    for entry in dictionary:
        pattern = re.compile(entry)
        if pattern.search(word):
            return True
    return False


def post_message(channel, text=None, attachments=None, as_user=True, slack_client=None):
    log.info("posting message in channel %s (as_user=%s):" % (channel, as_user))
    log.info(text.encode('utf-8').strip())
    slack_client.api_call("chat.postMessage", channel=channel, text=text, attachments=attachments, as_user=as_user)


def store_message(data, conn, cache=None):
    if not cache:
        cache = {
            "users": {},
            "channels": {},
            "teams": {},
        }
    timestamp = data["ts"].split(".")[0]
    if "bot_id" in data.keys():
        return cache
    try:
        slack_user_id = data["user"]
    except KeyError as ke:
        log.exception(json.dumps(data, indent=2))
        return cache
    try:
        slack_team_id = data["team"]
    except KeyError as e:
        return cache
    slack_channel_id = data["channel"]
    text = data["text"]
    files = []
    if "files" in data.keys():
        files = data['files']
    if "file" in data.keys():
        files.append(data['file'])

    if not slack_team_id in cache["teams"].keys():
        team_id = insert("tbl_teams", "slack_team_id", slack_team_id, "slack_team_id", slack_team_id, conn)
        cache["teams"][slack_team_id] = team_id
    else:
        team_id = cache["teams"][slack_team_id]
    if not slack_user_id in cache["users"].keys():
        user_id = insert("tbl_users", ["slack_user_id", "team_id"], [slack_user_id, team_id], "slack_user_id", slack_user_id, conn)
        cache["users"][slack_user_id] = user_id
    else:
        user_id = cache["users"][slack_user_id]
    if not slack_channel_id in cache["channels"].keys():
        channel_id = insert("tbl_channels", ["slack_channel_id", "team_id"], [slack_channel_id, team_id], "slack_channel_id", slack_channel_id, conn)
        cache["channels"][slack_channel_id] = channel_id
    else:
        channel_id = cache["channels"][slack_channel_id]
    message_id = insert_message(team_id, channel_id, user_id, timestamp, text, conn)
    handle_files(files, message_id, conn)
    if "user_profile" in data.keys():
        handle_user_profile(data['user_profile'], user_id, conn)
    return cache


def main():
    conn = init_db()
    cache = None
    slack_client = SlackClient(config.get("BOT_TOKEN"))
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    reset_moonbeam()
    while True:
        if slack_client.rtm_connect():
            log.info("moonbeam-bot connected and running!")
            try:
                while True:
                    output_list = slack_client.rtm_read()
                    if output_list and len(output_list) > 0:
                        for output in output_list:
                            if output and 'text' in output and ('is_ephemeral' not in output or output['is_ephemeral'] != "true"):
                                try:
                                    cache = store_message(output, conn, cache)
                                except Exception as e:
                                    log.exception(e)
                                if ('bot_id' in output and output['bot_id'] == config.get("BOT_ID")) or ('username' in output and output['username'] == "slackbot"):
                                    continue
                                log.info(json.dumps(output, indent=2))
                                # Control message from jheese
                                if 'channel' in output and output['channel'] == config.get("MASTER_CHANNEL_ID") and 'user' in output and output['user'] == config.get("MASTER_ID"):
                                    command = output['text']
                                    if command == "words":
                                        post_message(channel=config.get("MASTER_CHANNEL_ID"), text=get_moonbeam_words(), as_user=False, slack_client=slack_client)
                                    elif command.startswith("reset"):
                                        if len(command.split(" ")) == 1:
                                            moonbeam_name = None
                                        else:
                                            moonbeam_name = " ".join(command.split(" ")[1:])
                                        reset_moonbeam(moonbeam_name)
                                        post_message(channel=config.get("MASTER_CHANNEL_ID"), text=get_moonbeam_words(moonbeam_name), as_user=False, slack_client=slack_client)
                                    if command.split()[0] == "post":
                                        room_name = command.split()[1]
                                        message = " ".join(command.split()[2:])
                                        post_message(channel=room_name, text=message, slack_client=slack_client)
                                if "user" in output and output["user"] in config.get("AUTOSCOOGLE_USERS") and "text" in output:
                                    # Potential auto-scoogle request
                                    subject = None
                                    for trigger in autoscoogle_triggers:
                                        if trigger in output["text"].lower():
                                            subject = output["text"].split(trigger)[1]
                                            break
                                    if subject:
                                        scoogle = "I Auto-Scoogled that for you:\nhttp://www.google.com/search?q=%s" % urllib.quote(subject)
                                        post_message(channel=output['channel'], text=scoogle, slack_client=slack_client)
                                # Quotable request
                                if "quotable" in output['text'].lower():
                                    quote = get_quote_message()
                                    log.info("printing quotable:")
                                    log.info(quote)
                                    post_message(channel=output['channel'], text=quote, slack_client=slack_client)
                                # General command request
                                action = ""
                                if output['text'].lower() == "yes, have some":
                                    post_message(channel=output['channel'], \
                                        text="http://yeshavesome.tv.inetu.org",
                                        slack_client=slack_client)
                                if "covid-stats" in output['text'].lower():
                                    post_covid(channel=output['channel'], stat='deaths', slack_client=slack_client)
                                    post_covid(channel=output['channel'], stat='recovered', slack_client=slack_client)
                                    post_covid(channel=output['channel'], stat='cases', slack_client=slack_client)
                                    post_covid(channel=output['channel'], stat='rates', slack_client=slack_client)
                                elif output['text'].lower().startswith("moonbeam"):
                                    orig_words = output['text'].split()[1:]
                                    words = output['text'].lower().split()[1:]
                                    rude = False
                                    pleased = False
                                    dice_pattern = re.compile("\d*d\d+(\+\d)*(-\d)*$")
                                    dices = []
                                    command_index = -1
                                    index = -1
                                    for word in words:
                                        index += 1
                                        if profanity.contains_profanity(word):
                                            rude = True
                                            continue
                                        if word == "roll":
                                            action = word
                                            continue
                                        if word == "add-quote":
                                            action = "add-quote"
                                            command_index = index
                                            continue
                                        if word == "help":
                                            action = "help"
                                            continue
                                        # Strip all punctuation from the word so we can check if it's a dice roll
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
                                    if not action:
                                        break
                                    if action == "add-quote":
                                        try:
                                            quote = " ".join(orig_words[command_index+1:])
                                            if len(quote.split(" - ")) != 2:
                                                raise Exception("No dash in quote")
                                            add_quote(quote)
                                            post_message(channel=output['channel'], text="Okay <@%s>, I added the following Quotable to my database:" % output['user'], slack_client=slack_client)
                                            post_message(channel=output['channel'], text=get_quote_message(quote), slack_client=slack_client)
                                        except Exception as e:
                                            random_quote = get_quote()
                                            post_message(channel=output['channel'], \
                                                text="<@%s>, to add a quote to my database, your message must follow the format: `Moonbeam add-quote <quote> - <attribution>`, " % \
                                                output['user'] + ", eg. `Moonbeam add-quote %s`" % random_quote, slack_client=slack_client)
                                            raise e
                                        continue
                                    if action == "help":
                                        post_message(channel=output['channel'], \
                                            text="I understand the following commands: `Moonbeam roll <dice>`, `Moonbeam add-quote <quote> - <attribution>`, " + \
                                            "`covid-stats`, `covid-deaths`, `covid-cases`, `covid-recovery`, `covid-rates`, `quotable`", slack_client=slack_client)
                                        continue
                                    if rude:
                                        post_message(channel=output['channel'], \
                                                text="There's no need to be rude, <@%s>! :face_with_raised_eyebrow:" % output['user'], slack_client=slack_client)
                                        break
                                    if not pleased:
                                        post_message(channel=output['channel'], \
                                                text="Ah ah ah, <@%s>, you didn't say the magic word... :face_with_monocle:" % output['user'], slack_client=slack_client)
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
                                        post_message(channel=output['channel'], text='', attachments=[attachments], slack_client=slack_client)
                                    else:
                                        log.info("action was %s" % action)
                                        post_message(channel=output['channel'], \
                                                text="<@%s>, I'm not really sure what \"%s\" means..." % (output['user'], output['text']) ,slack_client=slack_client)
                                    break
                                else:
                                    if "covid-deaths" in output['text'].lower():
                                        post_covid(channel=output['channel'], stat='deaths')
                                    if "covid-cases" in output['text'].lower():
                                        post_covid(channel=output['channel'], stat='cases')
                                    if "covid-recovery" in output['text'].lower():
                                        post_covid(channel=output['channel'], stat='recovered')
                                    if "covid-rates" in output['text'].lower():
                                        post_covid(channel=output['channel'], stat='rates')
                                # Check for moonbeam words
                                for moonbeam in moonbeams:
                                    message_words = output['text'].lower().split(" ")
                                    if moonbeam[3]:
                                        for word in moonbeam[3]:
                                            for message_word in message_words:
                                                message_word = "".join([i for i in str(message_word) if i.isalpha()])
                                                if word == message_word:
                                                    log.debug(json.dumps(output, indent=2))
                                                    post_message(channel=output['channel'], \
                                                            text="%s because: *%s*\n%s" % (moonbeam[0], word, moonbeam[1]), slack_client=slack_client)
                                                    reset_moonbeam(moonbeam[0])
                                                    break
                    sleep(READ_WEBSOCKET_DELAY)
            except Exception as e:
                traceback.print_exc()
        else:
            log.error("Connection failed. Invalid Slack token or bot ID?")


def init_db():
    conn = None
    try:
        conn = mysql.connector.connect(host=config.get("DB_HOST"),
                                       database=config.get("DB_NAME"),
                                       user=config.get("DB_USER"),
                                       password=config.get("DB_PASSWORD"))
    except Error as e:
        log.exception("Failed to connect to db: %s" % e)
    return conn


def select(query, conn):
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    return records


def get_id(table, slack_id_column, slack_id, conn):
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    query = "select id from %s where %s = '%s'" % (table, slack_id_column, slack_id)
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    if records:
        return records
    return False


def insert(table, columns, values, slack_id_column, slack_id, conn):
    item_id = get_id(table, slack_id_column, slack_id, conn)
    if item_id:
        return item_id[0][0]
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    if isinstance(columns, list):
        columns = ", ".join(columns)
    if isinstance(values, list):
        for index, value in enumerate(values):
            if isinstance(value, int):
                log.debug("inserting %s at index %s" % (unicode(value), index))
                values[index] = unicode(value)
            else:
                values[index] = value.replace(u"'", u"\'")
        log.debug(values)
        values = u", ".join("'" + value + "'" for value in values)
    query = "insert into %s(%s) values (%s)" % (table, columns, values)
    log.debug(query)
    cursor.execute(query)
    conn.commit()
    item_id = get_id(table, slack_id_column, slack_id, conn)
    cursor.close()
    return item_id[0][0]


def get_message_id(timestamp, user_id, conn):
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    query = "select id from tbl_messages where timestamp = %s and user_id = %s"
    cursor.execute(query, (timestamp, user_id))
    records = cursor.fetchall()
    cursor.close()
    if records:
        return records[0][0]
    return False


def insert_message(team_id, channel_id, user_id, timestamp, text, conn):
    message_id = get_message_id(timestamp, user_id, conn)
    if message_id:
        return message_id
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    query = "insert into tbl_messages (team_id, channel_id, user_id, timestamp, text) values (%s, %s, %s, %s, %s)"
    log.info("Inserting message:")
    log.info(query % (team_id, channel_id, user_id, timestamp, text))
    cursor.execute(query, (team_id, channel_id, user_id, timestamp, text))
    conn.commit()
    cursor.close()
    message_id = get_message_id(timestamp, user_id, conn)
    log.info("Got message ID : (%s)" % message_id)
    return message_id


def insert_file(file, conn):
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    query = "insert into tbl_files (message_id, mimetype, thumb_800, thumb_80, permalink, permalink_public, name) values (%s, %s, %s, %s, %s, %s, %s)"
    values = (
        file['message_id'],
        file['mimetype'],
        file.get('thumb_800'),
        file.get('thumb_80'),
        file.get('permalink'),
        file.get('permalink_public'),
        file.get('name'),
    )
    log.debug(query % values)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()


def handle_files(files, message_id, conn):
    for file_data in files:
        file = {
            'message_id': message_id,
            'mimetype': file_data['mimetype'],
        }
        if 'thumb_800' in file_data.keys():
            file['thumb_800'] = file_data['thumb_800']
        if 'thumb_80' in file_data.keys():
            file['thumb_80'] = file_data['thumb_80']
        if 'permalink' in file_data.keys():
            file['permalink'] = file_data['permalink']
        if 'permalink_public' in file_data.keys() and 'is_public' in file_data.keys() and file_data['is_public'] == True:
            file['permalink_public'] = file_data['permalink_public']
        if 'name' in file_data.keys():
            file['name'] = file_data['name']
        elif 'title' in file_data.keys():
            file['name'] = file_data['title']
        insert_file(file, conn)


def handle_user_profile(user_profile, user_id, conn):
    subs = []
    query = "update tbl_users set"
    if "name" in user_profile.keys():
        query += " username = %s,"
        subs.append(user_profile['name'])
    if "real_name" in user_profile.keys():
        query += " full_name = %s,"
        subs.append(user_profile['real_name'])
    if "image_72" in user_profile.keys():
        query += " avatar_url = %s,"
        subs.append(user_profile['image_72'])
    if not subs:
        return
    if not conn:
        conn = init_db()
    cursor = conn.cursor()
    query = query[:-1]
    query += " where id = %s"
    subs.append(user_id)
    log.debug(query % tuple(subs))
    cursor.execute(query, tuple(subs))
    conn.commit()
    cursor.close()


if __name__ == "__main__":
    main()
