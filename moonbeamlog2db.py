import json
import sys
import mysql.connector
from mysql.connector import Error
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD


def init_db():
    conn = None
    try:
        conn = mysql.connector.connect(host=DB_HOST,
                                       database=DB_NAME,
                                       user=DB_USER,
                                       password=DB_PASSWORD)
    except Error as e:
        print("Failed to connect to db: %s" % e)
    return conn


def select(query, conn):
    cursor = conn.cursor()
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    return records


def get_id(table, slack_id_column, slack_id, conn):
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
    cursor = conn.cursor()
    if isinstance(columns, list):
        columns = ", ".join(columns)
    if isinstance(values, list):
        for index, value in enumerate(values):
            if isinstance(value, int):
                print("inserting %s at index %s" % (unicode(value), index))
                values[index] = unicode(value)
            else:
                values[index] = value.replace(u"'", u"\'")
        print(values)
        values = u", ".join("'" + value + "'" for value in values)
    query = "insert into %s(%s) values (%s)" % (table, columns, values)
    print(query)
    cursor.execute(query)
    conn.commit()
    item_id = get_id(table, slack_id_column, slack_id, conn)
    cursor.close()
    return item_id[0][0]


def get_message_id(timestamp, user_id, conn):
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
    cursor = conn.cursor()
    query = "insert into tbl_messages (team_id, channel_id, user_id, timestamp, text) values (%s, %s, %s, %s, %s)"
    cursor.execute(query, (team_id, channel_id, user_id, timestamp, text))
    conn.commit()
    cursor.close()
    message_id = get_message_id(timestamp, user_id, conn)
    return message_id


def insert_file(file, conn):
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
    print(query % values)
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
    cursor = conn.cursor()
    query = query[:-1]
    query += " where id = %s"
    subs.append(user_id)
    print(query % tuple(subs))
    cursor.execute(query, tuple(subs))
    conn.commit()
    cursor.close()


def handle_json(json_buffer, conn, cache=None):
    if not cache:
        cache = {
            "users": {},
            "channels": {},
            "teams": {},
        }
    try:
        data = json.loads(json_buffer)
    except Exception as e:
        print("Exception (%s) parsing JSON: (%s)" % (e, json_buffer))
        with open('/tmp/failed_imports', 'a+') as f:
            f.write(json_buffer)
        return
    timestamp = data["ts"].split(".")[0]
    if "bot_id" in data.keys():
        return cache
    try:
        slack_user_id = data["user"]
    except KeyError:
        print(json_buffer)
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
    if files:
        print("Found file(s): %s" % files)

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
    #print("channel: %s, user: %s, team: %s, message: %s" % (channel_id, user_id, team_id, message_id))
    if message_id % 100 == 0:
        print("channel: %s, user: %s, team: %s, message: %s" % (channel_id, user_id, team_id, message_id))
    return cache


def main():
    conn = init_db()
    cache = None
    with open('/var/log/moonbeam-bot.log', 'r') as f:
        message_depth = 0
        json_buffer = ""
        while True:
            line = f.readline()
            if message_depth == 0:
                if line.startswith("{"):
                    message_depth += 1
                    json_buffer += line
                elif line.startswith("INFO:moonbeam-bot:{"):
                    message_depth += 1
                    json_buffer += line[18:]
                else:
                    continue
            else:
                if line.startswith("}"):
                    json_buffer += line
                    message_depth -= 1
                    if message_depth == 0:
                        cache = handle_json(json_buffer, conn, cache)
                        json_buffer = ""
                else:
                    json_buffer += line

if __name__ == "__main__":
    main()
sys.exit()

