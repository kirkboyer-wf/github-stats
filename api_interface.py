# Funcs/classes for interfacing with (the pyGithub wrapper for) the Github API

# built-in modules
from datetime import datetime
import pickle

# third-party modules
import github
from github.GithubException import RateLimitExceededException
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


def update_all_data():
    ndb.Key(models.LastUpdate, 'last_update').delete()
    make_task(purpose='get_repos', obj=_github_object())


def update_data():
    make_task(purpose='get_repos', obj=_github_object())
    models.LastUpdate.get_or_insert('last_update')


def _last_update():
    update = models.LastUpdate.get_by_id('last_update')
    if not update:
        return datetime.fromtimestamp(0)
    return update


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
    """Get all the forks of a repo, then start the next step for that repo
    and all the retrieved forks."""
    _make_tasks_from_list(repo.get_forks(), 'get_pulls')

    make_task(purpose='get_pulls',
              obj=repo)


def _get_pulls(repo):
    """Get all pulls from a given repo, then start tasks to get info from them.
    """
    _make_tasks_from_list(
        repo.get_pulls(
            since=_last_update().timestamp
        ),
        'get_comments')


def _make_datastore_comment(pull, comment):
    datastore_comment = models.Comment(
        github_id=comment.id,
        pull_request_id=pull.id,
        repo=pull.base.repo.name,
        author=comment.user.name,
        body=comment.body)
    datastore_comment.put_async()


def _get_comments(pull):
    """Get all comments from a pull, then store them along with the pull
    request's body (i.e. the first comment in its issues thread) on the
    datastore."""
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
        except RateLimitExceededException:
            make_task(
                purpose=purpose,
                params={
                    'purpose': purpose,
                    'object': pickle.dumps(obj),
                },
                delay=_rate_reset_wait())
