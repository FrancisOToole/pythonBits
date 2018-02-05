# -*- coding: utf-8 -*-

import requests
import contextlib
import re

from . import __version__ as version
from .config import config

class TrackerException(Exception):
    pass

#todo: get domain from announce_url
class Tracker():
    headers={'User-Agent': 'pythonBits/{}'.format(version)}
    
    @staticmethod
    def logged_in(resp):
        if ("Log in!" in resp.text or "href=\"login.php\"" in resp.text):
            return False
        if ("logout.php" in resp.text):
            return True
        
        print resp.text
        raise TrackerException('Unknown response format')
    
    @contextlib.contextmanager
    def login(self):
        domain = config.get('Tracker','domain')
        login_url = "https://{}/login.php".format(domain)
        
        username = config.get('Tracker', 'username', ask_to_save=True)
        password = config.get('Tracker', 'password', ask_to_save=True, 
                              use_getpass=True)

        payload = {'username': username,
                   'password': password,
                   'keep_logged': "1",
                   'login': "Log in!"}

        with requests.Session() as s:
            s.headers.update(self.headers)
            
            print "Logging in", username, "to", domain
            resp = s.post(login_url, data=payload)
            resp.raise_for_status()
            
            # alternatively check for redirects via resp.history
            if not self.logged_in(resp):
                raise TrackerException("Log-in failed!")
            logout_re = "logout\.php\?auth=[0-9a-f]{32}"
            m = re.search(logout_re, resp.text)
            
            logout_url = "https://{}/{}".format(domain, m.group(0))
            
            
            yield s
            
            
            resp = s.get(logout_url)
            if self.logged_in(resp):
                raise TrackerException("Log-out failed!")
            print "Logged out", username
            

    def upload(self, **kwargs):
        url = "https://{}/upload.php".format(config.get('Tracker','domain'))
        with self.login() as session:
            
            resp = session.post(url, **kwargs)
            resp.raise_for_status()
            
            
            print resp.history
            if resp.history:
                print 'submission succeeded(?)'
                #todo get url from redirect
                return 'uploaded_url'
            else:
                print 'resp', resp
                print 'search', ("No torrent file uploaded" in resp.text)
                
                raise TrackerException('Failed to upload submission')
            
            #check if submission failed
            pass