import requests

from . import userdata, settings
from .log import log
from .constants import SESSION_TIMEOUT, SESSION_ATTEMPTS, SESSION_CHUNKSIZE

class Session(requests.Session):
    def __init__(self, headers=None, cookies_key=None, base_url='{}', timeout=None, attempts=None):
        super(Session, self).__init__()

        self._headers     = headers or {}
        self._cookies_key = cookies_key
        self._base_url    = base_url
        self._timeout     = timeout or SESSION_TIMEOUT
        self._attempts    = attempts or SESSION_ATTEMPTS
        self._verify      = settings.getBool('verify_ssl', True)

        self.headers.update(self._headers)
        if self._cookies_key:
            self.cookies.update(userdata.get(self._cookies_key, {}))

    def request(self, method, url, timeout=None, attempts=None, verify=None, **kwargs):
        if not url.startswith('http'):
            url = self._base_url.format(url)

        kwargs['timeout'] = timeout or self._timeout
        kwargs['verify'] = verify or self._verify
        attempts = attempts or self._attempts

        for i in range(1, attempts+1):
            log('Attempt {}/{}: {} {} {}'.format(i, attempts, method, url, kwargs if method.lower() != 'post' else ""))

            try:
                return super(Session, self).request(method, url, **kwargs)
            except:
                if i == attempts:
                    raise

    def save_cookies(self):
        if not self._cookies_key:
            raise Exception('A cookies key needs to be set to save cookies')

        userdata.set(self._cookies_key, self.cookies.get_dict())

    def clear_cookies(self):
        if self._cookies_key:
            userdata.delete(self._cookies_key)
        self.cookies.clear()

    def chunked_dl(self, url, dst_path, method='GET'):
        resp = self.request(method, url, stream=True)
        resp.raise_for_status()

        with open(dst_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)