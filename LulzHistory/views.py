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

import json, base64

from flask import render_template, session
from flask.ext import restful
import requests

from werkzeug.contrib.cache import SimpleCache

from . import app
from .auth import github, require_github


cache = SimpleCache()


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


@app.route('/repo/')
@app.route('/repo/<owner>/')
@require_github
def repo_index(owner=None, repo=None, branch=None):

    if repo is None:
        ## List repositories (optionally filtering on owner)
        return list_repositories(owner)

    if branch is None:
        branch = 'master'  # todo: use repo default instead

    ## Now return a view showing this repo history, with lulz
    pass


def list_repositories(owner=None):
    """
    List repositories for a given user/organization
    """

    ## todo: fetch repos for organizations too..

    if owner is None:
        title = "Your repositories"
        url = '/user/repos?sort=updated&direction=desc'

    else:
        title = "Repositories for {}".format(owner)
        url = '/users/{}/repos?sort=updated&direction=desc'.format(owner)

    auth = github.get_session(token=session['token'])
    repos = dig_down_merge(auth.get, url)
    return render_template("repos-index.html", repos=repos, title=title)


@app.route('/repo/<owner>/<repo>/')
@app.route('/repo/<owner>/<repo>/<branch>/')
@require_github
def lulz_history(owner=None, repo=None, branch=None):
    """
    Show the lulz'd history for a given repository/branch
    """
    if branch is None:
        branch = 'master'
    auth = github.get_session(token=session['token'])

    commits_cache_key = 'commits/{}/{}/{}'.format(owner, repo, branch)
    branches_cache_key = 'branches/{}/{}'.format(owner, repo)

    ## todo: figure out how to get commits for a specific branch!
    commits = cache.get(commits_cache_key)
    if commits is None:
        commits = dig_down_merge(
            auth.get,
            '/repos/{owner}/{repo}/commits?ref={branch}'.format(
                owner=owner, repo=repo, branch=branch))
        cache.set(commits_cache_key, commits, timeout=120)

    branches = cache.get(branches_cache_key)
    if branches is None:
        branches = dig_down_merge(
            auth.get, '/repos/{}/{}/branches'.format(owner, repo))
        cache.set(branches_cache_key, branches, timeout=120)

    return render_template(
        'lulz-history.html',
        commits=commits,
        repo_name="{}/{}".format(owner, repo),
        current_branch=branch)
