#!/usr/bin/env python3
from __future__ import print_function
import os
import sys
import time
import json
import shutil
import subprocess
import platform
import xml.etree.ElementTree as ET
import re
import zipfile
import configparser
import threading
import ssl
import urllib.request
from gzip import GzipFile
from collections import defaultdict
from urllib.parse import urlsplit, unquote_plus, quote_plus, parse_qsl

kodi_home = os.path.dirname(os.path.realpath(__file__))
cmd = os.path.basename(__file__)
sys.path.append(os.path.join(kodi_home, 'lib'))

import polib
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs

TVHEADEND = 'TVH'
SHELL = 'SHELL'
HTTP = 'HTTP'
TV_GRAB = 'TV_GRAB'
KODI = 'KODI'

SETTINGS = {
    'userdata': kodi_home,
    'proxy_type': SHELL,
    'interactive': None,
    'addons_url': 'https://slyguy.uk/.repo/addons.json.gz',
    'debug': 0,
}

config = configparser.RawConfigParser(defaults=SETTINGS)
config.read(os.path.join(kodi_home, 'config.ini'))

for key in SETTINGS:
    SETTINGS[key] = os.environ.get(key, config.get('DEFAULT', key))

addons_dir = os.path.join(SETTINGS['userdata'], 'addons')
addons_data = os.path.join(SETTINGS['userdata'], 'addon_data')
tmp_dir = os.path.join(SETTINGS['userdata'], 'tmp')

if SETTINGS['interactive'] == None:
    SETTINGS['interactive'] = SETTINGS['proxy_type'] == SHELL

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

if not os.path.exists(addons_dir):
    os.makedirs(addons_dir)

if not os.path.exists(addons_data):
    os.makedirs(addons_data)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class ProxyException(Exception):
    pass

def run_plugin(path, wait=True):
    def run():
        env_mapper = os.environ.copy()
        env_mapper.update({'proxy_type': KODI})
        return subprocess.check_output([sys.executable, os.path.join(kodi_home, cmd), path], env=env_mapper).decode('utf-8').split('\n')

    if wait:
        return run()

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    return thread

def get_argv(position, default=None):
    try:
        return sys.argv[position]
    except IndexError:
        return default

CACHE = {}
def get_addons():
    # TODO: add expiry
    if 'addons' not in CACHE:
        with urllib.request.urlopen(SETTINGS['addons_url'], context=ctx) as f:
            CACHE['addons'] = json.loads(GzipFile(fileobj=f).read())

    return CACHE['addons']

def install(addon_id):
    addon_path = os.path.join(addons_dir, addon_id)
    addon = get_addons()[addon_id]
    url = addon['src'] + '{}-{}.zip'.format(addon_id, addon['version'])
    local_filename = os.path.join(addons_dir, addon_id+'.zip')

    if os.path.exists(local_filename):
        os.remove(local_filename)

    urllib.request.urlretrieve(url, local_filename)

    if os.path.exists(addon_path):
        shutil.move(addon_path, addon_path+".bu")

    try:
        zip = zipfile.ZipFile(local_filename)
        zip.extractall(path=addons_dir)
        zip.close()
    except:
        if os.path.exists(addon_path):
            shutil.rmtree(addon_path)

        if os.path.exists(addon_path+".bu"):
            shutil.move(addon_path+".bu", addon_path)
    else:
        addon_xml_path = os.path.join(addons_dir, addon_id, 'addon.xml')
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()
        version = root.attrib['version']

        _print('{} ({}): Installed'.format(addon_id, version))
        if os.path.exists(addon_path+".bu"):
            shutil.rmtree(addon_path+".bu")
    finally:
        os.remove(local_filename)

def _get_installed_addons():
    return [f for f in os.listdir(addons_dir) if os.path.exists(os.path.join(addons_dir, f, 'addon.xml'))]

