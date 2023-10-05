from . import plugin
from random import randint, seed
import json


class QuotablePlugin(plugin.NoBotPlugin):
    def __read_quotes(self):
        with open(self._config.get('QUOTES_FILE'), 'r') as f:
            return json.load(f)

    def __strip_quotes(self, snippet):
        quote_mark_sets = [
            ['"', '"'],
            ['\u201c', '\u201d'],
        ]
        for (open_quote, close_quote) in quote_mark_sets:
            if snippet.startswith(open_quote) and snippet.endswith(close_quote):
                snippet = snippet.lstrip(quote_mark_set[0]).rstrip(quote_mark_set[1])
        return snippet

    def __add_quote(self, quote):
        quotes = self.__read_quotes()
        dupe_quote = self.__check_for_dupe(quote, quotes)
        if dupe_quote:
            return dupe_quote
        else:
            [quote_text, attribution] = quote.split(' - ')
            quote_text = self.__strip_quotes(quote_text)
            attribution = self.__strip_quotes(attribution)
            quote = " - ".join([quote_text, attribution])
            quotes.append(quote)
            with open(self._config.get('QUOTES_FILE'), 'w') as f:
                json.dump(quotes, f, indent=2)
            return

    def __search_quotes(self, search_words, channel):
        quotes = self.__read_quotes()
        matches = {}
        # Search through each of the quotes
        for quote in quotes:
            # Search for each of the words in the search string
            for search_word in search_words:
                # If we find it, keep a score of how many matches are in each quote
                if search_word in quote.lower():
                    if quote in matches.keys():
                        matches[quote] += 1
                    else:
                        matches[quote] = 1
        self._log.info(f'Matches: {json.dumps(matches, indent=2)}')

        # Find the highest matching quote(s)
        high_score = 0
        num_winners = 0
        winners = []
        for quote in matches.keys():
            if matches[quote] > high_score:
                winners = [quote]
                num_winners = 1
                high_score = matches[quote]
            elif matches[quote] == high_score:
                winners.append(quote)
                num_winners += 1

        if winners:
            self._log.info(f'Found {len(winners)} quotes')
            seed()
            winning_winner = winners[randint(0, 1000) % len(winners)]
            return self.__get_quote_message(channel, winning_winner)
        else:
            return self.__build_message(f'Sorry, no results found for search string "{" ".join(search_words)}".', channel)

    def __get_quote(self, index=None):
        seed()
        quotes = self.__read_quotes()
        if index is not None:
            return quotes[index]
        return quotes[randint(0, 1000) % len(quotes)]

    def __build_message(self, text, channel):
        return {
            'channel': channel,
            'text': text,
        }

    def __get_quote_message(self, channel, quote=None, index=None):
        if not quote:
            quote = self.__get_quote(index)
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
        text = f"I'm sorry <@{request['user']}>, I wasn't able to complete your request.\n" + \
               "To add a quote to my database, your message must follow the format: `Moonbeam add-quote <quote> - <attribution>`\n" + \
               f"For example: `Moonbeam add-quote {random_quote}`\n\n" + \
               "To retrieve a quote from my database by index, your message must follow the format: `Moonbeam quotable post <quote_index>`\n" + \
               "For example: `Moonbeam quotable post 13`\n\n" + \
               "To search for a quote in my database, your message must follow the format: `Moonbeam quotable search <search_string>`\n" + \
               "For example: `Moonbeam quotable search weasel`"
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
        channel = request['channel']
        if "user" not in request.keys():
            return responses
        user = request.get('user')
        text = request.get('text')
        if text.lower().strip() == "quotable":
            quote = self.__get_quote_message(channel=channel)
            self._log.info("printing quotable:")
            self._log.info(quote['text'])
            responses.append(quote)
        elif "quotable" in text.lower() and "post" in text.lower():
            index_index = -1
            word_index = -1
            words = text.lower().split()
            for word in words:
                word_index += 1
                if word == 'post':
                    index_index = word_index+1
                    break
            if index_index >= 0:
                self._log.info(f'index_index is {index_index}')
                try:
                    quote_index = int(words[index_index])
                    self._log.info(f'quote_index is {quote_index}')
                    responses.append(self.__get_quote_message(channel=channel, index=quote_index))
                except Exception as e:
                    self._log.exception(e)
                    responses.append(self.__show_usage(request))
        elif "quotable" in text.lower() and "search" in text.lower():
            search_string_index = -1
            word_index = -1
            words = text.lower().split()
            for word in words:
                word_index += 1
                if word == 'search':
                    search_string_index = word_index+1
                    break
            if search_string_index >= 0:
                self._log.info(f'search_string_index is {search_string_index}')
                try:
                    search_words = words[search_string_index:]
                    self._log.info(f'search_words is {search_words}')
                    quotes = self.__search_quotes(search_words=search_words, channel=channel)
                    if isinstance(quotes, list):
                        responses.extend(quotes)
                    elif isinstance(quotes, dict):
                        responses.append(quotes)
                    else:
                        responses.append(self.__show_usage(request))
                except Exception as e:
                    self._log.exception(e)
                    responses.append(self.__show_usage(request))
        elif "quotable" in text.lower() and "stats" in text.lower():
            responses.append(self.__build_message(self.__get_stats(), channel))
        elif text.lower().startswith('moonbeam') and "add-quote" in text.lower():
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
                        responses = self.__add_success(request, self.__read_quotes()[-1:][0], responses)
                    else:
                        responses.append(self.__build_message(f"Sorry, <@{user}>, but that quote looks very similar to this quote, which is already in my database:", channel))
                        responses.append(self.__get_quote_message(channel, dupe_quote))
                        responses.append(self.__build_message(f"If you are sure you still want to add it, send me a DM saying \"add quote\" and I'll take care of it for you. :thumbsup:\n" + \
                                         "Otherwise, you can send me a DM saying \"cancel quote\" and we'll forget this ever happened. :wink:", channel))
                        if not hasattr(self, '__confirmations'):
                            self.__confirmations = {}
                        self.__confirmations[user] = quote
                except Exception as e:
                    self._log.exception(e)
                    responses.append(self.__show_usage(request))
            else:
                responses.append(self.__show_usage(request))
        elif text.lower() == "add quote" or text.lower() == "cancel quote":
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

    def get_trigger_words(self):
        return [ "add-quote", "quotable" ]
