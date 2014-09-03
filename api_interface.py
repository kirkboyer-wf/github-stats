# Funcs/classes for interfacing with (the pyGithub wrapper for) the Github API

# built-in modules
from datetime import datetime
import pickle

# third-party modules
import github
from github.GithubException import GithubException
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
import jinja2
import os
import webapp2

# project modules
import models
import settings


JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def fix_unicode(s):
    return s.encode('utf-8') if isinstance(s, unicode) else s


def update_all_data():
    ndb.Key(models.LastUpdate, 'last_update').delete()
    make_task(purpose='get_repos', obj=_github_object())


def update_data():
    make_task(purpose='get_repos', obj=_github_object())
    models.LastUpdate.get_or_insert('last_update')


def _last_update():
    update = models.LastUpdate.get_by_id('last_update')
    return update or datetime.fromtimestamp(0)


def _github_object():
    return github.Github(login_or_token=settings.AUTH_TOKEN)


def _rate_reset_wait():
    return (_github_object().get_rate_limit().rate.reset-datetime.now()).seconds


def make_task(purpose=None, obj=None, delay=None):
    taskqueue.add(
        url=settings.URLS[purpose],
        params={
            'purpose': purpose,
            'object': pickle.dumps(obj),
        },
        method='POST',
        countdown=delay)


def _make_tasks_from_list(_list, purpose):
    for i, obj in enumerate(list(_list)):
        make_task(purpose=purpose, obj=obj, delay=i)


def _get_repos(gh):
    org = gh.get_organization(settings.ORG_NAME)

    _make_tasks_from_list(org.get_repos(), 'get_forks')


def _get_forks(repo):
    _make_tasks_from_list(repo.get_forks(), 'get_pulls')

    make_task(purpose='get_pulls',
              obj=repo)


def _get_pulls(repo):
    _make_tasks_from_list(
        repo.get_pulls(
            since=_last_update().timestamp
        ),
        'get_comments')


def _make_datastore_comment(pull, comment):
    datastore_comment = models.Comment(
        github_id=comment.id,
        pull_request_id=pull.id,
        repo=fix_unicode(pull.base.repo.name),
        language=fix_unicode(pull.base.repo.language),
        author=fix_unicode("{0} ({1})".format(
            comment.user.name, comment.user.login)),
        body=fix_unicode(comment.body))
    datastore_comment.put()


def _get_comments(pull):
    comment_list = list(pull.get_comments())
    comment_list.extend(list(pull.get_issue_comments()))
    for comment in comment_list:
        _make_datastore_comment(pull, comment)

    _make_datastore_comment(pull, pull)


GET_FOR = {
    'get_repos': _get_repos,
    'get_forks': _get_forks,
    'get_pulls': _get_pulls,
    'get_comments': _get_comments,
}


class Get(webapp2.RequestHandler):
    def post(self):
        purpose = self.request.get('purpose')
        obj = pickle.loads(self.request.get('object'))
        try:
            GET_FOR[purpose](obj)
        except GithubException, e:
            if u'rate limit exceeded' in e.data[u'message']:
                make_task(
                    purpose=purpose,
                    params={
                        'purpose': purpose,
                        'object': pickle.dumps(obj),
                    },
                    delay=_rate_reset_wait())
