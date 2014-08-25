# Models for storing github data in the datastore

# external modules
import re

# appengine stuff
from google.appengine.ext import ndb


class Github(ndb.Model):
    github_object = ndb.PickleProperty()


def _usernames_mentioned_in_comment(comment):
    pattern = r'[@][a-zA-z]{3,25}[-]wf'
    return list(set(re.findall(pattern, comment.body)))


class Comment(ndb.Model):
    github_id = ndb.IntegerProperty()
    author = ndb.StringProperty()
    body = ndb.TextProperty()
    users = ndb.ComputedProperty(_usernames_mentioned_in_comment)


class PullRequest(ndb.Model):
    github_id = ndb.IntegerProperty()
    body = ndb.TextProperty()

    # list of comments
    comments = ndb.StructuredProperty(Comment, repeated=True)


class PullRequestComment(ndb.Model):
    """Just a pyGithub PullRequestComment object."""
    github_id = ndb.IntegerProperty()
    pull_request_comment = ndb.PickleProperty()


class Repository(ndb.Model):
    """Just a pyGithub Repository object."""
    name = ndb.StringProperty()
    repository = ndb.PickleProperty()

    # list of forks (Repositories)
    has_forks = ndb.BooleanProperty(default=True)
    forks = ndb.PickleProperty()

    # list of pull requests
    pulls = ndb.StructuredProperty(PullRequest, repeated=True)


def _dict_of_repos(org_model):
    return {repo.name: repo for repo in org_model.repos}


class Organization(ndb.Model):
    name = ndb.StringProperty()
    organization = ndb.PickleProperty()
    has_repos = ndb.BooleanProperty(default=False)
    _repos = ndb.StructuredProperty(Repository, repeated=True)
    repos = ndb.ComputedProperty(_dict_of_repos)


class Team(ndb.Model):
    """Just a pyGithub Team object."""
    name = ndb.StringProperty()
    team = ndb.PickleProperty()


class AttemptedTask(ndb.Model):
    ID = ndb.IntegerProperty()

    # the python .__name__ of the function the task is trying to complete
    function_name = ndb.StringProperty()

    # Whether the task terminated successfully
    completed = ndb.BooleanProperty(default=False)

    # whether the task was allowed to start or not
    accepted = ndb.BooleanProperty()

    timestamp = ndb.DateTimeProperty()


class TaskList(ndb.Model):
    """Helps to keep track of which tasks are already running,
    """
    tasks = ndb.StructuredProperty(AttemptedTask, repeated=True)

