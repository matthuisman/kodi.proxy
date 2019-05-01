import os
import sys
import time
import io
import json
import urllib
import urlparse
import xml.etree.ElementTree as ET

from collections import defaultdict

import polib

import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs

progam_dir = 'C:\Program Files\Kodi'
dir_path   = os.path.dirname(os.path.realpath(__file__))
tmp_dir    = os.path.realpath(os.path.join(dir_path, '../../.tmp/'))
addon_dir  = os.path.realpath(os.path.join(dir_path, '../addons'))
cmd        = os.path.basename(__file__)

def get_argv(position, default=None):
    try:
        return sys.argv[position]
    except IndexError:
        return default

def run(url='', file='default.py'):
    os.environ['ADDON_DEV'] = '1'

    if len(sys.argv) == 3:
        file = get_argv(1)
        url  = get_argv(2)
    else:
        url = get_argv(1, url)

    _run(url, file)

def _run(url='', file='default.py'):
    split      = urlparse.urlsplit(url)
    addon_id   = split.netloc or os.path.basename(os.getcwd())
    addon_path = os.path.join(addon_dir, addon_id)
    fragment   = urllib.quote(split.fragment, ':&=') if split.fragment else ''
    query      = urllib.quote(split.query, ':&=') if split.query else ''

    if query and fragment:
        query = '?' + query + '%23' + fragment
    elif query:
        query = '?' + query
    elif fragment:
        query = '#' + fragment

    url = '{}://{}{}'.format(split.scheme or 'plugin', addon_id, split.path or '/')

    file_path = os.path.join(addon_path, file)
    sys.argv = [url, 1, query, 'resume:false']

    sys.path.insert(0, addon_path)
    cur_dir = os.getcwd()
    os.chdir(progam_dir)
    
    print("calling {} {}".format(file_path, sys.argv))
    start = time.time()
    execfile(file_path)
    print("**** time: {0:.3f} s *****\n".format(time.time() - start))
    
    sys.path.pop(0)
    os.chdir(cur_dir)

def _func_print(name, locals):
    locals.pop('self')
    print("{}: {}".format(name, locals))

## xbmc ##

LOG_LABELS = {
    xbmc.LOGNONE: 'None',
    xbmc.LOGDEBUG: 'DEBUG',
    xbmc.LOGINFO: 'INFO',
    xbmc.LOGWARNING: 'WARNING',
    xbmc.LOGERROR: 'ERROR',
    xbmc.LOGFATAL: 'FATAL',
}

def log(msg, level=xbmc.LOGDEBUG):
    print('{} - {}'.format(LOG_LABELS[level], msg))

def getInfoLabel(cline):
    return {
        'System.BuildVersion': '18.0.1',
    }.get(cline, "")

def executebuiltin(function, wait=False):
    print("XBMC Builtin: {}".format(function))
    if function.startswith('XBMC.RunPlugin'):
        url = '?'+function.split('?')[1].rstrip('")')
        _run(url=url)

def translatePath(path):
    if path.startswith('special://temp/'):
        return os.path.join(tmp_dir, os.path.basename(path))

    return path

def getCondVisibility(condition):
    print("Get visibility condition: {}".format(condition))
    return False

def getLanguage(format):
    return 'eng'

def Player_play(self, item="", listitem=None, windowed=False, startpos=-1):
    _func_print('Play', locals())

def Montor_waitForAbort(self, timeout=-1):
    time.sleep(timeout)
    return False

def Montor_abortRequested(self):
    return False

xbmc.log                    = log
xbmc.getInfoLabel           = getInfoLabel
xbmc.executebuiltin         = executebuiltin
xbmc.translatePath          = translatePath
xbmc.getCondVisibility      = getCondVisibility
xbmc.Player.play            = Player_play
xbmc.Monitor.waitForAbort   = Montor_waitForAbort
xbmc.Monitor.abortRequested = Montor_abortRequested
xbmc.getLanguage            = getLanguage

## xbmcaddon ##

