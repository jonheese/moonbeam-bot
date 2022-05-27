#!/usr/bin/python3
import argparse
import json
import mysql.connector
from mysql.connector import Error
import sys


def init_db():
    conn = None
    try:
        conn = mysql.connector.connect(host=config['DB_HOST'],
                                       database=config['DB_NAME'],
                                       user=config['DB_USER'],
                                       password=config['DB_PASSWORD'])
    except Error as e:
        print(f"Failed to connect to db: {e}")
    return conn


def get_emoji_id(emoji_trigger, emoji_url, team_id, conn):
    cursor = conn.cursor()
    query = f"select id from tbl_emojis where emoji_trigger = '{emoji_trigger}' and url = '{emoji_url}' and team_id = '{team_id}'"
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    if records:
        return records
    return False


def insert_emoji(emoji_trigger, emoji_url, conn, team_id=1):
    emoji_id = get_emoji_id(emoji_trigger, emoji_url, team_id, conn)
    if emoji_id:
        return emoji_id
    cursor = conn.cursor()
    query = "insert into tbl_emojis (team_id, emoji_trigger, url) values (%s, %s, %s)"
    cursor.execute(query, (team_id, emoji_trigger, emoji_url))
    conn.commit()
    cursor.close()
    return get_emoji_id(emoji_trigger, emoji_url, team_id, conn)


def main(json_file=None):
    global config
    with open('/usr/local/moonbeam-bot/config.json', 'r') as f:
        config = json.load(f).get('DBStorePlugin')
    conn = init_db()
    if not json_file:
        raise RuntimeError("json_file must be provided")
    emoji_mappings = {}
    with open(json_file, 'r') as fp:
        emoji_mappings = json.load(fp)
    # print(json.dumps(emoji_mappings, indent=2))
    for emoji_trigger, emoji_url in emoji_mappings.items():
        emoji_id = insert_emoji(emoji_trigger, emoji_url, conn)
        if emoji_id:
            print(f"Inserted emoji {emoji_trigger} and got id {emoji_id[0][0]}")
        else:
            print(f"Tried to insert emoji {emoji_trigger} and got id {emoji_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Harvest emojis into database')
    parser.add_argument('json_file')
    args = parser.parse_args()
    main(args.json_file)
sys.exit()
