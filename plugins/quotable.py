from . import plugin
from random import randint, seed
import json

class QuotablePlugin(plugin.NoBotPlugin):
    def __read_quotes(self):
        with open(self._config.get('QUOTES_FILE'), 'r') as f:
            return json.load(f)


    def __add_quote(self, quote):
        quotes = self.__read_quotes()
        dupe_quote = self.__check_for_dupe(quote, quotes)
        if dupe_quote:
            return dupe_quote
        else:
            quotes.append(quote)
            with open(self._config.get('QUOTES_FILE'), 'w') as f:
                json.dump(quotes, f, indent=2)
            return


    def __get_quote(self):
        seed()
        quotes = self.__read_quotes()
        quote = quotes[randint(0, 1000) % len(quotes)]
        return quote


    def __build_message(self, text, channel):
        return {
            'channel': channel,
            'text': text,
        }


    def __get_quote_message(self, channel, quote=None):
        if not quote:
            quote = self.__get_quote()
        split_quote = quote.split(" - ")
        split_attribution = split_quote[1].split(",")
        person = split_attribution[0]
        quote = split_quote[0]
        attribution = ", ".join(split_quote[1:])
        if '\n' in quote:
            output = ''
            for line in quote.split('\n'):
                output += f"&gt;{line}\n"
            quote = output
        else:
            quote = f"&gt;{quote}\n"
        return self.__build_message(f"The Quotable {person}\n{quote} - {attribution}", channel)


    def __check_for_dupe(self, requested_quote, quotes):
        word_count = len(requested_quote.split())
        for quote in quotes:
            hit_count = 0
            for word in quote.split():
                if word in requested_quote.split():
                    hit_count += 1
            if hit_count / word_count > 0.8:
                return quote
        return False


    def __show_usage(self, request):
        random_quote = self.__get_quote()
        text = f"<@{request['user']}>, to add a quote to my database, your message must follow the format: `Moonbeam add-quote <quote> - <attribution>`" + \
               f", eg. `Moonbeam add-quote {random_quote}`"
        return self.__build_message(text, request['channel'])


    def __add_success(self, request, quote, responses):
        responses.append(self.__build_message(f"Okay, <@{request['user']}>, I added the following Quotable to my database:", request['channel']))
        responses.append(self.__get_quote_message(request['channel'], quote))
        return responses


    def __get_stats(self):
        max_length = 0
        scores = {}
        quotes = self.__read_quotes()
        for quote in quotes:
            split_quote = quote.split(" - ")
            split_attribution = split_quote[1].split(",")
            person = split_attribution[0]
            quote = split_quote[0]
            attribution = ", ".join(split_quote[1:])
            split_person = person.split()
            person = split_person[0] + " " + split_person[len(split_person) - 1]
            if person in scores.keys():
                scores[person] = scores[person] + 1
            else:
                scores[person] = 1
            if len(person) > max_length:
                max_length = len(person)

        sorted_scores = sorted(scores.items(), key=lambda item: item[1])
        sorted_scores.reverse()
        scores = {k: v for k, v in sorted_scores}

        text = '```'
        for person, count in scores.items():
            percent = (count / len(quotes)) * 100
            spaces = max_length - len(person)
            count_percent = f'{count} ({percent:.2f}%)'
            count_spacing = 12 - len(count_percent)
            text += f"{person}: {spaces*' '} {count_percent}{' ' * count_spacing} {'#' * count}\n"
        spaces = max_length - 5
        count_percent = f"{len(quotes)} (100%)"
        count_spacing = 12 - len(count_percent)
        text += f"Total: {spaces*' '} {count_percent}{' ' * count_spacing} {'#' * len(quotes)}\n"
        text = text + '```'
        return text


    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        text = request['text']
        channel = request['channel']
        user = request['user']
        if "quotable" in request['text'].lower():
            if "stats" in request['text'].lower():
                responses.append(self.__build_message(self.__get_stats(), request['channel']))
            else:
                quote = self.__get_quote_message(channel=channel)
                self._log.info("printing quotable:")
                self._log.info(quote['text'])
                responses.append(quote)
        if text.lower().startswith('moonbeam') and "add-quote" in request['text'].lower():
            command_index = -1
            index = -1
            words = text.split()
            for word in words:
                index += 1
                if word == "add-quote":
                    command_index = index
                    break
            if command_index >= 0:
                try:
                    quote = " ".join(words[command_index+1:])
                    dupe_quote = self.__add_quote(quote)
                    if not dupe_quote:
                        responses = self.__add_success(request, quote, responses)
                    else:
                        responses.append(self.__build_message(f"Sorry, <@{user}>, but that quote looks very similar to this quote, which is already in my database:", channel))
                        responses.append(self.__get_quote_message(channel, dupe_quote))
                        responses.append(self.__build_message(f"If you are sure you still want to add it, send me a DM saying \"add quote\" and I'll take care of it for you. :thumbsup:\n" + \
                                         "Otherwise, you can send me a DM saying \"cancel quote\" and we'll forget this ever happened. :wink:", channel))
                        if not self.hasattr(self, '__confirmations'):
                            self.__confirmations = {}
                        self.__confirmations[user] = quote
                except Exception as e:
                    self._log.exception(e)
                    responses.append(self.__show_usage(request))
            else:
                responses.append(self.__show_usage(request))
        if text.lower() == "add quote" or text.lower() == "cancel quote":
            if not self.hasattr(self, '__confirmations'):
                self.__confirmations = {}
            if user in self.__confirmations.keys():
                if text.lower() == "add quote":
                    responses = self.__add_success(request, self.__confirmations[user], responses)
                    self._log.debug(f"Removing quote confirmation for user {user}: {self.__confirmations[user]}")
                    self.__confirmations.pop(user)
                else:
                    self.__confirmations.pop(user)
                    responses.append(self.__build_message("Okay, request cancelled. :speak_no_evil:", channel))
            else:
                responses.append(self.__build_message(f":thinking_face: Ummm... I don't think there's any quote to {text.lower().split()[0]}...", channel))
        return responses

