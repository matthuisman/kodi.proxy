import json
import sys
from time import time
from functools import wraps

import xbmcgui

from .log import log
from .util import hash_6
from .constants import ADDON_ID, CACHE_EXPIRY, ROUTE_CLEAR_CACHE
from . import signals, gui, router, settings

cache_key = 'cache.'+ADDON_ID
_window   = xbmcgui.Window(10000)

class Cache(object):
    data = {}

cache = Cache()

@signals.on(signals.BEFORE_DISPATCH)
def load():
    if not cache.data and settings.getBool('persist_cache', True):
        cache.data = json.loads(_window.getProperty(cache_key) or "{}")
        _window.setProperty(cache_key, "{}")

def set(key, value, expires=CACHE_EXPIRY):
    expires = int(time() + expires)
    cache.data[key] = [value, expires]
    
def get(key, default=None):
    try:
        row = cache.data[key]
    except KeyError:
        return default

    if row[1] < time():
        cache.data.pop(key, None)
        return default
    else:
        return row[0]

def delete(key):
    return int(cache.data.pop(key, None) != None)

def empty():
    deleted = len(cache.data)
    cache.data.clear()
    log('Mem Cache: Deleted {} Rows'.format(deleted))

def key_for(f, *args, **kwargs):
    func_name = f.__name__ if callable(f) else f
    if not enabled() or func_name not in funcs:
        return None

    return _build_key(func_name, *args, **kwargs)

def _build_key(func_name, *args, **kwargs):
    key = func_name

    def to_str(item):
        try:
            return item.encode('utf-8')
        except:
            return str(item)

    def is_primitive(item):
        return type(item) in (int, str, dict, list, bool, float, unicode)
    
    for k in sorted(args):
        if is_primitive(k):
            key += to_str(k)

    for k in sorted(kwargs):
        if is_primitive(kwargs[k]):
            key += to_str(k) + to_str(kwargs[k])

    return hash_6(key)

def cached(*args, **kwargs):
    def decorator(f, expires=CACHE_EXPIRY, key=None):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            _key = key or _build_key(f.__name__, *args, **kwargs)
            if callable(_key):
                _key = _key(*args, **kwargs)

            if not kwargs.pop('_skip_cache', False):
                value = get(_key)
                if value != None:
                    log('Cache Hit: {}'.format(_key))
                    return value

            value = f(*args, **kwargs)
            if value != None:
                set(_key, value, expires)

            return value

        return decorated_function

    return lambda f: decorator(f, *args, **kwargs)

@signals.on(signals.AFTER_DISPATCH)
def remove_expired():
    _time = time()
    delete  = []

    for key in cache.data.keys():
        if cache.data[key][1] < _time:
            delete.append(key)

    for key in delete:
        cache.data.pop(key, None)

    if delete:
        log('Mem Cache: Deleted {} Expired Rows'.format(len(delete)))

    if settings.getBool('persist_cache', True):
        _window.setProperty(cache_key, json.dumps(cache.data))
        cache.data.clear()

@router.route(ROUTE_CLEAR_CACHE)
def clear_cache(key, **kwargs):
    delete_count = delete(key)
    msg = _(_.PLUGIN_CACHE_REMOVED, delete_count=delete_count)
    gui.notification(msg)