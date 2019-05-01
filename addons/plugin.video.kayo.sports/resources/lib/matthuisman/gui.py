import sys
import traceback
from urllib import quote
from contextlib import contextmanager

import xbmcgui, xbmc, xbmcgui

from .constants import ADDON_ID, ADDON_NAME, ADDON_ICON, ADDON_FANART, GUI_DEFAULT_AUTOCLOSE
from .exceptions import GUIError
from .language import _

def _make_heading(heading=None):
    return heading if heading else ADDON_NAME

def notification(message, heading=None, icon=None, time=3000, sound=False):
    heading = _make_heading(heading)
    icon    = ADDON_ICON if not icon else icon

    xbmcgui.Dialog().notification(heading, message, icon, time, sound)

def refresh():
    xbmc.executebuiltin('Container.Refresh')

def select(heading=None, options=None, **kwargs):
    heading = _make_heading(heading)
    return xbmcgui.Dialog().select(heading, options, **kwargs)

def exception(heading=_.PLUGIN_EXCEPTION):
    exc_type, exc_value, exc_traceback = sys.exc_info()

    tb = []
    for trace in reversed(traceback.extract_tb(exc_traceback)):
        if ADDON_ID in trace[0]:
            trace = list(trace)
            trace[0] = trace[0].split(ADDON_ID)[1]
            tb.append(trace)

    error = '{}\n{}'.format(''.join(traceback.format_exception_only(exc_type, exc_value)), ''.join(traceback.format_list(tb)))

    text(error, heading=heading)

@contextmanager
def progress(message, heading=None, percent=0):
    heading = _make_heading(heading)

    lines = list()
    for line in message.splitlines():
        lines.append(line)

    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, *lines)
    dialog.update(percent)

    try:
        yield dialog
    finally:
        dialog.close()

def input(message, default='', hide_input=False, **kwargs):
    if hide_input:
        kwargs['option'] = xbmcgui.ALPHANUM_HIDE_INPUT
        
    return xbmcgui.Dialog().input(message, default, **kwargs)

def ok(message, heading=None):
    heading = _make_heading(heading)

    lines = list()
    for line in message.splitlines():
        lines.append(line)
    if not lines:
        lines = (heading,)

    return xbmcgui.Dialog().ok(heading, *lines)

def text(message, heading=None, **kwargs):
    heading = _make_heading(heading)
    
    return xbmcgui.Dialog().textviewer(heading, message)

def yes_no(message, heading=None, autoclose=GUI_DEFAULT_AUTOCLOSE, **kwargs):
    heading = _make_heading(heading)

    lines = list()
    for line in message.splitlines():
        lines.append(line)

    if autoclose:
        kwargs['autoclose'] = autoclose

    return xbmcgui.Dialog().yesno(heading, *lines, **kwargs)

class Item(object):
    def __init__(self, id=None, label='', path=None, playable=False, info=None, context=None, 
            headers=None, cookies=None, properties=None, is_folder=None, art=None, inputstream=None,
            video=None, audio=None, subtitles=None):

        self.id          = id
        self.label       = label
        self.path        = path
        self.info        = info or {}
        self.playable    = playable
        self.context     = context or []
        self.headers     = headers or {}
        self.cookies     = cookies or {}
        self.properties  = properties or {}
        self.art         = art or {}
        self.video       = video or {}
        self.audio       = audio or {}
        self.subtitles   = subtitles or []
        self.inputstream = inputstream
        self._is_folder  = is_folder

    @property
    def is_folder(self): 
        return not self.playable if self._is_folder == None else self._is_folder

    @is_folder.setter
    def is_folder(self, value):
        self._is_folder = value

    def get_url_headers(self):
        string = ''
        
        for key in self.headers:
            string += '{0}={1}&'.format(key, quote(self.headers[key]))

        if self.cookies:
            string += 'Cookie='
            for key in self.cookies:
                string += '{0}%3D{1}; '.format(key, quote(self.cookies[key]))

        return string.strip('&')

    def get_li(self):
        try:
            #KODI 18+
            li = xbmcgui.ListItem(offscreen=True)
        except:
            li = xbmcgui.ListItem()

        if self.label:
            li.setLabel(self.label)
            if not self.info.get('plot'):
                self.info['plot'] = self.label
                
            if not self.info.get('title'):
                self.info['title'] = self.label

        if self.path:
            li.setPath(self.path)

        if self.info:
            li.setInfo('video', self.info)

        if self.video:
            li.addStreamInfo('video', self.video)

        if self.audio:
            li.addStreamInfo('audio', self.audio)

        if self.art:
            if 'poster' not in self.art:
                self.art['poster'] = self.art.get('thumb')

            li.setArt(self.art)

        if self.playable:
            li.setProperty('IsPlayable', 'true')

        if self.context:
            li.addContextMenuItems(self.context)

        if self.subtitles:
            li.setSubtitles(self.subtitles)

        for key in self.properties:
            li.setProperty(key, str(self.properties[key]))

        headers = self.get_url_headers()

        if self.inputstream and self.inputstream.check():
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', self.inputstream.manifest_type)

            if self.inputstream.license_type:
                li.setProperty('inputstream.adaptive.license_type', self.inputstream.license_type)
            
            if headers:
                li.setProperty('inputstream.adaptive.stream_headers', headers)

            if self.inputstream.license_key:
                li.setProperty('inputstream.adaptive.license_key', '{url}|Content-Type={content_type}&{headers}|{challenge}|{response}'.format(
                    url = self.inputstream.license_key, 
                    headers = headers,
                    content_type = self.inputstream.content_type,
                    challenge = self.inputstream.challenge,
                    response = self.inputstream.response, 
                ))
            elif headers:
                li.setProperty('inputstream.adaptive.license_key', '|{0}'.format(headers))

            if self.inputstream.mimetype:
                li.setMimeType(self.inputstream.mimetype)
                li.setContentLookup(False)

        if headers and self.path.startswith('http'):
            li.setPath(self.path + '|{}'.format(headers))

        return li

    def play(self):
        li = self.get_li()
        xbmc.Player().play(li.getPath(), li)