def menu(url='', module='default'):
    cmds = ['install', 'uninstall', 'update', 'plugin']

    installed_addons = _get_installed_addons()

    split = urlsplit(url)
    addon_id = split.netloc.lower()
    cmd = split.scheme.lower()

    if not cmd and not SETTINGS['interactive']:
        return

    _print("")

    if cmd not in cmds:
        for idx, option in enumerate(cmds):
            _print('{}: {}'.format(idx, option))

        selected = int(get_input('\nSelect: '))
        if selected < 0:
            return

        return menu(url='{}://'.format(cmds[selected]))

    if cmd == 'install':
        addons = get_addons()

        if not addon_id:
            _print('{}: {}'.format(0, 'ALL'))

            options = ['ALL']

            for idx, addon_id in enumerate(sorted(addons, key=lambda x: addons[x]['name'].lower()), start=1):
                addon = addons[addon_id]
                label = '{name} ({version})'.format(**addon)
                options.append(addon_id)
                if addon_id in installed_addons:
                    label += ' [INSTALLED]'

                _print('{}: {}'.format(idx, label))

            addon_id = options[int(get_input('\nSelect: '))]
            return menu(url='install://{}'.format(addon_id))

        if addon_id == 'all':
            to_install = addons.keys()
        elif addon_id in installed_addons:
            raise ProxyException('{} already installed'.format(addon_id))
        else:
            to_install = [addon_id]

        for addon_id in to_install:
            load_dependencies(addon_id, install_missing=True)

    elif cmd == 'uninstall':
        if not installed_addons:
            raise ProxyException('No addons installed')

        if not addon_id:
            options = installed_addons[:]
            options.insert(0, 'all')

            for idx, addon in enumerate(options):
                _print('{}: {}'.format(idx, addon))

            addon_id = options[int(get_input('\nSelect: '))]
            return menu(url='uninstall://{}'.format(addon_id))

        if addon_id == 'all':
            to_uninstall = installed_addons
        elif addon_id not in installed_addons:
            raise ProxyException('{} is not installed.'.format(addon_id))
        else:
            to_uninstall = [addon_id]

        for addon_id in to_uninstall:
            addon_data = os.path.join(addons_data, addon_id)
            if os.path.exists(addon_data) and int(get_input('{}\n\n0: Keep addon data\n1: Delete addon data\n\nSelect :'.format(addon_id), 0)) == 1:
                shutil.rmtree(addon_data)

            addon_dir = os.path.join(addons_dir, addon_id)
            shutil.rmtree(addon_dir)

            _print('{} Uninstalled'.format(addon_id))

    elif cmd == 'update':
        if not addon_id:
            options = installed_addons[:]
            options.insert(0, 'all')

            for idx, addon in enumerate(options):
               _print('{}: {}'.format(idx, addon))

            addon_id = options[int(get_input('\nSelect: '))]
            return menu(url='update://{}'.format(addon_id))

        if addon_id == 'all':
            to_update = installed_addons
        else:
            to_update = [addon_id]

        if not to_update:
            raise ProxyException('No addons to update')

        addons = get_addons()
        for addon in to_update:
            addon_xml_path = os.path.join(addons_dir, addon, 'addon.xml')
            tree = ET.parse(addon_xml_path)
            root = tree.getroot()
            version = root.attrib['version']

            if version == addons[addon]['version']:
                _print('{} ({}): Upto date'.format(addon, version))
                continue

            install(addon)

    elif cmd == 'plugin':
        if not addon_id:
            options = []
            for addon in installed_addons:
                addon_xml_path = os.path.join(addons_dir, addon, 'addon.xml')
                with open(addon_xml_path) as f:
                    if 'xbmc.python.pluginsource' not in f.read():
                        continue
                options.append(addon)

            for idx, addon in enumerate(options):
                _print('{}: {}'.format(idx, addon))

            addon_id = options[int(get_input('\nSelect: '))]
            return menu(url='plugin://{}'.format(addon_id))

        run(url, module)
        while next_path:
            run(next_path, module)

start_path = None
last_path = None
current_path = None
next_path = None

