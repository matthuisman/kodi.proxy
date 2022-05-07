# kodi.proxy

```
git clone https://github.com/matthuisman/kodi.proxy
cd kodi.proxy
pip install virtualenv
virtualenv --python=python3 .env
source .env/bin/activate
pip install -r requirements.txt
chmod +x proxy.py
chmod +x tvh.sh
./proxy.py
```

Example TvHeadend URL:
```
pipe:///root/kodi.proxy/tvh.sh "plugin://plugin.video.kayo.sports/?_=play&_play=1&id=53208&play_type=2&start_from=0&_l=.pvr"
```
