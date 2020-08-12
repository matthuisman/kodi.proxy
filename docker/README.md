# tvheadend

```
docker build . -t tvh-proxy

docker run -d \
  --name=tvh-proxy \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Pacific/Auckland \
  -p 9981:9981 \
  -p 9982:9982 \
  --restart unless-stopped \
  tvh-proxy
```

Run the below to install the IPTV Merge Plugin
```
docker exec -it -u abc tvh-proxy /usr/share/kodi.proxy/proxy "install://plugin.program.iptv.merge"
```

Easily install / setup other plugins to be used as IPTV sources
```
docker exec -it -u abc tvh-proxy /usr/share/kodi.proxy/proxy
```

Run the IPTV Merge Plugin to setup Playlists and EPG sources
```
docker exec -it -u abc tvh-proxy /usr/share/kodi.proxy/proxy "plugin://plugin.program.iptv.merge"
```

In TvHeadend add a new Automatic IPTV Network and set it's url to
```
pipe:///usr/share/kodi.proxy/iptv_merge.m3u8.sh
```
Also set Maximum timeout to 30 seconds

Enable the below EPG Grabber
```
XMLTV: tv_grab_iptv_merge (MattHuisman.nz)
```