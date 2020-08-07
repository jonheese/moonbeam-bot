from . import plugin
from random import randint, seed
import json

class QuotablePlugin(plugin.Plugin):
    def __init__(self):
        super().__init__()


    def __read_quotes(self):
        with open(self._config.get('QUOTES_FILE'), 'r') as f:
            return json.load(f)


    def __add_quote(self, quote):
        quotes = read_quotes()
        quotes.append(quote)
        with open(self._config.get('QUOTES_FILE'), 'w') as f:
            json.dump(quotes, f, indent=2)


    def __get_quote(self):
        seed()
        quotes = self.__read_quotes()
        quote = quotes[randint(0, 1000) % len(quotes)]
        return quote


    def __get_quote_message(self, quote=None):
        if not quote:
            quote = self.__get_quote()
        split_quote = quote.split(" - ")
        split_attribution = split_quote[1].split(",")
        person = split_attribution[0]
        quote = split_quote[0]
        attribution = ", ".join(split_quote[1:])
        return f"The Quotable {person}\n&gt;{quote}\n - {attribution}"


    def receive(self, request):
        responses = []
        if "quotable" in request['text'].lower():
            quote = self.__get_quote_message()
            self._log.info("printing quotable:")
            self._log.info(quote)
            responses.append(
                {
                    'channel': request['channel'],
                    'text': quote,
                }
            )
        return responses
