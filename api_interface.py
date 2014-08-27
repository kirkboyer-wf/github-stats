# Funcs/classes for interfacing with (the pyGithub wrapper for) the Github API

# external modules
import github as pyGithub
import os
import logging
import jinja2
import webapp2

# project modules
import models
import settings
from enforcement import safe_ndb_get_key_by_id
from enforcement import safe_ndb_put
from enforcement import safe_start_task
from enforcement import unclaim_purpose

# appengine stuff
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


# Lots of unicode strings; deal with them!
def encode_if_unicode(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string


def get_github_task():
    """Makes a task to get a new github object."""
    if safe_ndb_get_key_by_id('github_obj'):
        return  # Don't duplicate the github object

    logging.debug("Github-Get: Inserting task to retrieve Github Object "
                  "from github.")
    safe_start_task(purpose='get_github_object',
                    url=settings.URLS['get_github'],
                    method='POST')


def _get_github():
    # Assume the task was safely started, and do your stuff
    try:
        gh = models.Github()
        github_object = pyGithub.Github(login_or_token=settings.AUTH_TOKEN,
                                        per_page=100)
        gh.populate(github_object=github_object,
                    key=ndb.Key(models.Github, 'github_object'))
        safe_ndb_put(gh)
    finally:
        unclaim_purpose('get_github_object')


class GetGithub(webapp2.RequestHandler):
    def get(self):
        _get_github()

    def post(self):
        _get_github()


def get_org_task():
    """Create a task that will try to get an organization from github until
    it's allowed.
    """
    if safe_ndb_get_key_by_id('org_obj'):
        return  # Don't duplicate the org object

    logging.debug("Org-Get: Inserting task to retrieve org {0} "
                  "from github.".format(settings.ORG_NAME))
    safe_start_task(purpose='get_org_object',
                    url=settings.URLS['get_org'],
                    method='POST')


def _get_org():
    # Assume the task was safely started, and try to get a github object
    try:
        gh_key = safe_ndb_get_key_by_id('github_object')
        # gh = models.Github.query().get()
        if not gh_key:
            logging.debug("GetOrg task failed: no github object.")
            get_github_task()
            raise Exception("GetOrg: Don't have github object yet.")
        else:
            gh = gh_key.get()
            unclaim_purpose('get_org_object')

        # Get the organization object and put it on the datastore
        github_org_object = gh.github_object.get_organization(settings.ORG_NAME)
        org = models.Organization()
        org.populate(organization=github_org_object,
                     name=encode_if_unicode(github_org_object.name),
                     key=ndb.Key(models.Organization, 'org_object'))
        safe_ndb_put(org)
    finally:
        unclaim_purpose('get_org_object')


class GetOrg(webapp2.RequestHandler):
    def post(self):
        _get_org()

    def get(self):
        _get_org()


def get_repos_task():
    """Create a task that will try to get all Repositories from github for
    a given organization.
    """
    org_key = safe_ndb_get_key_by_id('org_obj')
    if org_key:
        org = org_key.get()
        if hasattr(org, 'has_repos') and org.has_repos:
            return  # Org already has its repos, so don't make them again

    logging.debug("Repos-get: Inserting task to retrieve repos for {0}".format(
        settings.ORG_NAME))
    safe_start_task(purpose='get_repos',
                    url=settings.URLS['get_repos'],
                    method='POST')


def _get_repos():
    try:
        org_key = safe_ndb_get_key_by_id('org_object')
        if not org_key:
            get_org_task()
            logging.debug("GetRepos task failed: no org object.")
            raise Exception("GetRepos: Don't have organization object yet.")
        else:
            org = org_key.get()
            # Get the repos and store them in the Org object, if the org object
            # doesn't already have them
            # TODO: make this update if a timestamp is out of date
            github_repo_objects = list(org.organization.get_repos())
            github_repo_objects = {encode_if_unicode(repo.name): repo
                                   for repo in github_repo_objects}
            org.populate(repos=github_repo_objects, has_repos=True)
            safe_ndb_put(org)

            # Store the repository objects individually on the datastore

            datastore_repos = []
            for name, repo in github_repo_objects.items():
                datastore_repo = models.Repository()
                name = encode_if_unicode(name)
                datastore_repo.populate(
                    name="repo:"+name,
                    repository=repo,
                    key=ndb.Key(models.Repository, "repo:"+name))
                datastore_repos.append(datastore_repo)

            ndb.put_multi(datastore_repos)
    finally:
        unclaim_purpose('get_repos')


class GetRepos(webapp2.RequestHandler):
    def get(self):
        _get_repos()

    def post(self):
        _get_repos()


def get_repo_task(repo_name):
    """Create a task that will try to get the given repository from github
    for the given organization, and store it separately on the datastore.
    """
    repo_key = safe_ndb_get_key_by_id('repo:'+repo_name)
    if repo_key:
        return  # We already have this repo. TODO: make date relevant

    logging.debug("Repo-get: Inserting task to retrieve repo {0}"
                  " for organization {1}".format(settings.ORG_NAME, repo_name))
    safe_start_task(purpose='get_repo:{0}'.format(repo_name),
                    url=settings.URLS['get_repo'],
                    method='POST',
                    params={'repo_name': repo_name})


def _get_repo(repo_name):
    try:
        org_key = safe_ndb_get_key_by_id('org_object')
        if not org_key:
            get_org_task()
            logging.debug("GetRepo task failed: no org object.")
            raise Exception("GetRepo: Don't have organization object yet.")
        else:
            org = org_key.get()
            # github operation
            github_repo_object = org.organization.get_repo(repo_name)
            repo = models.Repository()
            repo_name = encode_if_unicode(repo_name)
            repo.populate(name="repo:"+repo_name,
                          repository=github_repo_object,
                          key=ndb.Key(models.Repository, "repo:"+repo_name))
            safe_ndb_put(repo)
    finally:
        unclaim_purpose('get_repo:{0}'.format(repo_name))


class GetRepo(webapp2.RequestHandler):
    def get(self):
        repo_name = self.request.get('repo_name')
        _get_repo(repo_name)

    def post(self):
        repo_name = self.request.get('repo_name')
        _get_repo(repo_name)


def get_forks_task(repo_name):
    """Create a task that will try to get the given repository from github
    for the given repository.
    """
    repo_key = safe_ndb_get_key_by_id('repo:'+repo_name)
    if repo_key:
        if repo_key.get().has_forks:
            return  # Already got this repo's forks.

    logging.debug("Forks-get: Inserting task to retrieve forks for {0}'s"
                  " repo {1}".format(settings.ORG_NAME, repo_name))
    safe_start_task(purpose='get_forks:{0}'.format(repo_name),
                    url=settings.URLS['get_forks'],
                    method='POST',
                    params={'repo_name': repo_name})


def _get_forks(repo_name):
    try:
        repo_key = safe_ndb_get_key_by_id("repo:{0}".format(repo_name))
        if not repo_key:
            get_repo_task(repo_name)
            logging.debug("GetForks task failed: don't have repo.")
            raise Exception("GetRepo: Don't have repo {0} to fork.".format(
                repo_name))
        else:
            repo = repo_key.get()
            github_forks_list = list(repo.repository.get_forks())
            for github_fork in github_forks_list:
                fork = models.Repository()
                fork_name = encode_if_unicode(fork.name)
                fork.populate(name='repo:'+fork_name,
                              repository=github_fork,
                              key=ndb.Key(models.Repository, 'repo:'+fork_name))
                safe_ndb_put(fork)

    finally:
        unclaim_purpose('get_forks:{0}'.format(repo_name))


class GetForks(webapp2.RequestHandler):
    def _get_forks(self):
        repo_name = self.request.get('repo_name')

        # Make sure we have what we need
        repo_object = models.Repository.query(
            models.Repository.name == repo_name).get()
        if not repo_object:
            get_repo_task(repo_name)
            logging.debug("GetForks task failed: no github object.")
            raise Exception("Don't have {0}'s {1} repo object yet.".format(
                settings.ORG_NAME, repo_name))

        # Get the fork-repositories and store them on the datastore
        github_repo_objects = list(repo_object.repository.get_forks())
        datastore_repos = []
        for fork in github_repo_objects:
            datastore_repo = models.Repository()
            datastore_repo.populate(name=encode_if_unicode(fork.name),
                                    repo=fork)
            datastore_repos.append(datastore_repo)

        ndb.put_multi(datastore_repos)
        repo_object.populate(has_forks=True)
        repo_object.put()

    def get(self):
        self._get_forks()

    def post(self):
        self._get_forks()


@ndb.transactional(xg=True)
def make_task_to_get_pulls(repo_name):
    """Create a task that will try to get the given repository's pull requests.
    """
    logging.debug("Pulls-get: Inserting task to retrieve pulls for"
                  " repository {0}".format(repo_name))
    taskqueue.add(url=settings.URLS['get_pulls'],
                  method='POST',
                  params={'repo_name': repo_name})


class GetPulls(webapp2.RequestHandler):
    def _get_pulls(self):
        repo_name = self.request.get('repo_name')

        # Make sure we have what we need
        repo_object = models.Repository.query(
            models.Repository.name == repo_name).get()
        if not repo_object:
            get_repo_task(repo_name)
            logging.debug("GetPulls task failed: no github object.")
            raise Exception("Don't have {0}'s {1} repo object yet.".format(
                settings.ORG_NAME, repo_name))

        # Get the pulls and store them in the repo object, if that object
        # doesn't already have up-to-date pulls
        github_pull_objects = list(repo_object.repository.get_pulls())
        datastore_pulls = []
        for pull in github_pull_objects:
            datastore_pull = models.PullRequest()
            datastore_pull.populate(github_id=pull.id,
                                    body=pull.body)
            datastore_pulls.append(datastore_pull)
        ndb.put_multi(datastore_pulls)
        repo_object.populate(has_pulls=True)
        repo_object.put()

    def get(self):
        self._get_pulls()

    def post(self):
        self._get_pulls()
