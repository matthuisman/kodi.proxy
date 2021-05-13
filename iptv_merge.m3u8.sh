#!/bin/sh

SCRIPT="$(realpath $0)"
SCRIPT_PATH="$(dirname $SCRIPT)"

PLAYLIST_PATH="$(proxy_type=TV_GRAB $SCRIPT_PATH/.env/bin/python $SCRIPT_PATH/proxy.py 'plugin://plugin.program.iptv.merge/?_=proxy_merge&type=playlist' | cut -c 2-)"

if [ $? -eq 200 ]; then
    cat "$PLAYLIST_PATH" | sed -E "s|(^plugin://.*?$)|pipe://$SCRIPT_PATH/tvh.sh \"\1\"|g" | sed -E "s|tvg-logo=\"(/.*?)\"|tvg-logo=\"file://\1\"|g"
else
    >&2 echo "$PLAYLIST_PATH"
fi
