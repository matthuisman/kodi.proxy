#!/bin/sh
if [ $# -eq 0 ]
  then
    ./proxy.py
    exit
fi

OUTPUT="$(PROXY_TYPE=TVH DEBUG=0 ./proxy.py $1)"

if [ $? -eq 200 ]; then
    eval "ffmpeg $OUTPUT"
else
    echo "$OUTPUT"
fi