def run(url=None, module='default'):
    global last_path, current_path, start_path, next_path

    next_path = None

    url = url or get_argv(0, '')
    split = urlsplit(url)
    addon_id = split.netloc or os.path.basename(os.getcwd())

    addon_path = os.path.join(addons_dir, addon_id)
    fragment = quote_plus(split.fragment, ':&=') if split.fragment else ''
    query = quote_plus(split.query, ':&=') if split.query else ''
    filename = module + '.py'
    file_path = os.path.join(addon_path, filename)

    if not os.path.exists(file_path):
        filename = 'default.py'
        file_path = os.path.join(addon_path, filename)

    if query and fragment:
        query = '?' + query + '%23' + fragment
    elif query:
        query = '?' + query
    elif fragment:
        query = '#' + fragment

    if not start_path:
        start_path = url

    if last_path == start_path:
        last_path = None
    else:
        last_path = current_path

    current_path = url

    _print(current_path+'\n')

    url = '{}://{}{}'.format(split.scheme or 'plugin', addon_id, split.path or '/')

    sys.argv = [url, 1, query, 'resume:false']

    _opath = sys.path[:]
    _ocwd = os.getcwd()

    load_dependencies(addon_id, install_missing=True)
    sys.path.insert(0, addon_path)
    os.chdir(addon_path)

    log("Calling {} {} {}".format(addon_id, module, sys.argv))

    start = time.time()
    exec(open(file_path, encoding="utf-8").read(), dict(__file__=file_path))
    print("**** time: {0:.3f} s *****\n".format(time.time() - start))

    sys.path = _opath
    os.chdir(_ocwd)

def load_dependencies(addon_id, optional=False, install_missing=False):
    addon_xml_path = os.path.join(addons_dir, addon_id, 'addon.xml')
    if not os.path.exists(addon_xml_path):
        if optional:
            return

        if install_missing:
            install(addon_id)
        else:
            raise Exception('Required addon dependency "{}" not installed'.format(addon_id))

    addon_path = os.path.join(addons_dir, addon_id)
    addon_xml_path = os.path.join(addon_path, 'addon.xml')
    if not os.path.exists(addon_xml_path):
        return

    tree = ET.parse(addon_xml_path)
    root = tree.getroot()

    for elem in root.findall("./extension"):
        if elem.attrib.get('point').lower() == 'xbmc.python.module':
            path = os.path.normpath(os.path.join(addon_path, elem.attrib['library']))
            sys.path.insert(0, path)

    for elem in root.findall("./requires/import"):
        if elem.attrib['addon'] != addon_id:
            load_dependencies(elem.attrib['addon'], optional=elem.attrib.get('optional', 'false').lower() == 'true', install_missing=install_missing)

def _func_print(name, locals):
    locals.pop('self')
    log("{}: {}".format(name, locals))

## xbmc ##

INFO_LABELS = {
    'System.BuildVersion': '19.2',
}

LOG_LABELS = {
    xbmc.LOGNONE: 'None',
    xbmc.LOGDEBUG: 'DEBUG',
    xbmc.LOGINFO: 'INFO',
    xbmc.LOGWARNING: 'WARNING',
    xbmc.LOGERROR: 'ERROR',
    xbmc.LOGFATAL: 'FATAL',
}

def log(msg, level=xbmc.LOGDEBUG):
    if SETTINGS['debug']:
        _print('{} - {}'.format(LOG_LABELS[level], msg))

def getInfoLabel(cline):
    return INFO_LABELS.get(cline, '')

def executebuiltin(function, wait=False):
    log("XBMC Builtin: {}".format(function))
    global next_path

    if function == 'Container.Refresh':
        next_path = last_path

    elif function.startswith('RunPlugin'):
        path = function.replace('RunPlugin(', '').rstrip('")')
        run_plugin(path, wait=False)

    elif function.startswith('Skin.SetString'):
        key, value = function.replace('Skin.SetString(', '').rstrip(')').split(',')
        INFO_LABELS['Skin.String({})'.format(key)] = value

