#!/bin/sh
OUTPUT="$(PROXY_TYPE=TVH DEBUG=0 ./proxy.py $1)"
echo $OUTPUT