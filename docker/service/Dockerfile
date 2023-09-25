FROM linuxserver/tvheadend

RUN apk add --no-cache python3 py3-virtualenv wget git

RUN cd /usr/share \
    && wget -O proxy.tar.gz https://codeload.github.com/matthuisman/kodi.proxy/tar.gz/master \
    && tar -xf proxy.tar.gz \
    && rm proxy.tar.gz \
    && mv kodi.proxy-* kodi.proxy \
    && cd kodi.proxy \
    && echo "userdata=/config/kodi.proxy" >> config.ini \
    && python proxy.py "install://script.module.slyguy"

COPY 40-config /etc/cont-init.d/40-config

CMD [ "python", "-u", "proxy.py", "plugin://script.module.slyguy", "service" ]
