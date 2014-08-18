class Notification(object):
    def __init__(self, user=None, repo=None, timestamp=None):
        self._user = user
        self._repo = repo
        self._timestamp = timestamp
