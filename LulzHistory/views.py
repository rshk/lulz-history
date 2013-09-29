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

from functools import partial
import re

from flask import render_template, session, request, redirect, url_for
from werkzeug.contrib.cache import SimpleCache

from . import app
from . import github
from .const import PICS_REPO_NAME
from .github import HTTPError
from .utils import cached as cached_decorator


## Caching-related stuff
cache = SimpleCache(default_timeout=120)
cached = partial(cached_decorator, cache)

## Regexp for image files.
## We pre compile and keep it there in order to
## be able to unit-test it, not for performance reasons..
img_file_re = re.compile(r'^[0-9a-f]{10,40}\.(jpg|gif|png)$')


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
            raise Exception(
                "Request failure (code: {})".format(resp.status_code))
        results.extend(resp.json())
    return results


def request_all(url, params=None):
    response = github.request('GET', url, params=params)
    for item in response.json():
        yield item
    while 'next' in response.links:
        response = github.request('GET', response.links['next']['url'])
        for item in response.json():
            yield item


@app.route('/goto')
def goto():
    repo = request.args['repo'].split('/')
    if len(repo) != 2:
        return ("Bad repo name", 400)
    return redirect(url_for('lulz_history', owner=repo[0], repo=repo[1]))


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


@cached(5*60, '/repos/{owner}/{repo}/commits?sha={branch}')
def get_commits(owner, repo, branch):
    url = '/repos/{owner}/{repo}/commits'.format(
        owner=owner, repo=repo)

    ## todo: we need to paginate, as commits can be quite a lot..
    ## (right now we're only showing 100 commits..)
    params = {'per_page': 100}

    if branch is not None:
        params['sha'] = branch

    return github.request('GET', url, params=params).json()

@cached(5*60, '/repos/{owner}/{repo}/branches')
def list_branches(owner, repo):
    url = '/repos/{owner}/{repo}/branches'.format(owner=owner, repo=repo)
    return list(request_all(url))

## todo: we should look for pics in the committer's repo
## named "lulz-pics", master branch, all subfolders..

# @cached(5*60, '/repos/{owner}/{repo}/contents?ref=lulz-pics')
# def get_lulz_pics(owner, repo):
#     url = '/repos/{owner}/{repo}/contents?ref=lulz-pics'\
#           ''.format(owner=owner, repo=repo)
#     return list(request_all(url))

@cached(10*60, 'repo_master_branch:{owner}/{repo}')
def get_repo_default_branch(owner, repo):
    return 'master'
    # resp = github.request('GET', '/repos/{owner}/{repo}'\
    #                       ''.format(owner=owner, repo=repo))
    # return resp.json()['master_branch']


@cached(5*60, 'repo_pics:{owner}/{repo}')
def get_repo_pics(owner, repo):
    """
    Scan a repository and find all the pictures in sub-directories.
    Returns a dictionary with ``{'commit_sha': 'picture_url'}``
    """
    branch = get_repo_default_branch(owner=owner, repo=repo)
    found = {}

    def scan_subtree(url):
        resp = github.request('GET', url)
        for item in resp.json():
            if item['type'] == 'dir':
                scan_subtree(item['url'])
            elif item['type'] == 'file':
                ## Is this a suitable picture?
                if img_file_re.match(item['name']):
                    sha = item['name'].split('.', 1)[0]
                    file_url = '{base}/{owner}/{repo}/{branch}/{path}'\
                               ''.format(
                                   base='https://raw.github.com',
                                   owner=owner,
                                   repo=repo,
                                   branch=branch,
                                   path=item['path'])
                    found[sha] = file_url
    try:
        scan_subtree('/repos/{owner}/{repo}/contents'
                     ''.format(owner=owner, repo=repo))
    except HTTPError:
        pass  # Will return stuff found so far
        ## todo: should we raise exceptions in case of failure?

    return found


@app.route('/repo/<owner>/<repo>/')
@app.route('/repo/<owner>/<repo>/<branch>/')
def lulz_history(owner=None, repo=None, branch=None):
    """
    Show the lulz'd history for a given repository/branch
    """

    commits = get_commits(owner=owner, repo=repo, branch=branch)
    authors = set(c['author']['login'] for c in commits if c['author'])
    branches = list_branches(owner=owner, repo=repo)
    all_pics = {}

    for author in authors:
        all_pics[author] = get_repo_pics(
            owner=author,
            repo=PICS_REPO_NAME)

    def find_pic(pics, commit):
        for key, val in pics.iteritems():
            if commit.startswith(key):
                return val

    for commit in commits:
        pic = find_pic(all_pics[commit['author']['login']], commit['sha'])

        if pic is not None:
            commit['pic'] = pic
            commit['is_lulz'] = True

        else:
            commit['pic'] = commit['author']['avatar_url']
            commit['is_lulz'] = False

    return render_template(
        'lulz-history.html',
        commits=commits,
        repo_name="{0}/{1}".format(owner, repo),
        current_branch=branch,
        branches=branches)
