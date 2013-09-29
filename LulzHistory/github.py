"""
Wrapper around requests.

The purpose of this module is:

* Automatically adding authentication tokens
  to requests

* Providing facilities for retrieving results
  by "digging down" paged requests

* Adding caching support to requests, to prevent
  hitting rate limits
"""

import urlparse

import requests
from werkzeug.contrib.cache import SimpleCache

from . import app


CLIENT_ID = app.config['GITHUB_CLIENT_ID']
CLIENT_SECRET = app.config['GITHUB_CLIENT_SECRET']
cache = SimpleCache(default_timeout=600)
aggressive_cache = SimpleCache(default_timeout=60)


class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __repr__(self):
        return "<HTTPError {}: {}>".format(self.status_code, self.message)

    def __unicode__(self):
        return unicode(repr(self))

    def __str__(self):
        return str(repr(self))


def request(method, url, params=None, **kwargs):
    """
    Wrapper around ``requests.request()``, adding GitHub
    authentication (with app credentials).
    """
    url = urlparse.urljoin('https://api.github.com/', url)

    ## Add authentication information to query string
    if params is None:
        params = {}
    if isinstance(params, basestring):
        ## If params is bytes -> we need to split
        parsed = urlparse.parse_qs(params)
        #params = {k: v[0] for k, v in parsed.iteritems()}
        params = dict((k, v[0]) for k, v in parsed.iteritems())  # <2.7
    params['client_id'] = CLIENT_ID
    params['client_secret'] = CLIENT_SECRET

    response = requests.request(method, url, params=params, **kwargs)

    if not response.ok:
        try:
            err_msg = response.json()['message']
        except Exception:
            err_msg = response.text
        raise HTTPError(response.status_code, err_msg)

    return response
