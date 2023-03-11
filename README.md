# kodi.proxy

```
git clone https://github.com/matthuisman/kodi.proxy
cd kodi.proxy
pip install virtualenv
virtualenv --python=python3 .env
source .env/bin/activate
chmod +x proxy.py
chmod +x tvh.sh
python3 proxy.py
```

Example TvHeadend URL:
```
pipe:///root/kodi.proxy/tvh.sh "plugin://plugin.video.kayo.sports/?_=play&_play=1&id=53208&play_type=2&start_from=0&_l=.pvr"
```

If you want to use the Slyguy proxy for its various features (force quality, dns / proxy overwrites etc) then you need to run the proxy service with 
```./proxy.py "plugin://script.module.slyguy" service```

With the above running, the proxy.py will return urls that route via the above SlyGuy proxy.
