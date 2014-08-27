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
    has_comments = ndb.BooleanProperty(default=False)
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
    has_forks = ndb.BooleanProperty(default=False)
    forks = ndb.PickleProperty()

    # list of pull requests
    has_pulls = ndb.BooleanProperty(default=False)
    pulls = ndb.PickleProperty()


def _dict_of_repos(org_model):
    return {repo.name: repo for repo in org_model.repos}


class Organization(ndb.Model):
    name = ndb.StringProperty()
    organization = ndb.PickleProperty()
    has_repos = ndb.BooleanProperty(default=False)

    # pickled dict of repos
    repos = ndb.PickleProperty()


class Team(ndb.Model):
    """Just a pyGithub Team object."""
    name = ndb.StringProperty()
    team = ndb.PickleProperty()
