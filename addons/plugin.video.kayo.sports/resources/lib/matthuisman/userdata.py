from . import settings
from .constants import USERDATA_KEY

_userdata = settings.getDict(USERDATA_KEY, {})

def get(key, default=None):
    return _userdata.get(key, default)

def set(key, value):
    _userdata[key] = value
    save()

def save():
    settings.setDict(USERDATA_KEY, _userdata)

def delete(key):
    if key in _userdata:
        del _userdata[key]
        save()
    
def clear():
    _userdata.clear()
    save()