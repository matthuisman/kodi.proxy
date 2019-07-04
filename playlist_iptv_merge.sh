#!/bin/sh

SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"

OUTPUT="$(PROXY_TYPE=TV_GRAB DEBUG=0 $SCRIPT_PATH/.env/bin/python $SCRIPT_PATH/proxy.py 'plugin://program.iptv.merge/?_=tv_grab')"
PLAYLIST_PATH="$($SCRIPT_PATH/.env/bin/python $SCRIPT_PATH/proxy.py 'settings://pvr.iptvsimple/m3uPath')"

cat "$PLAYLIST_PATH" | sed -E "s|(^plugin://.*?$)|pipe://$SCRIPT_PATH/tvh.sh \"\1\"|g"