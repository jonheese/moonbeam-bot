#!/bin/bash

MOONBEAM_DIR="/usr/local/moonbeam-bot"

cd $MOONBEAM_DIR
git remote update 2>&1 >/dev/null
needs_deploy=$(git status -uno 2>&1 | grep "can be fast-forwarded")
if [ -n "$needs_deploy" ] ; then
    git pull
    /etc/init.d/moonbeam-bot restart
fi
