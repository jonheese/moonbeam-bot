#!/bin/bash

# WARNING!
# This file is part of the legacy Moonbeam-bot launching mechanism
# It should not be used anymore, but is left here for posterity


#set -x
CONF_FILE="/etc/default/moonbeam-bot"
CONF_FILE_MISSING="Create file $CONF_FILE with (at least) the \$EXEC variable defined (eg. /usr/bin/python3 -u /usr/local/moonbeam-bot/moonbeam-bot.py)."
[ ! -f "$CONF_FILE" ] && echo "$CONF_FILE_MISSING" && exit 1
. $CONF_FILE
[ -z "$EXEC" ] && echo "$CONF_FILE_MISSING" && exit 1

LOG_FILE=${LOG_FILE:-/var/log/moonbeam-bot.log}
date >> $LOG_FILE
$EXEC >> $LOG_FILE 2>&1
