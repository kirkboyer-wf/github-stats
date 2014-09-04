# Models for storing github data in the datastore

# external modules
import re

# appengine stuff
from google.appengine.ext import ndb


def _usernames_mentioned_in_comment(comment):
    pattern = r'[@][a-zA-Z]{3,25}[-]wf'
    return list(set(re.findall(pattern, comment.body)))


class Comment(ndb.Model):
    github_id = ndb.IntegerProperty()
    pull_request_id = ndb.IntegerProperty()
    repo = ndb.StringProperty()
    language = ndb.StringProperty()
    author = ndb.StringProperty()
    body = ndb.TextProperty()
    users = ndb.ComputedProperty(_usernames_mentioned_in_comment,
                                 repeated=True)


class Update(ndb.Model):
    last = ndb.DateTimeProperty()
    current = ndb.DateTimeProperty()
