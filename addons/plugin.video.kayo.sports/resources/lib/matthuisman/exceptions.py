
class Error(Exception):
    pass

class InputStreamError(Error):
    pass

class PluginError(Error):
    pass

class GUIError(Error):
    pass

class RouterError(Error):
    pass