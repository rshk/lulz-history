##==============================================================================
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
##==============================================================================

"""
Views
"""

import base64
import json
import urllib

from flask import render_template, session
from flask.ext import restful
import requests
from werkzeug.contrib.cache import SimpleCache

from . import app
from .github import request
from .auth import github, require_github


cache = SimpleCache(default_timeout=120)


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

    ## Retrieve commits history
    commits_cache_key = '/repos/{owner}/{repo}/commits?sha={branch}'.format(
        owner=owner, repo=repo, branch=branch)
    data = cache.get(commits_cache_key)
    if data is not None:
        commits = data
    else:
        url = '/repos/{owner}/{repo}/commits'.format(
            owner=owner, repo=repo)
        params = {'per_page': 100}
        if branch is not None:
            args['sha'] = branch
        commits = list(request_all(url, params=params))
        cache.set(commits_cache_key, commits)

    ## Retrieve list of branches
    branches_cache_key = '/repos/{owner}/{repo}/branches'.format(
        owner=owner, repo=repo)
    data = cache.get(branches_cache_key)
    if data is not None:
        branches = data
    else:
        url = '/repos/{owner}/{repo}/branches'.format(owner=owner, repo=repo)
        branches = list(request_all(url))
        cache.set(branches_cache_key, branches)

    ## Retrieve list of available lulz pictures
    lulz_pics_cache_key = '/repos/{owner}/{repo}/contents?ref=lulz-pics'\
                          ''.format(owner=owner, repo=repo)
    data = cache.get(lulz_pics_cache_key)
    if data is not None:
        lulz_pics = data
    else:
        url = '/repos/{owner}/{repo}/contents?ref=lulz-pics'\
              ''.format(owner=owner, repo=repo)
        lulz_pics = list(request_all(url))
        cache.set(lulz_pics_cache_key, lulz_pics)

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
