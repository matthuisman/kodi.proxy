#!/bin/bash
echo "export OVERRIDE_LA_URL='$2'"
echo "WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000 gst-play-1.0 '$1' --videosink 'h264parse ! nvv4l2decoder ! nvvidconv ! video/x-raw,width=(int)1920,height=(int)1080 ! waylandsink'"
#export OVERRIDE_LA_URL='$2'
#WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000 gst-play-1.0 '$1' --videosink "h264parse ! nvv4l2decoder ! nvvidconv ! video/x-raw,width=(int)1920,height=(int)1080 ! waylandsink"