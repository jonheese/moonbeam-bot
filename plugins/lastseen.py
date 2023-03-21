from . import plugin
from datetime import datetime
import json
import mysql.connector
import pytz

class LastSeenPlugin(plugin.NoBotPlugin):
    def __init__(self, web_client, plugin_config):
        super().__init__(web_client=web_client, plugin_config=plugin_config)
        self.__init_db()

    def __init_db(self):
        try:
            self.__conn = mysql.connector.connect(
                host=self._config.get("DB_HOST"),
                database=self._config.get("DB_NAME"),
                user=self._config.get("DB_USER"),
                password=self._config.get("DB_PASSWORD")
            )
        except Error as e:
            self._log.exception(f"Failed to connect to db: {e}")
            self.__conn = None

    def __select(self, query):
        if not self.__conn or not self.__conn.is_connected():
            self.__init_db()
        cursor = self.__conn.cursor()
        self._log.info("Executing query:")
        self._log.info(query)
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        return records

    def __search_for_user(self, name):
        self._log.info(f"Searching for user named '{name}'")
        query = f"SELECT id FROM tbl_users WHERE username LIKE '%{name}%' OR full_name like '%{name}%'"
        results = self.__select(query=query)
        return [result[0] for result in results]

    def __get_last_seen_by_user_ids(self, user_ids):
        self._log.info(f"Getting last seen for user IDs: {user_ids}")
        if not user_ids:
            return []
        query = \
            "SELECT u.username, u.full_name, m.timestamp, c.slack_channel_id, t.team_name, " +\
            "m.archive_url, m.text " + \
            "FROM tbl_messages m JOIN tbl_users u ON u.id = m.user_id " + \
            "JOIN tbl_channels c ON c.id = m.channel_id " + \
            f"JOIN tbl_teams t ON t.id = m.team_id WHERE u.id in ({','.join(str(user_id) for user_id in user_ids)}) " + \
            "ORDER BY m.timestamp DESC LIMIT 1"
        return self.__select(query=query)

    def __get_last_seen(self, name):
        records = self.__get_last_seen_by_user_ids(user_ids=self.__search_for_user(name=name))
        if records:
            last_sighting = {
                'username': records[0][0],
                'full_name': records[0][1],
                'timestamp': records[0][2],
                'slack_channel_id': records[0][3],
                'team_name': records[0][4],
                'archive_url': records[0][5],
                'text': records[0][6],
            }

            timestamp = str(
                datetime.fromtimestamp(
                    timestamp=last_sighting['timestamp'],
                    tz=pytz.timezone('America/New_York')
                )
            )
            message = \
                f"The last time I saw {last_sighting['username']} ({last_sighting['full_name']}) " + \
                f"was at {timestamp} in <#{last_sighting['slack_channel_id']}> ({last_sighting['team_name']}) " + \
                f"when they said: \n"
            if last_sighting['archive_url']:
                message += f"{last_sighting['archive_url']}\n"
            message += f">>>{last_sighting['text']}"
            return message
        else:
            return "Sorry, I don't have any record of that user ever posting anything."

    def receive(self, request):
        if super().receive(request) is False:
            return False
        responses = []
        if request['text'].lower().startswith("moonbeam lastseen"):
            responses.append(
                {
                    'channel': request['channel'],
                    'text': self.__get_last_seen(name=request['text'].split()[2])
                }
            )
        return responses
