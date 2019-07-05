#!/bin/sh

SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"

PLAYLIST_PATH="$(PROXY_TYPE=TV_GRAB $SCRIPT_PATH/.env/bin/python $SCRIPT_PATH/proxy.py 'plugin://plugin.program.iptv.merge/?_=proxy_merge&type=playlist')"

cat "$PLAYLIST_PATH" | sed -E "s|(^plugin://.*?$)|pipe://$SCRIPT_PATH/tvh.sh \"\1\"|g"