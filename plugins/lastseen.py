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

    def __get_last_seen_by_username(self, username):
        self._log.info(f"Looking for lastseen of user {username}")
        query = \
            "SELECT u.username, u.full_name, m.timestamp, c.slack_channel_id, t.team_name, " +\
            "m.archive_url, m.text " + \
            "FROM tbl_messages m JOIN tbl_users u ON u.id = m.user_id " + \
            "JOIN tbl_channels c ON c.id = m.channel_id " + \
            f"JOIN tbl_teams t ON t.id = m.team_id WHERE u.username LIKE '%{username}%' " + \
            "ORDER BY m.timestamp DESC LIMIT 1"
        return self.__select(query=query)

    def __get_last_seen_by_full_name(self, full_name):
        self._log.info(f"Looking for lastseen of user {full_name}")
        query = \
            "SELECT u.username, u.full_name, m.timestamp, c.slack_channel_id, t.team_name, " +\
            "m.archive_url, m.text " + \
            "FROM tbl_messages m JOIN tbl_users u ON u.id = m.user_id " + \
            "JOIN tbl_channels c ON c.id = m.channel_id " + \
            f"JOIN tbl_teams t ON t.id = m.team_id WHERE u.full_name LIKE '%{full_name}%' " + \
            "ORDER BY m.timestamp DESC LIMIT 1"
        return self.__select(query=query)

    def __get_last_seen(self, name):
        records = self.__get_last_seen_by_username(username=name)
        records.extend(self.__get_last_seen_by_full_name(full_name=name))
        last_sighting = None
        for record in records:
            if not record:
                continue
            self._log.info(json.dumps(record, indent=2))
            timestamp = int(record[2])
            if not last_sighting:
                last_sighting = record
            else:
                if timestamp > last_sighting[2]:
                    last_sighting = record

        if last_sighting:
            timestamp = str(
                datetime.fromtimestamp(
                    timestamp=last_sighting[2],
                    tz=pytz.timezone('America/New_York')
                )
            )
            message = f"The last time I saw {last_sighting[0]} ({last_sighting[1]}) was at {timestamp} in " + \
                f"<#{last_sighting[3]}> ({last_sighting[4]}) when they said: \n"
            if last_sighting[5]:
                message += f"{last_sighting[5]}\n"
            message += f">>>{last_sighting[6]}"
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
