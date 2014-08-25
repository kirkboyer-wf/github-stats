# Deal with appengine task stuff

from functools import wraps


def once_only_task(f, task_ID):
    """Assigns a special ID to this task and only starts it if appengine doesn't
    already have a task assigned the same ID.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        pass
