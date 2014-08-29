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


def update_data(after=None):
    make_task(purpose='get_repos',
              params={'after': after},
              method='POST')


def _github_object():
    return github.Github(login_or_token=settings.AUTH_TOKEN)


def _rate_reset():
    return _github_object().get_rate_limit().rate.reset


def make_task(purpose=None, payload=None, delay_until=None):
    wait_time = (delay_until-datetime.datetime.now()
                 ).seconds if delay_until else 0
    taskqueue.add(url=settings.URLS[purpose],
                  payload=pickle.dumps(payload),
                  method='POST',
                  countdown=wait_time)


def _get_repos():
    """Get the organization, then get all its repos and start tasks to get
    info from them."""
    try:
        gh = _github_object()
        org = gh.get_organization(settings.ORG_NAME)

        repo_list = list(org.get_repos())
        for repo in repo_list:
            make_task(purpose='get_forks',
                      payload=repo)

    except RateLimitExceededException:
        make_task(purpose='get_org',
                  delay_until=_rate_reset())


class GetRepos(webapp2.RequestHandler):
    def get():
        _get_repos()

    def post():
        _get_repos()


def _get_forks(repo):
    """Get all the forks of a repo, then start the next step for that repo
    and all the retrieved forks."""
    try:
        forks_list = list(repo.get_forks())
        for fork in forks_list:
            make_task(purpose='get_pulls',
                      payload=fork)
        make_task(purpose='get_pulls',
                  payload=repo)

    except RateLimitExceededException:
        make_task(purpose='get_forks',
                  payload=repo,
                  delay_until=_rate_reset())


class GetForks(webapp2.RequestHandler):
    def get(self):
        repo = pickle.loads(self.request.body)
        _get_forks(repo)

    def post(self):
        repo = pickle.loads(self.request.body)
        _get_forks(repo)


def _get_pulls(repo):
    """Get all pulls from a given repo, then start tasks to get info from them.
    """
    try:
        pulls_list = list(repo.get_pulls())
        for pull in pulls_list:
            make_task(purpose='get_comments',
                      payload=pull)

    except RateLimitExceededException:
        make_task(purpose='get_pulls',
                  payload=repo,
                  delay_until=_rate_reset())


class GetPulls(webapp2.RequestHandler):
    def get(self):
        repo = pickle.loads(self.request.body)
        _get_pulls(repo)

    def post(self):
        repo = pickle.loads(self.request.body)
        _get_pulls(repo)


def _get_comments(pull):
    """Get all comments from a pull, then store them along with the pull
    request's body (i.e. the first comment in its issues thread) on the
    datastore."""
    try:
        comment_list = list(pull.get_comments())
        comment_list.extend(list(pull.get_issue_comments()))
        for comment in comment_list:
            datastore_comment = models.Comment()
            datastore_comment.populate(
                github_id=comment.id,
                pull_request_id=pull.id,
                repo=pull.base.repo.name,
                author=comment.user.name,
                body=comment.body)
            datastore_comment.put_async()
        pull_body_comment = models.Comment()
        pull_body_comment.populate(
            github_id=pull.id,
            pull_request_id=pull.id,
            repo=pull.base.repo.name,
            author=pull.user.name,
            body=pull.body)

    except RateLimitExceededException:
        make_task(purpose='get_comments',
                  payload=pull,
                  delay_until=_rate_reset())


class GetComments(webapp2.RequestHandler):
    def get(self):
        pull = pickle.loads(self.request.body)
        _get_comments(pull)

    def post(self):
        pull = pickle.loads(self.request.body)
        _get_comments(pull)

