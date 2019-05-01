from time import time

from matthuisman import userdata, settings
from matthuisman.session import Session
from matthuisman.exceptions import Error

from .constants import HEADERS, CLIENTID
from .language import _

class APIError(Error):
    pass

class API(object):
    def new_session(self):
        self.logged_in = False

        self._session = Session(HEADERS)
        self._set_authentication()
        
        settings.setBool('_logged_in', self.logged_in)

    def _set_authentication(self):
        access_token = userdata.get('access_token')
        if not access_token:
            return

        self._session.headers.update({'authorization': 'Bearer {}'.format(access_token)})
        self.logged_in = True

    def _oauth_token(self, data):
        token_data = self._session.post('https://auth.kayosports.com.au/oauth/token', json=data).json()
        if 'error' in token_data:
            raise APIError(_(_.LOGIN_ERROR, msg=token_data.get('error_description')))

        userdata.set('access_token', token_data['access_token'])
        userdata.set('expires', int(time() + token_data['expires_in'] - 15))

        if 'refresh_token' in token_data:
            userdata.set('refresh_token', token_data['refresh_token'])

        self._set_authentication()

    def _refresh_token(self):
        if userdata.get('expires', 0) > time():
            return

        payload = {
            "refresh_token": userdata.get('refresh_token'),
            "grant_type": "refresh_token",
            "client_id": CLIENTID,
        }

        self._oauth_token(payload)

    def login(self, username, password):
        payload = {
            "audience": "kayosports.com.au",
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "scope": "openid offline_access",
            "realm": "prod-martian-database",
            "client_id": CLIENTID,
            "username": username,
            "password": password,
        }

        self._oauth_token(payload)

    def profiles(self):
        self._refresh_token()
        return self._session.get('https://profileapi.kayosports.com.au/user/profile').json()

    def sport_menu(self):
        return self._session.get('https://resources.kayosports.com.au/production/sport-menu/lists/default.json').json()

    def cdn_selection(self, media_type):
        return self._session.get('https://cdnselectionserviceapi.kayosports.com.au/android/usecdn/mobile/{}'.format(media_type)).json().get('useCDN')

    #landing has heros and panels
    def landing(self, name, **kwargs):
        params = {
            'evaluate': 99, 
            'resourcesEnv': 'production',
            'chromecastEnv': 'production',
            'statsEnv': 'production',
        }

        params.update(**kwargs)

        return self._session.get('https://vccapi.kayosports.com.au/content/types/landing/names/{}'.format(name), params=params).json()

    #panel has shows and episodes
    def panel(self, id, **kwargs):
        params = {
            'evaluate': 3, 
        }

        params.update(**kwargs)

        return self._session.get('https://vccapi.kayosports.com.au/content/types/carousel/keys/{}'.format(id), params=params).json()[0]

    #show has episodes and panels
    def show(self, show_id, season_id=None, **kwargs):
        params = {
            'evaluate': 3,
            'showCategory': show_id,
            'seasonCategory': season_id,
        }

        params.update(**kwargs)

        return self._session.get('https://vccapi.kayosports.com.au/content/types/landing/names/show', params=params).json()

    def event(self, id, **kwargs):
        params = {
            'evaluate': 3,
            'event': id,
        }

        params.update(**kwargs)

        return self._session.get('https://vccapi.kayosports.com.au/content/types/landing/names/event', params=params).json()[0]['contents'][0]['data']['asset']

    def stream(self, asset):
        self._refresh_token()

        params = {
            'fields': 'alternativeStreams',
        }

        data = self._session.post('https://vmndplay.kayosports.com.au/api/v1/asset/{}/play'.format(asset), params=params, json={}).json()
        if 'errors' in data:
            raise APIError(_(_.ASSET_ERROR, msg=data['errors'][0]['detail']))

        return data['data'][0]

    def logout(self):
        userdata.delete('access_token')
        userdata.delete('refresh_token')
        userdata.delete('expires')
        userdata.delete('profile')
        self.new_session()