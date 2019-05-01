from urlparse import parse_qsl
from urllib import urlencode

from . import signals
from .constants import ROUTE_TAG, ADDON_ID, ROUTE_LIVE_TAG, ROUTE_LIVE_SUFFIX, ROUTE_URL_TAG
from .log import log
from .language import _
from .exceptions import RouterError

_routes = {}

# @router.add('_settings', settings)
def add(url, f):
    if url == None:
        url = f.__name__
    _routes[url] = f

# @router.route('_settings')
def route(url):
    def decorator(f):
        add(url, f)
        return f
    return decorator

# @router.parse_url('?_=_settings')
def parse_url(url):
    if url.startswith('?'):
        params   = dict(parse_qsl(url.lstrip('?')))
        _url     = params.pop(ROUTE_TAG, '')
    else:
        params = {}
        _url = url

    params[ROUTE_URL_TAG] = url

    function = _routes.get(_url)

    if not function:
        raise RouterError(_(_.ROUTER_NO_FUNCTION, raw_url=url, parsed_url=_url))

    log('Router Parsed: \'{0}\' => {1} {2}'.format(url, function.__name__, params))

    return function, params

def url_for_func(func, **kwargs):
    for url in _routes:
        if _routes[url].__name__ == func.__name__:
            return build_url(url, **kwargs)

    raise RouterError(_(_.ROUTER_NO_URL, function_name=func.__name__))

def url_for(func_or_url, **kwargs):
    if callable(func_or_url):
        return url_for_func(func_or_url, **kwargs)
    else:
        return build_url(func_or_url, **kwargs)

def build_url(url, addon_id=ADDON_ID, **kwargs):
    kwargs[ROUTE_TAG] = url
    is_live = kwargs.pop('_is_live', False)

    params = []
    for k in sorted(kwargs):
        if kwargs[k] == None:
            continue

        try: params.append((k, unicode(kwargs[k]).encode('utf-8')))
        except: params.append((k, kwargs[k]))

    if is_live:
        params.append((ROUTE_LIVE_TAG, ROUTE_LIVE_SUFFIX))

    return 'plugin://{0}/?{1}'.format(addon_id, urlencode(params))

# router.dispatch('?_=_settings')
def dispatch(url):
    with signals.throwable():
        signals.emit(signals.BEFORE_DISPATCH)
        function, params = parse_url(url)
        function(**params)

    signals.emit(signals.AFTER_DISPATCH)