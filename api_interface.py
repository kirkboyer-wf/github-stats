# Funcs/classes for interfacing with (the pyGithub wrapper for) the Github API

# built-in modules
import datetime
import pickle

# third-party modules
import github
from github.GithubException import RateLimitExceededException
from google.appengine.api import taskqueue
import jinja2
import os
import webapp2

# project modules
import models
import settings


JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def update_data():
    make_task(purpose='get_repos')
    models.LastUpdate.get_or_insert('last_update')


def _last_update():
    update_key = models.LastUpdate.get_by_id('last_update')
    if not update_key:
        return datetime.datetime.fromtimestamp(0)
    return update_key.get()


def _github_object():
    return github.Github(login_or_token=settings.AUTH_TOKEN)


def _rate_reset():
    return _github_object().get_rate_limit().rate.reset


def make_task(purpose=None, obj=None, delay_until=None):
    wait_time = (delay_until-datetime.datetime.now()
                 ).seconds if delay_until else 0
    taskqueue.add(
        url=settings.URLS[purpose],
        params={
            'purpose': purpose,
            'object': pickle.dumps(obj) if obj else None,
        },
        method='POST',
        countdown=wait_time)


def _make_tasks_from_list(_list, purpose):
    for obj in list(_list):
        make_task(purpose=purpose,
                  obj=(pickle.dumps(obj) if obj else None))


def _get_repos():
    """Get the organization, then get all its repos and start tasks to get
    info from them."""
    gh = _github_object()
    org = gh.get_organization(settings.ORG_NAME)

    _make_tasks_from_list(org.get_repos(), 'get_forks')


def _get_forks(repo):
    """Get all the forks of a repo, then start the next step for that repo
    and all the retrieved forks."""
    _make_tasks_from_list(repo.get_forks(), 'get_pulls')

    make_task(purpose='get_pulls',
              obj=(pickle.dumps(repo) if repo else None))


def _get_pulls(repo):
    """Get all pulls from a given repo, then start tasks to get info from them.
    """
    _make_tasks_from_list(
        repo.get_pulls(
            since=_last_update()
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
        obj = (pickle.loads(self.request.get('object'))
               if purpose != 'get_repos' else None)
        try:
            GET_FOR[purpose](obj)
        except RateLimitExceededException:
            make_task(
                purpose=purpose,
                params={
                    'purpose': purpose,
                    'object': pickle.dumps(obj) if obj else None,
                },
                delay_until=_rate_reset())
