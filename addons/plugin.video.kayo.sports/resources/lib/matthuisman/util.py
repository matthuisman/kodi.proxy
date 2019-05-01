import os
import time
import hashlib
from datetime import datetime

import xbmc

from .language import _
from .constants import ADDON
from .log import log
from .exceptions import Error 

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def hash_6(value, default=None):
    if not value:
        return default

    h = hashlib.md5(str(value))
    return h.digest().encode('base64')[:6]

def md5sum(filepath):
    if not os.path.exists(filepath):
        return None

    return hashlib.md5(open(filepath,'rb').read()).hexdigest()

def get_kodi_version():
    try:
        return int(xbmc.getInfoLabel("System.BuildVersion").split('.')[0])
    except:
        return 0

def strptime(date, str_format):
    try:
        return datetime.strptime(date, str_format)
    except TypeError:
        return datetime(*(time.strptime(date, str_format)[0:6]))

def process_brightcove(data):
    try:
        raise Error(data[0]['message'])
    except KeyError:
        pass

    sources = []

    for source in data.get('sources', []):
        if not source.get('src'):
            continue

        # HLS
        if source.get('type') == 'application/x-mpegURL' and 'key_systems' not in source:
            sources.append({'source': source, 'type': 'hls', 'order_1': 1, 'order_2': int(source.get('ext_x_version', 0))})

        # MP4
        elif source.get('container') == 'MP4' and 'key_systems' not in source:
            sources.append({'source': source, 'type': 'mp4', 'order_1': 2, 'order_2': int(source.get('avg_bitrate', 0))})

        # Widevine
        elif source.get('type') == 'application/dash+xml' and 'com.widevine.alpha' in source.get('key_systems', ''):
            sources.append({'source': source, 'type': 'widevine', 'order_1': 3, 'order_2': 0})

        elif source.get('type') == 'application/vnd.apple.mpegurl' and 'key_systems' not in source:
            sources.append({'source': source, 'type': 'hls', 'order_1': 1, 'order_2': 0})

    if not sources:
        raise Error(_.NO_BRIGHTCOVE_SRC)

    sources = sorted(sources, key = lambda x: (x['order_1'], -x['order_2']))
    source = sources[0]

    from . import plugin, inputstream

    if source['type'] == 'mp4':
        return plugin.Item(
            path = source['source']['src'],
            art = False,
        )
    elif source['type'] == 'hls':
        return plugin.Item(
            path = source['source']['src'],
            inputstream = inputstream.HLS(),
            art = False,
        )
    elif source['type'] == 'widevine':
        return plugin.Item(
            path = source['source']['src'],
            inputstream = inputstream.Widevine(license_key=source['source']['key_systems']['com.widevine.alpha']['license_url']),
            art = False,
        )
    else:
        raise Error(_.NO_BRIGHTCOVE_SRC)