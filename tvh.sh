#!/bin/sh

SCRIPT="$(realpath $0)"
SCRIPT_PATH="$(dirname $SCRIPT)"

OUTPUT="$(proxy_type=TVH $SCRIPT_PATH/.env/bin/python $SCRIPT_PATH/proxy.py $1)"

if [ $? -eq 200 ]; then
    shift
    eval "ffmpeg $OUTPUT $@ -vcodec copy -acodec copy -f mpegts pipe:1"
else
    echo "$OUTPUT"
fi
