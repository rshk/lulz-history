##=============================================================================
## Copyright 2013 Samuele Santi
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##=============================================================================

"""
Views
"""

import base64
import json
import urllib
from functools import wraps

from flask import render_template, session, request
from werkzeug.contrib.cache import SimpleCache

from . import app
from .github import request
from .auth import github


cache = SimpleCache(default_timeout=120)


def cached(timeout=5 * 60, key=None):
    """Decorator for caching function return values"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(key, '__call__'):
                cache_key = key(*args, **kwargs)
            elif key is not None:
                cache_key = key
            else:
                ## todo: generate from args/kwargs?
                raise ValueError("Unspecified cache key")
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


@app.context_processor
def add_user_info():
    user = cache.get('user_profile')
    if user is None:
        try:
            auth = github.get_session(token=session['token'])
            resp = auth.get('user')
            if not resp.ok:
                raise Exception("Request failed")
            user = resp.json()
            user['authenticated'] = True
        except:
            user = {'authenticated': False}
        cache.set('user_profile', user, timeout=120)
    return dict(user=user)


@app.route("/")
def index():
    return render_template("index.html")


def dig_down_request(do_req, url):
    """
    Continue following the "next" link in order to retrieve
    **all** the results from a paginated request.
    """
    while True:
        resp = do_req(url)
        yield resp

        if 'next' in resp.links:
            url = resp.links['next']['url']
        else:
            return  # Nothing to see here..


def dig_down_merge(do_req, url):
    results = []
    for resp in dig_down_request(do_req, url):
        if not resp.ok:
            raise Exception("Request failure (code: {})".format(resp.status_code))
        results.extend(resp.json())
    return results


def request_all(url, params=None):
    response = request('GET', url, params=params)
    for item in response.json():
        yield item
    while 'next' in response.links:
        response = request('GET', response.links['next']['url'])
        for item in response.json():
            yield item


@app.route('/repo/<owner>/')
def repo_index(owner):
    title = u"Repositories for {}".format(owner)
    url = '/users/{}/repos'.format(owner)
    params = {
        'sort': 'updated',
        'direction': 'desc',
    }
    cache_key = '/users/{}/repos'.format(owner)
    data = cache.get(cache_key)
    if data:
        repos = data
    else:
        repos = list(request_all(url, params=params))
        cache.set(cache_key, repos)
    return render_template("repos-index.html", repos=repos, title=title)


@app.route('/repo/<owner>/<repo>/')
@app.route('/repo/<owner>/<repo>/<branch>/')
def lulz_history(owner=None, repo=None, branch=None):
    """
    Show the lulz'd history for a given repository/branch
    """

    @cached(5*60, '/repos/{owner}/{repo}/commits?sha={branch}')
    def get_commits(owner, repo, branch):
        url = '/repos/{owner}/{repo}/commits'.format(
            owner=owner, repo=repo)

        ## todo: we need to paginate, as commits can be quite a lot..
        ## (right now we're only showing 100 commits..)
        params = {'per_page': 100}

        if branch is not None:
            params['sha'] = branch

        return request('GET', url, params=params).json()

    commits = get_commits(owner=owner, repo=repo, branch=branch)

    @cached(5*60, '/repos/{owner}/{repo}/branches')
    def list_branches(owner, repo):
        url = '/repos/{owner}/{repo}/branches'.format(owner=owner, repo=repo)
        return list(request_all(url))

    branches = list_branches(owner=owner, repo=repo)

    ## todo: we should look for pics in the committer's repo
    ## named "lulz-pics", master branch, all subfolders..

    @cached(5*60, '/repos/{owner}/{repo}/contents?ref=lulz-pics')
    def get_lulz_pics(owner, repo):
        url = '/repos/{owner}/{repo}/contents?ref=lulz-pics'\
              ''.format(owner=owner, repo=repo)
        return list(request_all(url))

    lulz_pics = get_lulz_pics(owner=owner, repo=repo)

    lulz_pics_dict = {}
    for pic in lulz_pics:
        if pic['type'] == 'file':
            #lulz_pics_dict[pic['name']] = pic['html_url']
            lulz_pics_dict[pic['name']] = \
                "https://raw.github.com/{owner}/{repo}/lulz-pics/{pic}".format(
                    owner=owner, repo=repo, pic=pic['name'])

    for commit in commits:
        sha_short = commit['sha'][:11]
        pic_name = '{}.jpg'.format(sha_short)
        if pic_name in lulz_pics_dict:
            commit['pic'] = lulz_pics_dict[pic_name]
            commit['is_lulz'] = True
        else:
            commit['pic'] = commit['author']['avatar_url']
            commit['is_lulz'] = False

    return render_template(
        'lulz-history.html',
        commits=commits,
        repo_name="{}/{}".format(owner, repo),
        current_branch=branch)