def Addon_init(self, addon_id=None):
    if not addon_id:
        addon_id = urlparse.urlsplit(sys.argv[0]).netloc

    profile = os.path.join(tmp_dir, addon_id)
    path = os.path.join(addon_dir, addon_id)

    self._info = {
        'id': addon_id,
        'path': path,
        'name': addon_id,
        'profile': profile,
        'version': 'X',
        'fanart': 'fanart.jpg',
        'icon': 'icon.png',
    }

    addon_xml_path = os.path.join(path, 'addon.xml')
    if not os.path.exists(addon_xml_path):
        print("WARNING: Missing {}".format(addon_xml_path))
    else:
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()
        for key in root.attrib:
            self._info[key] = root.attrib[key]

    self._settings = {}
    settings_path = os.path.join(path, 'resources', 'settings.xml')
    if not os.path.exists(settings_path):
        print("WARNING: Missing {}".format(settings_path))
    else:
        tree = ET.parse(settings_path)
        root = tree.getroot()
        for child in root:
            if 'id' in child.attrib:
                self._settings[child.attrib['id']] = child.attrib.get('default')

    self._strings  = {}
    
    po_path = os.path.join(path, 'resources', 'language', 'resource.language.en_gb', 'strings.po')
    if not os.path.exists(po_path):
        print("WARNING: Missing {}".format(po_path))
    else:
        try:
            po = polib.pofile(po_path)
            for entry in po:
                self._strings[int(entry.msgctxt.lstrip('#'))] = entry.msgid
        except:
            print("WARNING: Failed to parse PO File: {}".format(po_path))

    settings_json_path = os.path.join(self._info['profile'], 'settings.json')
    if os.path.exists(settings_json_path):
        with io.open(os.path.join(self._info['profile'], 'settings.json'), 'r', encoding='utf-8') as f:
            self._settings.update(json.loads(f.read()))

    if id == 'inputstream.adaptive':
        self._info.update({
            'version': '2.1.0',
        })

        self._settings.update({
            'DECRYPTERPATH': self._info['profile'],
        })

def Addon_getLocalizedString(self, id):
    return self._strings.get(id, '')

def Addon_openSettings(self):
    print("OPEN SETTINGS!")

def Addon_getSetting(self, id):
    return str(self._settings.get(id, ""))

def Addon_setSetting(self, id, value):
    self._settings[str(id)] = str(value)

    if not os.path.exists(self._info['profile']):
        os.makedirs(self._info['profile'])

    with io.open(os.path.join(self._info['profile'], 'settings.json'), 'w', encoding='utf8') as f:
        f.write(unicode(json.dumps(self._settings, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)))

def Addon_getAddonInfo(self, id):
    return self._info.get(id, "")

xbmcaddon.Addon.__init__           = Addon_init
xbmcaddon.Addon.getLocalizedString = Addon_getLocalizedString
xbmcaddon.Addon.openSettings       = Addon_openSettings
xbmcaddon.Addon.getSetting         = Addon_getSetting
xbmcaddon.Addon.setSetting         = Addon_setSetting
xbmcaddon.Addon.getAddonInfo       = Addon_getAddonInfo

## xbmcgui ##

def Dialog_yesno(self, heading, line1, line2="", line3="", nolabel="No", yeslabel="Yes", autoclose=0):
    return raw_input("{}: {} {} {}\n{}/({}): ".format(heading, line1, line2, line3, yeslabel, nolabel)).strip().lower() == yeslabel.strip().lower()

def Dialog_ok(self, heading, line1, line2="", line3=""):
    raw_input('\n{}\n {} {} {} [OK]'.format(heading, line1, line2, line3))

def Dialog_textviewer(self, heading, message):
    raw_input('\n{}\n {} [OK]'.format(heading, message))

def Dialog_notification(self, heading, message, icon="", time=0, sound=True):
    _func_print('Notification', locals())

def Dialog_select(self, heading, list, autoclose=0, preselect=-1, useDetails=False):
    for idx, item in enumerate(list):
        print('{}: {}'.format(idx, item.encode('utf-8')))
    return int(raw_input('{}: '.format(heading)))

def Dialog_input(self, heading, defaultt="", type=0, option=0, autoclose=0):
    return raw_input('{0} ({1}): '.format(heading, defaultt)).strip() or defaultt

def DialogProgress_create(self, heading, line1="", line2="", line3=""):
    print('Progress: {} {} {} {}'.format(heading, line1, line2, line3))

def ListItem_init(self, label="", label2="", iconImage="", thumbnailImage="", path=""):
    self._data = defaultdict(dict)
    _locals = locals()
    _locals.pop('self')
    self._data.update(_locals)

def ListItem_setLabel(self, label):
    self._data['label'] = label

def ListItem_getLabel(self):
    return self._data.get('label', '').encode('utf-8')

def ListItem_setArt(self, dictionary):
    self._data['art'] = dictionary

def ListItem_setInfo(self, type, infoLabels):
    self._data['info'][type] = infoLabels

def ListItem_addStreamInfo(self, cType, dictionary):
    self._data['stream_info'][cType] = dictionary

