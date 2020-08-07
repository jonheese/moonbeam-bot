# moonbeam-bot
Moonbeam is an extensible Slack chat bot.

# Extending
To extend Moonbeam functionality, you can write your own plugin and PR it here for inclusion in the official Moonbeam bot.

Your plugin should extend the `Plugin` class, be stored in a new file in the `plugins` directory, implement the `receive()` method.  See `plugins/help_plugin.py` for an easy-to-consume example.

After you write your plugin, you'll need to import it in `moonbeam-bot.py` (follow the convention there) and load it into the `plugins` constructor argument in the startup routing there.

More to come (one day).
