# Enforce uniqueness of objects in datastore by name (don't allow even
# differently-typed objects to have the same name).

# Also enforce uniqueness of tasks by what they are trying to accomplish, so
# we don't waste time and github-rate-limit requests.

# TODO: Do everything context-style instead of this jankety way

from google.appengine.ext import ndb
from google.appengine.api import taskqueue
import logging
import webapp2

OBJECT_LIST_KEY = "object_list_key_sAj8eFJHQIiqjQHxHFy0pQokFQ23QFVaSDF"
TASK_LIST_KEY = "task_list_key_qpD13Apif4zc09zFqhV8PpoN2z9AmmoeD1QpG"


class EnforcedObjects(ndb.Model):
    keys = ndb.KeyProperty(repeated=True)


@ndb.transactional(xg=True)
def get_enforced_objects():
    return EnforcedObjects.get_or_insert(OBJECT_LIST_KEY)


@ndb.transactional(xg=True)
def safe_ndb_get_key_by_id(object_id):
    """Return the given key if it's in the enforced list."""
    objects = get_enforced_objects()
    # return the first (should be only) occurrence of the key in the list,
    # otherwise return None
    for key in objects.keys:
        if key.id() == object_id:
            return key


@ndb.transactional(xg=True)
def safe_ndb_put(target, id=None):
    """Attempt to register a new Key; if one exists with the given name,
    return None. If registration was successful, return the Key."""
    # if an ID wasn't given, create one!
    if not hasattr(target, 'key'):
        if not id:
            logging.info("Failed to put {0} in datastore; no id.".format(
                target))
            return
        else:
            target.populate(key=ndb.Key(target.__class__, id))

    if not safe_ndb_get_key_by_id(target.key.id()):
        result_key = target.put()
        enforced_objects = get_enforced_objects()
        enforced_objects.keys.append(result_key)
        enforced_objects.put()
        return result_key


class EnforcedTasks(ndb.Model):
    claimed_purposes = ndb.StringProperty(repeated=True)


@ndb.transactional(xg=True)
def get_enforced_tasks():
    return EnforcedTasks.get_or_insert(TASK_LIST_KEY)


@ndb.transactional(xg=True)
def safe_start_task(purpose=None, **kwargs):
    """Attempts to claim the purpose for you. If successful, starts the task
    and returns True. Otherwise returns False."""
    tasks = get_enforced_tasks()
    if purpose in tasks.claimed_purposes:
        logging.info("Task with purpose ({0}) failed; purpose claimed.".format(
            purpose))
        return False
    else:
        tasks.claimed_purposes.append(purpose)
        tasks.put()
        logging.info("\tCLAIMING: -<{0}>-".format(purpose))
        taskqueue.add(**kwargs)
        return True


@ndb.transactional(xg=True)
def unclaim_purpose(purpose):
    """If the given purpose is claimed, unclaim it. Obviously only a task
    that just completed the purpose/task should do this."""
    logging.info("\tUNCLAIMING: -<{0}>-".format(purpose))
    tasks = get_enforced_tasks()
    if purpose in tasks.claimed_purposes:
        tasks.claimed_purposes = [item for item in tasks.claimed_purposes
                                  if item != purpose]
        tasks.put()


class PurgeTasks(webapp2.RequestHandler):
    def get(self):
        try:
            ndb.Key(EnforcedTasks, TASK_LIST_KEY).delete()
        except:
            logging.info("There was no enforced task list, apparnetly.")

    def post(self):
        try:
            ndb.Key(EnforcedTasks, TASK_LIST_KEY).delete()
        except:
            logging.info("There was no enforced task list, apparnetly.")
