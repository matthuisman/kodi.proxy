#!/bin/sh
scriptdir=$(dirname "$0")

cd scriptdir
source .env/bin/activate
OUTPUT="$(PROXY_TYPE=TVH DEBUG=0 ./proxy.py $1)"

if [ $? -eq 200 ]; then
    eval "ffmpeg $OUTPUT"
else
    echo "$OUTPUT"
fi