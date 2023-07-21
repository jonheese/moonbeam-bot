from . import plugin

class HelpPlugin(plugin.NoBotPlugin):
    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if request['text'].lower().startswith("moonbeam help"):
            self._log.debug(f"Got help request: {request['text']}")
            responses.append(
                {
                    'channel': request['channel'],
                    'text': "I understand the following commands:\n" + \
                            "`Moonbeam add-quote <quote> - <attribution>` - Add a quote to the Quotable database (there is no need to use double-quotes in your message)\n" + \
                            "`Moonbeam add-trigger <trigger> - <reply>` - Add a trigger/reply to my trigger database (NOTE: Multiple replies can be given for a single trigger with subsequent requests and replies will be chosen at random when triggered)\n" + \
                            "`Moonbeam archive <search-string>` - Return a link to search the Slack archive for the given search string\n" + \
                            "`Moonbeam lastseen <search-string>` - Search for a Slack user by the given search string (either username or full name) and return the last time they posted to the team\n" + \
                            "`Moonbeam movie(s) <search-string>` - Return The Movie Database (TMDB) results for the given search string\n" + \
                            "`Moonbeam post <channel-name> <message>` - Command Moonbeam to post `<message>` in channel `<channel-name>`\n" + \
                            "`Moonbeam quotable post <n>` - Post the _nth_ entry in the quotable database\n" + \
                            "`Moonbeam quotable search <search_string>` - Search the quotable database and return the most relevant quote (will choose randomly to break a tie)\n" + \
                            "`Moonbeam roll <dice>` - Roll dice, `<dice>` format is _MdN_ where _M_ is the number of dice and _N_ is how many sides are on each die, also accepts modifiers like `+` and `-` (eg. 3d8+2)\n" + \
                            "`Moonbeam weather [[N] <period-type>] [zipcode]` - Return Weatherbit weather forecast for the optional _N_ time periods of _period-type_ (default 5 days) and optional _zipcode_ (default 18104)\n" + \
                            "`covid-deaths` - Return the current COVID-19 death rates for the world and the US\n" + \
                            "`covid-cases` - Return the current COVID-19 case rates for the world and the US\n" + \
                            "`covid-recovery` - Return the current COVID-19 recovery rates for the world and the US\n" + \
                            "`covid-rates` - Return all of the above COVID-19 rates, along with overall chances of death by COVID-19 (calculated by multiplying the case rate by the death rate)\n" + \
                            "`covid-stats` - Return all of the above COVID-19 stats, along with the world and US counts\n" + \
                            "`quotable` - Return a quote from the Quotable database",
                }
            )
        return responses
