#!/bin/sh

SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"

OUTPUT="$(PROXY_TYPE=TVH DEBUG=0 $SCRIPT_PATH/.env/bin/python $SCRIPT_PATH/proxy.py $1)"

if [ $? -eq 200 ]; then
    eval "ffmpeg $OUTPUT"
else
    echo "$OUTPUT"
fi