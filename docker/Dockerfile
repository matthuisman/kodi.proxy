FROM linuxserver/tvheadend

RUN apk add --no-cache py-virtualenv wget

RUN cd /usr/share \
    && wget -O proxy.tar.gz https://codeload.github.com/matthuisman/kodi.proxy/tar.gz/5e06d75b9e9eafcbee9972c8028b74db4df0387b \
    && tar -xf proxy.tar.gz \
    && rm proxy.tar.gz \
    && mv kodi.proxy-* kodi.proxy \
    && cd kodi.proxy \
    && echo "userdata=/config/kodi.proxy" >> config.ini \
    && virtualenv --python=python2.7 .env \
    && .env/bin/pip install -r requirements.txt \
    && chmod 555 proxy tv_grab_iptv_merge iptv_merge.m3u8.sh tvh.sh \
    && ln -s /usr/share/kodi.proxy/tv_grab_iptv_merge /usr/bin/tv_grab_iptv_merge

COPY 40-config /etc/cont-init.d/40-config