def ListItem_addContextMenuItems(self, items, replaceItems=False):
    self._data['context'] = items

def ListItem_setProperty(self, key, value):
    self._data['property'][key] = value

def ListItem_setPath(self, path):
    self._data['path'] = path

def ListItem_getPath(self):
    return self._data.get('path', '')

def ListItem_str(self):
    return str(json.loads(json.dumps(self._data)))

def ListItem_repr(self):
    return self.__str__()

WINDOW_DATA = {}
def Window_init(self, existingWindowId=-1):
    global WINDOW_DATA
    self._window_id = existingWindowId
    if existingWindowId not in WINDOW_DATA:
        WINDOW_DATA[existingWindowId] = {}

def Window_getProperty(self, key):
    return WINDOW_DATA[self._window_id].get(key, "")

def Window_setProperty(self, key, value):
    global WINDOW_DATA
    WINDOW_DATA[self._window_id][key] = value

def Window_clearProperty(self, key):
    global WINDOW_DATA
    WINDOW_DATA[self._window_id].pop(key, None)

xbmcgui.Dialog.yesno                 = Dialog_yesno
xbmcgui.Dialog.ok                    = Dialog_ok
xbmcgui.Dialog.textviewer            = Dialog_textviewer
xbmcgui.Dialog.notification          = Dialog_notification
xbmcgui.Dialog.input                 = Dialog_input
xbmcgui.DialogProgress.create        = DialogProgress_create
xbmcgui.DialogProgress.iscanceled    = lambda self:False
xbmcgui.Dialog.select                = Dialog_select

xbmcgui.ListItem.__init__            = ListItem_init
xbmcgui.ListItem.setLabel            = ListItem_setLabel
xbmcgui.ListItem.getLabel            = ListItem_getLabel
xbmcgui.ListItem.setArt              = ListItem_setArt
xbmcgui.ListItem.setInfo             = ListItem_setInfo
xbmcgui.ListItem.addStreamInfo       = ListItem_addStreamInfo
xbmcgui.ListItem.addContextMenuItems = ListItem_addContextMenuItems
xbmcgui.ListItem.setProperty         = ListItem_setProperty
xbmcgui.ListItem.setPath             = ListItem_setPath
xbmcgui.ListItem.getPath             = ListItem_getPath
xbmcgui.ListItem.__str__             = ListItem_str
xbmcgui.ListItem.__repr__            = ListItem_repr

xbmcgui.Window.__init__              = Window_init
xbmcgui.Window.getProperty           = Window_getProperty
xbmcgui.Window.setProperty           = Window_setProperty
xbmcgui.Window.clearProperty         = Window_clearProperty

## xbmcplugin ##
def _init_data():
    return {'items': [], 'sort': [], 'content': '', 'category': ''}
    
DATA = _init_data()

def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
    global DATA
    DATA['items'].append((url, listitem, isFolder))
    return True

def addDirectoryItems(handle, items, totalItems=0):
    global DATA
    for item in items:
        DATA['items'].append(item)
    return True

def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
    global DATA
    if not succeeded:
        return

    print('Title: {category}\nContent: {content}'.format(**DATA))
    for item in DATA['items']:
        print("\nLabel: {}\nUrl: {}\nItem: {}\nIs Folder: {}".format(item[1].getLabel(), '{} "{}"'.format(cmd, item[0]), item[1], item[2]))

    print("")

    DATA = _init_data()

def setResolvedUrl(handle, succeeded, listitem):
    print("Resolved: {0}".format(listitem))

def addSortMethod(handle, sortMethod, label2Mask=""):
    global DATA
    DATA['sort'].append(sortMethod)

def setContent(handle, content):
    global DATA
    DATA['content'] = content

def setPluginCategory(handle, category):
    global DATA
    DATA['category'] = category

xbmcplugin.addDirectoryItem  = addDirectoryItem
xbmcplugin.addDirectoryItems = addDirectoryItems
xbmcplugin.endOfDirectory    = endOfDirectory
xbmcplugin.setResolvedUrl    = setResolvedUrl
xbmcplugin.addSortMethod     = addSortMethod
xbmcplugin.setContent        = setContent
xbmcplugin.setPluginCategory = setPluginCategory


## xbmcvfs ##

def exists(path):
    return os.path.exists(path)

def mkdir(path):
    return os.mkdir(path)

def mkdirs(path):
    return os.makedirs(path)

def delete(file):
    return os.remove(file)

xbmcvfs.exists = exists
xbmcvfs.mkdir  = mkdir
xbmcvfs.mkdirs = mkdirs
xbmcvfs.delete = delete

run()