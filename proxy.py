import os
import sys
import time
import io
import json
import shutil
import traceback
from collections import defaultdict
import xml.etree.ElementTree as ET
import urlparse
import urllib
import imp

import polib

import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs

kodi_home  = os.path.dirname(os.path.realpath(__file__))
repo_url   = 'http://k.mjh.nz/.repository/addons.xml'
cmd        = os.path.basename(__file__)

DEBUG = False

def get_argv(position, default=None):
    try:
        return sys.argv[position]
    except IndexError:
        return default

def run():
    url    = get_argv(1, '')
    module = get_argv(2, 'default')

    os.environ['ADDON_DEV'] = get_argv(3, '0')

    _run(url, module)

def _run(url='', module='default'):
    split      = urlparse.urlsplit(url)
    addon_id   = split.netloc or os.path.basename(os.getcwd())

    addon_dir  = translatePath('special://home/addons')
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

    sys.argv = [url, 1, query, 'resume:false']

    _opath = sys.path[:]
    _ocwd = os.getcwd()

    sys.path.insert(0, addon_path)
    os.chdir(addon_path)
    
    log("Calling {} {} {}".format(addon_id, module, sys.argv))

    f, filename, description = imp.find_module(addon_id, [addon_dir])
    package = imp.load_module(addon_id, f, filename, description)

    f, filename, description = imp.find_module(module, package.__path__)

    start = time.time()
    try:
        module = imp.load_module('{}.{}'.format(addon_id, module), f, filename, description)
    finally:
        f.close()

    log("**** time: {0:.3f} s *****\n".format(time.time() - start))
    
    sys.path = _opath
    os.chdir(_ocwd)

def _func_print(name, locals):
    locals.pop('self')
    log("{}: {}".format(name, locals))

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
    if DEBUG:
        print('{} - {}'.format(LOG_LABELS[level], msg))

def getInfoLabel(cline):
    return {
        'System.BuildVersion': '18.0.1',
    }.get(cline, "")

def executebuiltin(function, wait=False):
    log("XBMC Builtin: {}".format(function))
    if function.startswith('XBMC.RunPlugin'):
        _run(function.replace('XBMC.RunPlugin(', '').rstrip('")'))

def translatePath(path):
    translates = {
        'special://home/': kodi_home,
        'special://temp/': os.path.join(kodi_home, 'temp'),
    }

    for translate in translates:
        if translate in path:
            path = os.path.join(translates[translate], path.replace(translate, ''))
            return os.path.realpath(path)

    return path

def getCondVisibility(condition):
    log("Get visibility condition: {}".format(condition))
    return False

def getLanguage(format):
    return 'eng'

def Player_play(self, item="", listitem=None, windowed=False, startpos=-1):
    _func_print('Play', locals())

def Montor_waitForAbort(self, timeout=0):
    log("Wait for Abort: {}".format(timeout))
    time.sleep(1)
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
    
    self._info = {
        'id': addon_id,
        'name': addon_id,
        'path': translatePath('special://home/addons/'+addon_id),
        'profile': translatePath('special://home/userdata/addon_data/'+addon_id),
        'version': 'X',
        'fanart': 'fanart.jpg',
        'icon': 'icon.png',
    }

    self._settings = {}
    self._strings  = {}

    addon_xml_path     = os.path.join(self._info['path'], 'addon.xml')
    settings_path      = os.path.join(self._info['path'], 'resources', 'settings.xml')
    po_path            = os.path.join(self._info['path'], 'resources', 'language', 'resource.language.en_gb', 'strings.po')
    settings_json_path = os.path.join(self._info['profile'], 'settings.json')

    if not os.path.exists(addon_xml_path):
        log("WARNING: Missing {}".format(addon_xml_path))
    else:
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()
        for key in root.attrib:
            self._info[key] = root.attrib[key]

    if not os.path.exists(settings_path):
        log("WARNING: Missing {}".format(settings_path))
    else:
        tree = ET.parse(settings_path)
        for elem in tree.findall('*/setting'):
            if 'id' in elem.attrib:
                self._settings[elem.attrib['id']] = elem.attrib.get('default')
    
    if not os.path.exists(po_path):
        log("WARNING: Missing {}".format(po_path))
    else:
        try:
            po = polib.pofile(po_path)
            for entry in po:
                self._strings[int(entry.msgctxt.lstrip('#'))] = entry.msgid
        except:
            log("WARNING: Failed to parse PO File: {}".format(po_path))

    if os.path.exists(settings_json_path):
        with io.open(settings_json_path, 'r', encoding='utf-8') as f:
            self._settings.update(json.loads(f.read()))

    # if addon_id == 'inputstream.adaptive':
    #     self._settings.update({
    #         'DECRYPTERPATH': self._info['profile'],
    #     })

def Addon_getLocalizedString(self, id):
    return self._strings.get(id, '')

def Addon_openSettings(self):
    log("OPEN SETTINGS!")

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
        log('{}: {}'.format(idx, item.encode('utf-8')))
    return int(raw_input('{}: '.format(heading)))

def Dialog_input(self, heading, defaultt="", type=0, option=0, autoclose=0):
    return raw_input('{0} ({1}): '.format(heading, defaultt)).strip() or defaultt

def DialogProgress_create(self, heading, line1="", line2="", line3=""):
    log('Progress: {} {} {} {}'.format(heading, line1, line2, line3))

def Dialog_browseSingle(self, type, heading, shares, mask='', useThumbs=False, treatAsFolder=False, defaultt=''):
    return raw_input('{0} ({1}): '.format(heading, defaultt)).strip() or defaultt

def ListItem_init(self, label="", label2="", iconImage="", thumbnailImage="", path="", offscreen=False):
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

def Window_init(self, existingWindowId=-1):
    self._window_id   = existingWindowId
    self._window_path = os.path.join(translatePath('special://temp'), 'window-{}.json'.format(self._window_id))

    try:
        with open(self._window_path) as f:
            self._win_data = json.loads(f.read())
    except:
        self._win_data = {}

def Window_getProperty(self, key):
    return self._win_data.get(key, "")

def Window_setProperty(self, key, value):
    self._win_data[key] = value
    self.save()

def Window_clearProperty(self, key):
    self._win_data.pop(key, None)
    self.save()

def Window_save(self):
    with open(self._window_path, 'w') as f:
        f.write(json.dumps(self._win_data))

xbmcgui.Dialog.yesno                 = Dialog_yesno
xbmcgui.Dialog.ok                    = Dialog_ok
xbmcgui.Dialog.textviewer            = Dialog_textviewer
xbmcgui.Dialog.notification          = Dialog_notification
xbmcgui.Dialog.input                 = Dialog_input
xbmcgui.DialogProgress.create        = DialogProgress_create
xbmcgui.DialogProgress.iscanceled    = lambda self:False
xbmcgui.Dialog.select                = Dialog_select
xbmcgui.Dialog.browseSingle          = Dialog_browseSingle

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
xbmcgui.Window.save                  = Window_save

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
    log("Resolved: {0}".format(listitem))

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