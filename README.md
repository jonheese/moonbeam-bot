# moonbeam-bot
Moonbeam is an extensible Slack chat bot.

# Running
## docker-compose
The simplest (and recommended) method to run the Moonbeam is via docker-compose.  You'll need to set a bunch of environment variables first, so using an `.env` file is recommended.  It should have the following format:

```
# List of plugin class specs to load.  The example is the full list at this time:
Moonbeam_PLUGINS=plugins.archive.ArchivePlugin,plugins.autoscoogle.AutoScooglePlugin,plugins.command.CommandPlugin,plugins.covid.COVIDPlugin,plugins.dbstore.DBStorePlugin,plugins.dice.DicePlugin,plugins.help.HelpPlugin,plugins.moonbeam.MoonbeamPlugin,plugins.quotable.QuotablePlugin,plugins.trigger.TriggerPlugin,plugins.weather.WeatherPlugin

# The Slack ID and token of your Moonbeam app (bot) account
Moonbeam_BOT_ID=MOONBEAM_ID
Moonbeam_BOT_TOKEN=xoxb-MOONBEAM_TOKEN

# The Slack user ID and DM channel ID for your "master" user, i.e. the user who can issue commands to your Moonbeam
CommandPlugin_MASTER_ID=UMASTERUSERID
CommandPlugin_MASTER_CHANNEL_ID=DMASTERCHANNELID

# The filename of your quotable JSON storage file, relative to the base Moonbeam dir, quotes.json should be fine
QuotablePlugin_QUOTES_FILE=quotes.json

# The filename of your trigger JSON storage file, relative to the base Moonbeam dir, triggers.json should be fine
TriggerPlugin_TRIGGERS_FILE=triggers.json

# The filename of your prefilled pleasantries JSON storage file, relative to the base Moonbeam dir, pleasantries.json should be fine
DicePlugin_PLEASANTRIES_FILE=pleasantries.json


# The Slack user ID and DM channel ID for your "master" user, i.e. the user who can issue commands to your Moonbeam
MoonbeamPlugin_MASTER_ID=UMASTERUSERID
MoonbeamPlugin_MASTER_CHANNEL_ID=MASTERCHANNELID
# The filename of your prefilled words JSON storage file, relative to the base Moonbeam dir, words.json should be fine
MoonbeamPlugin_WORDS_FILE=words.json
# JSON text var containing the URLs to the Moonbeam and Super-Moonbeam images, respectively
MoonbeamPlugin_MOONBEAM_IMAGE_URLS=[ "http://whatever.com/moonbeam.jpg", "http://whatever.com/supermoonbeam.jpg" ]

# The database connection info for storing chat logs
DBStorePlugin_DB_NAME=slack_archive
DBStorePlugin_DB_USER=slack_archive
DBStorePlugin_DB_PASSWORD=PASSWORD
DBStorePlugin_DB_HOST=172.17.0.1

# JSON text var containing the Slack user IDs for whom AutoScoogle should be enabled
AutoScooglePlugin_AUTOSCOOGLE_USERS=[ "USLACKUSER", "UANOTHERONE" ]
# JSON text var containing the triggers that preced an AutoScoogle query
AutoScooglePlugin_AUTOSCOOGLE_TRIGGERS=[ "what is ", "what are ", "wtf is ", "wtf are ", "what the fuck is ", "what the fuck are " ]

# Weatherbit API key
WeatherPlugin_WEATHERBIT_API_KEY=API_KEY
```

If you don't want to run any of the existing plugins, just exclude them from the `Moonbeam_PLUGINS` list.

Then run: `docker-compose up --build` to start it up.  Once it's working well, you can daemonize it by running `docker-compose up --build -d`.

## Manually running
If you don't want to run it via docker-compose, you can run it manually.  You'll need to either set the above env vars beforehand, or you can create `config.json` in the base directory, using `config-dist.json` (and the annotated block above) as a guide.

Then run `python3 -u moonbeam-bot.py`.  This can be run as an initscript using the sample scripts found in `initscripts`, but this is left as an exercise for the reader.

# Extending
To extend Moonbeam functionality, you can write your own plugin and PR it here for inclusion in the official Moonbeam bot.

Your plugin should extend the `Plugin` (or `NoBotsPlugin`) class, be stored in a new file in the `plugins` directory, implement the `receive()` method.  See `plugins/help_plugin.py` for an easy-to-consume example.

After you write your plugin, you'll need to add it to `Moonbeam_PLUGINS` in the config file/vars, along with any needed config directives.

# Feedback
If you're using Moonbeam somewhere, first of all, I'm very surprised.  Second, please let me know, especially if you have any feedback on it: github@jonheese.com.

Thank you.
