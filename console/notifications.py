import re
import pickle
import logging
from google.appengine.ext import db


def _users_tagged_in_comment(comment):
    """Given a comment, returns the set of @somebody-wf tags that
    appear in its body.
    """
    pattern = r'[@][a-zA-Z]{3,}[-]wf'
    return set(re.findall(pattern, comment.body))


def _primary_language(repo):
    """Given a repo, determine its primary language (based on number of lines
    of code).
    """
    languages = repo.get_languages()
    if not languages:
        return 'None'
    return max(languages.iterkeys(), key=(lambda key: languages[key]))


def _get_notes_from_repo(repo):
    notes = []
    logging.info("Getting notes from repo: {0}".format(repo.name))

    for comment in repo.get_pulls_comments():
        notes.extend([{'user': user,
                       'repo': repo.name,
                       'timestamp': comment.created_at,
                       'language': _primary_language(repo)}
                      for user in _users_tagged_in_comment(comment)])

    return notes


def get_all_notifications_from_org(organization):
    notes = []
    for repo in organization.get_repos():
        notes.extend(_get_notes_from_repo(repo))
    return notes


class NotificationEntry(db.Model):
    user = db.StringProperty()
    repo = db.StringProperty()
    timestamp = db.DateTimeProperty()
    language = db.StringProperty()


class DictProperty(db.Property):
    data_type = dict

    def get_value_for_datastore(self, model_instance):
        value = super(DictProperty, self).get_value_for_datastore(
            model_instance)
        return db.Blob(pickle.dumps(value))

    def make_value_from_datastore(self, value):
        if value is None:
            return dict()
        return pickle.loads(value)

    def default_value(self):
        if self.default is None:
            return dict()
        else:
            return super(DictProperty, self).default_value().copy()

    def validate(self, value):
        if not isinstance(value, dict):
            raise db.BadValueError('Property {0} needs to be convertible'
                                   'to a dict instance {1} (class dict)'.format(
                                       self.name, value))
        return super(DictProperty, self).validate(value)

    def empty(self, value):
        return value is None


class LanguageEntry(db.Model):
    _users = DictProperty()  # dict with entries user: num_lang_notes
    language = db.StringProperty()
    updated = db.DateTimeProperty()  # when the top 10 was last calculated

    def users(self):
        """Returns a list with the top 10 users, sorted descending.
        (So the first entry is the top user for this language.)
        """
        return sorted(self._users.keys(), key=(lambda key: self._users[key]))


class UserEntry(db.Model):
    languages = DictProperty()  # dict with entries language: num_notes
    user = db.StringProperty()
