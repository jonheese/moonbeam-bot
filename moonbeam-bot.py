#!/usr/local/bin/python3

from slack import RTMClient, WebClient
from slack.errors import SlackApiError
from time import time

import json
import logging
import moonbeam_utils
import os
import traceback
from importlib import import_module


class Moonbeam:
    def __init__(self):
        logging.basicConfig(
            level=os.environ.get("LOGLEVEL", "DEBUG"),
            format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
        )
        self.__log = logging.getLogger(type(self).__name__)
        self.__log.info("Starting Moonbeam")
        self.__config = self.__load_config(prefix="Moonbeam")
        if 'BOT_TOKEN' not in self.__config:
            raise RuntimeError("BOT_TOKEN not found in config")
        self.__web_client = WebClient(self.__config['BOT_TOKEN'])
        self.__rtm_client = RTMClient(
            token=self.__config.get("BOT_TOKEN"),
            ping_interval=30,
            auto_reconnect=True,
        )
        self.__trigger_words = []
        self.__plugins = []
        self.__load_plugins()
        self.__rtm_client.run_on(event='message')(self.__process_message)
        self.__rtm_client.run_on(event='user_typing')(self.__process_typing)
        self.__rtm_client.run_on(event='reaction_added')(self.__process_reaction_added)
        self.__rtm_client.run_on(event='reaction_removed')(self.__process_reaction_removed)
        self.__rtm_client.start()

    def __post_message(self, response, conditionals=None):
        channel = response.get('channel')
        as_user = response.get('as_user')
        self.__log.info(f"Posting message in channel {channel} (as_user={as_user}):")
        try:
            if 'text' in response.keys() or 'blocks' in response.keys():
                text = response.get('text')
                if response.get('emojify') or \
                        ('emojify' not in response.keys() and \
                        round(time()) % 50 == 0): # 1/50th of the time randomly
                    text = moonbeam_utils.emojify(text)
                mappings = response.get('mappings')
                if mappings:
                    if '@CHANNEL@' in text and '@CHANNEL@' in mappings.keys():
                        channel_name = mappings.get('@CHANNEL@')
                        channel_id = 'UNKNOWN'
                        channels = self.__web_client.conversations_list()
                        for ch in channels.get('channels'):
                            if ch.get('name') == channel_name:
                                channel_id = ch.get('id')
                                break
                        mappings['@CHANNEL@'] = channel_id
                    text = self.__replace_vars(response.get('text'), mappings)
                slack_response = self.__web_client.chat_postMessage(
                    channel=channel,
                    text=text,
                    attachments=response.get('attachments'),
                    blocks=response.get('blocks'),
                    as_user=as_user,
                )
                if conditionals and conditionals.get(True):
                    self.__post_message(conditionals.get(True))
            elif 'name' in response.keys():
                slack_response = self.__web_client.reactions_add(
                    channel=channel,
                    name=response.get('name'),
                    timestamp=response.get('timestamp'),
                )
            else:
                raise RuntimeError(f"Unable to process response: {json.dumps(response, indent=2)}")
        except SlackApiError as e:
            if conditionals and conditionals.get(False):
                if not mappings:
                    mappings = response.get('mappings', {})
                mappings['@ERROR@'] = traceback.format_exc()
                response = conditionals.get(False)
                response['text'] = self.__replace_vars(response.get('text'), mappings)
                self.__post_message(response)
            else:
                self.__log.exception(f"Encountered a Slack API Error posting message: {e.response['error']}")

    def __replace_vars(self, message, mappings):
        for key in mappings.keys():
            message = message.replace(key, mappings[key])
        return message

    def __process_message(self, **payload):
        message = payload['data']
        self.__web_client = payload['web_client']
        self.__log.info(json.dumps(message, indent=2))
        for plugin in self.__plugins:
            try:
                responses = plugin.receive(message)
                if responses and isinstance(responses, dict):
                    self.__post_message(responses)
                elif responses and isinstance(responses, list):
                    if len(responses) == 2 and isinstance(responses[1], dict) and isinstance(responses[1].get(True), dict):
                            [responses, conditionals] = responses
                            for response in responses:
                                self.__post_message(response, conditionals)
                    else:
                        for response in responses:
                            if isinstance(response, dict) and response:
                                self.__post_message(response)
                else:
                    self.__log.debug(f"{plugin.__class__.__name__} didn't need to do anything with that message")
            except Exception as e:
                self.__log.exception(f"Encountered an exception with {plugin.__class__.__name__} responding to message: {e}")

    def __process_typing(self, **payload):
        data = payload['data']
        self.__log.debug(json.dumps(data, indent=2))
        for plugin in self.__plugins:
            try:
                responses = plugin.typing(data)
                if responses:
                    for response in responses:
                        self.__post_message(response)
            except Exception as e:
                self.__log.exception(f"Encountered an exception with {plugin.__class__.__name__} responding to typing: {e}")

    def __process_reaction_added(self, **payload):
        data = payload['data']
        self.__log.debug(json.dumps(data, indent=2))
        for plugin in self.__plugins:
            try:
                responses = plugin.reaction(data, added=True)
                if responses:
                    for response in responses:
                        self.__post_message(response)
            except Exception as e:
                self.__log.exception(f"Encountered an exception with {plugin.__class__.__name__} responding to reaction added: {e}")

    def __process_reaction_removed(self, **payload):
        data = payload['data']
        self.__log.debug(json.dumps(data, indent=2))
        for plugin in self.__plugins:
            try:
                responses = plugin.reaction(data, added=False)
                if responses:
                    for response in responses:
                        self.__post_message(response)
            except Exception as e:
                self.__log.exception(f"Encountered an exception with {plugin.__class__.__name__} responding to reaction removed: {e}")

    def __load_config(self, prefix):
        config = {}
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        # Process config file first, if present
        if os.path.isfile(config_file):
            try:
                with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
                    config = json.load(f)
            except Exception as e:
                self.__log.warning(e)
        # Env vars override config file settings, if present
        for key, value in os.environ.items():
            if key.startswith(f"{prefix}_"):
                subkey = "_".join(key.split('_')[1:])
                try:
                    config[subkey] = json.loads(value)
                except json.decoder.JSONDecodeError:
                    config[subkey] = value
        return config

    def __load_plugins(self):
        active_plugins = self.__config.get('PLUGINS')
        if not active_plugins:
            self.__log.debug("No plugins specified in config file/environment variables")
            return
        elif not isinstance(active_plugins, list) and not isinstance(active_plugins, str):
            self.__log.debug("Plugins specified in config file/environment variables must be a (JSON) list or a comma-delimited string")
            return

        if isinstance(active_plugins, str):
            active_plugins = active_plugins.split(",")

        for plugin_path in active_plugins:
            try:
                module_path, class_name = plugin_path.rsplit('.', 1)
                module = import_module(module_path)
                cls = getattr(module, class_name)
            except AttributeError:
                raise ImportError(f"Module {module_path} does not define a \"{class_name}\" attribute/class")
            except ValueError:
                raise ImportError(f"{plugin_path} doesn't look like a module path")
            except ImportError as error:
                raise ImportError(f"Problem importing {plugin_path} - {error}")
            plugin_config = self.__config.get(cls.__name__, {})
            if not plugin_config:
                plugin_config = self.__load_config(prefix=cls.__name__)
            plugin_config['BOT_ID'] = self.__config['BOT_ID']
            self.__log.debug(f"Loading class {cls.__name__}")
            plugin = cls(web_client=self.__web_client, plugin_config=plugin_config)
            self.__trigger_words.extend(plugin.get_trigger_words())
            self.__plugins.append(plugin)
            self.__log.debug(f"Plugin registered: {plugin}")
        for plugin in self.__plugins:
            plugin.store_global_trigger_words(self.__trigger_words)


if __name__ == "__main__":
    moonbeam = Moonbeam()