def translatePath(path):
    translates = {
        'special://home/': kodi_home,
        'special://temp/': tmp_dir,
        'special://userdata/addon_data/': addons_data,
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

ABORTED = False
def Montor_waitForAbort(self, timeout=0):
    global ABORTED
    log("Wait for Abort: {}".format(timeout))

    try:
        for i in range(timeout):
            if ABORTED:
                break
            time.sleep(1)
    except:
        ABORTED = True

    return ABORTED

def Montor_abortRequested(self):
    return ABORTED

def executeJSONRPC(json_string):
    log('JSON RPC Request: {}'.format(json_string))

    request = json.loads(json_string)
    result = {}

    if request['method'] == 'Addons.GetAddons':
        addons = _get_installed_addons()
        rows = [{'addonid': addon} for addon in addons]
        result = {'result': {'addons': rows}}

    return json.dumps(result)

xbmc.log = log
xbmc.getInfoLabel = getInfoLabel
xbmc.executebuiltin = executebuiltin
xbmc.getCondVisibility = getCondVisibility
xbmc.Player.play = Player_play
xbmc.Monitor.waitForAbort = Montor_waitForAbort
xbmc.Monitor.abortRequested = Montor_abortRequested
xbmc.getLanguage = getLanguage
xbmc.executeJSONRPC = executeJSONRPC
xbmcvfs.translatePath = xbmc.translatePath = translatePath

## xbmcaddon ##

def Addon_init(self, id=None):
    if not id:
        id = urlsplit(sys.argv[0]).netloc

    self._info = {
        'id': id,
        'name': id,
        'path': os.path.join(addons_dir, id),
        'profile': os.path.join(addons_data, id),
        'version': '100.0.0',
        'fanart': 'fanart.jpg',
        'icon': 'icon.png',
    }

    # simulate pre-multi-instance
    if id == 'pvr.iptvsimple':
        self._info['version'] = '19.0.0'

    self._settings = {}
    self._strings  = {}

    self._settings_defaults = {
        'live_play_type': '1', #From live
        'default_quality': '1', #Best (requires proxy to be running)
        'persist_cache': 'false',
        'use_ia_hls_live': 'false',
        'use_ia_hls_vod': 'false',
        'verify_ssl': 'false',
        '_proxy_path': '', #start with: proxy.py "plugin://script.module.slyguy" service
    }

    addon_xml_path = os.path.join(self._info['path'], 'addon.xml')
    settings_path = os.path.join(self._info['path'], 'resources', 'settings.xml')
    po_path = os.path.join(self._info['path'], 'resources', 'language', 'resource.language.en_gb', 'strings.po')
    settings_json_path = os.path.join(self._info['profile'], 'settings.json')

    if not os.path.exists(addon_xml_path):
        log("WARNING: Missing {}".format(addon_xml_path))
    else:
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()
        for key in root.attrib:
            self._info[key] = root.attrib[key]

    if os.path.exists(settings_path):
        tree = ET.parse(settings_path)
        for elem in tree.findall('*/setting'):
            if 'id' in elem.attrib:
                self._settings[elem.attrib['id']] = self._settings_defaults.get(elem.attrib['id'], elem.attrib.get('default', ''))

    if not os.path.exists(po_path):
        log("WARNING: Missing {}".format(po_path))
    else:
        try:
            po = polib.pofile(po_path)
            for entry in po:
                index = int(entry.msgctxt.lstrip('#'))
                self._strings[index] = entry.msgid
        except:
            log("WARNING: Failed to parse PO File: {}".format(po_path))

    settings_json_path = os.path.join(self._info['profile'], 'settings.json')
    if os.path.exists(settings_json_path):
        try:
            with open(os.path.join(self._info['profile'], 'settings.json'), 'rb') as f:
                self._settings.update(json.load(f))
        except:
            print("Failed to loat settings.json")

    if not os.path.exists(self._info['profile']):
        os.makedirs(self._info['profile'])

    with open(os.path.join(self._info['profile'], 'settings.json'), 'w', encoding='utf-8') as f:
        json.dump(self._settings, f, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)

def Addon_getLocalizedString(self, id):
    return self._strings.get(id, '')

def Addon_openSettings(self):
    _print("OPEN SETTINGS!")
    _print(self._settings)
    #do settings dialog here!

def Addon_getSetting(self, id):
    return str(self._settings.get(id, ""))

def Addon_setSetting(self, id, value):
    self._settings[str(id)] = str(value)

    if not os.path.exists(self._info['profile']):
        os.makedirs(self._info['profile'])

    time.sleep(0.01)

    with open(os.path.join(self._info['profile'], 'settings.json'), 'w', encoding='utf-8') as f:
        json.dump(self._settings, f, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)

def Addon_getAddonInfo(self, id):
    return self._info.get(id, "")

xbmcaddon.Addon.__init__ = Addon_init
xbmcaddon.Addon.getLocalizedString = Addon_getLocalizedString
xbmcaddon.Addon.openSettings = Addon_openSettings
xbmcaddon.Addon.getSetting = Addon_getSetting
xbmcaddon.Addon.setSetting = Addon_setSetting
xbmcaddon.Addon.getAddonInfo = Addon_getAddonInfo

## xbmcgui ##

def get_input(text, default=''):
    if SETTINGS['interactive']:
        return input(text)
    else:
        _print(text)
        return default

def _print(text):
    print(text, file=sys.stderr)

    # if SETTINGS['interactive'] or SETTINGS['debug']:
    #     print(text)

def Dialog_yesno(self, heading, line1, line2="", line3="", nolabel="No", yeslabel="Yes", autoclose=0):
    _print("{}\n{} {} {}\n0: {}\n1: {}".format(heading, line1, line2, line3, nolabel, yeslabel))
    return int(get_input('Select: ', '0').strip()) == 1

def Dialog_ok(self, heading, line1, line2="", line3=""):
    get_input('\n{}\n {} {} {} [OK]'.format(heading, line1, line2, line3))

def Dialog_textviewer(self, heading, message):
    get_input('\n{}\n {} [OK]'.format(heading, message))

def Dialog_notification(self, heading, message, icon="", time=0, sound=True):
    _func_print('Notification', locals())

def Dialog_select(self, heading, list, autoclose=0, preselect=-1, useDetails=False):
    _print('-1: Cancel')

    for idx, item in enumerate(list):
        try:
            label = item.getLabel()
        except:
            label = item

        _print('{}: {}'.format(idx, label))

    return int(get_input('{}: '.format(heading), preselect))

def Dialog_input(self, heading, defaultt="", type=0, option=0, autoclose=0):
    return get_input('{0} ({1}): '.format(heading, defaultt)).strip() or defaultt

def DialogProgress_create(self, heading, line1="", line2="", line3=""):
    _print('{}\n{} {} {}'.format(heading, line1, line2, line3))

def Dialog_browseSingle(self, type, heading, shares, mask='', useThumbs=False, treatAsFolder=False, defaultt=''):
    return get_input('{0} ({1}): '.format(heading, defaultt)).strip() or defaultt

def ListItem_init(self, label="", label2="", iconImage="", thumbnailImage="", path="", offscreen=False):
    self._data = defaultdict(dict)
    _locals = locals()
    _locals.pop('self')
    self._data.update(_locals)

def ListItem_setLabel(self, label):
    self._data['label'] = label

def ListItem_getLabel(self):
    return self._data.get('label', '')

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

def ListItem_getProperty(self, key):
    return self._data['property'].get(key, '')

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
    self._window_path = os.path.join(tmp_dir, 'window-{}.json'.format(self._window_id))

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

xbmcgui.Dialog.yesno = Dialog_yesno
xbmcgui.Dialog.ok = Dialog_ok
xbmcgui.Dialog.textviewer = Dialog_textviewer
xbmcgui.Dialog.notification = Dialog_notification
xbmcgui.Dialog.input = Dialog_input
xbmcgui.DialogProgress.create = DialogProgress_create
xbmcgui.DialogProgress.iscanceled = lambda self:False
xbmcgui.Dialog.select = Dialog_select
xbmcgui.Dialog.browseSingle = Dialog_browseSingle

xbmcgui.ListItem.__init__ = ListItem_init
xbmcgui.ListItem.setLabel = ListItem_setLabel
xbmcgui.ListItem.getLabel = ListItem_getLabel
xbmcgui.ListItem.setArt = ListItem_setArt
xbmcgui.ListItem.setInfo = ListItem_setInfo
xbmcgui.ListItem.addStreamInfo = ListItem_addStreamInfo
xbmcgui.ListItem.addContextMenuItems = ListItem_addContextMenuItems
xbmcgui.ListItem.setProperty = ListItem_setProperty
xbmcgui.ListItem.getProperty = ListItem_getProperty
xbmcgui.ListItem.setPath = ListItem_setPath
xbmcgui.ListItem.getPath = ListItem_getPath
xbmcgui.ListItem.__str__ = ListItem_str
xbmcgui.ListItem.__repr__ = ListItem_repr

xbmcgui.Window.__init__ = Window_init
xbmcgui.Window.getProperty = Window_getProperty
xbmcgui.Window.setProperty = Window_setProperty
xbmcgui.Window.clearProperty = Window_clearProperty
xbmcgui.Window.save = Window_save

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
    global DATA, last_path, next_path

    if SETTINGS['proxy_type'] == KODI:
        for item in DATA['items']:
            print(item[0])

        return

    elif SETTINGS['proxy_type'] == TV_GRAB:
        for item in DATA['items']:
            print(unquote_plus(item[0]))
        sys.exit(200)

    if not succeeded:
        return

    if SETTINGS['debug']:
        _print('Title: {category}\nContent: {content}'.format(**DATA))

    if last_path:
        DATA['items'].insert(0, [last_path, xbmcgui.ListItem(label='BACK')])

    FORMAT_TAGS = ['B', 'COLOR']
    for idx, item in enumerate(DATA['items']):
        label = item[1].getLabel()
        for tag in FORMAT_TAGS:
            label = re.sub(r'\[/?{}.*?]'.format(tag), '', label)

        _print("{}: {}".format(idx, label))

    index = int(get_input('\nSelect: ', -1))
    if index >= 0:
        selected = DATA['items'][index]
        url = selected[0]
        DATA = _init_data()
        next_path = url

def setResolvedUrl(handle, succeeded, listitem):
    log("Resolved: {0}".format(listitem))

    if SETTINGS['proxy_type'] == TVHEADEND:
        output_tvh(listitem)
    elif SETTINGS['proxy_type'] == HTTP:
        output_http(listitem)
    elif SETTINGS['proxy_type'] == TV_GRAB:
        output_tv_grab(listitem)
    else:
        output_shell(listitem)

def output_tv_grab(listitem):
    print(listitem.getPath())
    sys.exit(200)

def output_http(listitem):
    raise Exception('Replace me!')

def output_shell(listitem):
    path = listitem.getPath()

    if '|' in path:
        url, headers = path.split('|')
    else:
        url, headers = path, ''

    _print('URL: {}'.format(url))
    _print('Headers: {}'.format(headers))

def output_tvh(listitem):
    path = listitem.getPath()
    name = listitem.getLabel().strip()

    def escape(value):
        return value.replace('"', r'\"')

    if '|' in path:
        url, headers = path.split('|')
        _headers = parse_qsl(headers)
        headers = ' -headers "'
        for pair in _headers:
            headers += '{key}: {value}\r\n'.format(key=escape(pair[0]), value=escape(pair[1]))
        headers += '"'
    else:
        url, headers = path, ''

    seek = listitem.getProperty('ResumeTime')
    if seek:
        seek = ' -ss {}'.format(seek)

    if name:
        name = ' -metadata service_name="{}"'.format(escape(name))

    print('-loglevel fatal -probesize 10M -analyzeduration 0 -fpsprobesize 0{headers}{seek} -i "{url}"{name}'.format(headers=headers, seek=seek, url=url, name=name))
    sys.exit(200)

def addSortMethod(handle, sortMethod, label2Mask=""):
    global DATA
    DATA['sort'].append(sortMethod)

def setContent(handle, content):
    global DATA
    DATA['content'] = content

def setPluginCategory(handle, category):
    global DATA
    DATA['category'] = category

def platform_system():
    return 'kodi.proxy'

platform.system = platform_system
xbmcplugin.addDirectoryItem = addDirectoryItem
xbmcplugin.addDirectoryItems = addDirectoryItems
xbmcplugin.endOfDirectory = endOfDirectory
xbmcplugin.setResolvedUrl = setResolvedUrl
xbmcplugin.addSortMethod = addSortMethod
xbmcplugin.setContent = setContent
xbmcplugin.setPluginCategory = setPluginCategory

## xbmcvfs ##

def exists(path):
    return os.path.exists(path)

def mkdir(path):
    return os.mkdir(path)

def mkdirs(path):
    return os.makedirs(path, exist_ok=True)

def delete(file):
    return os.remove(file)

def copy(src, dst):
    return shutil.copy(src, dst)

def listdir(path):
    if path.startswith('plugin://'):
        output = run_plugin(unquote_plus(path))
        return [], [x for x in output if x]
    else:
        return [], os.listdir(path)

xbmcvfs.exists = exists
xbmcvfs.copy = copy
xbmcvfs.mkdir = mkdir
xbmcvfs.mkdirs = mkdirs
xbmcvfs.delete = delete
xbmcvfs.listdir = listdir

if __name__ == "__main__":
    try:
        menu(get_argv(1, ''), get_argv(2, 'default'))
    except ProxyException as e:
        print(str(e))
