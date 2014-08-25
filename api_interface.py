# Functions for interfacing with (the pyGithub wrapper for) the Github API

# external modules
import github as pyGithub
import os
import logging
import jinja2
import webapp2

# project modules
import models
import settings

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


@ndb.transactional
def make_task_to_get_github():
    """Makes a github object available in the datastore."""
    logging.debug("Github-get: Inserting task to retrieve github login object.")
    taskqueue.add(url=settings.URLS['get_github'],
                  method='POST')


class GetGithub(webapp2.RequestHandler):
    def _get_github(self):
        if models.Github.query().get():
            return  # Don't make another github object.
        gh = models.Github()
        gh.populate(github_object=pyGithub.github(
            login_or_token=settings.AUTH_TOKEN,
            per_page=100))

        gh.put()

    def get(self):
        self._get_github()

    def post(self):
        self._get_github()


@ndb.transactional
def make_task_to_get_org():
    """Create a task that will try to get an organization from github until
    it's allowed.
    """
    logging.debug("Org-Get: Inserting task to retrieve org {0} "
                  "from github.".format(settings.ORG_NAME))
    taskqueue.add(url=settings.URLS['get_org'],
                  method='POST')


class GetOrg(webapp2.RequestHandler):
    def _get_org(self):
        if models.Organization.query(
                models.Organization.name == settings.ORG_NAME).get():
            return  # Don't make another organization object for this org

        # Make sure we have what we need
        gh = models.Github.query().get()
        if not gh:
            make_task_to_get_github()
            logging.debug("GetOrg task failed: no github object.")
            raise Exception("Don't have github object yet.")

        # Get the organization object and put it on the datastore
        github_org_object = gh.github.get_organization(settings.ORG_NAME)
        org = models.Organization()
        org.populate(organization=github_org_object,
                     name=encode_if_unicode(github_org_object.name))
        org.put()

    def post(self):
        self._get_org()

    def get(self):
        self._get_org()


@ndb.transactional
def make_task_to_get_repos():
    """Create a task that will try to get all Repositories from github for
    a given organization.
    """
    logging.debug("Repos-get: Inserting task to retrieve repos for {0}".format(
        settings.ORG_NAME))
    taskqueue.add(url=settings.urls['get_repos'],
                  method='POST')


class GetRepos(webapp2.RequestHandler):
    def _get_repos(self):
        # Make sure we have what we need
        org_object = models.Organization.query(
            models.Organization.name == settings.ORG_NAME).get()
        if not org_object:
            make_task_to_get_org(settings.ORG_NAME)
            logging.debug("GetRepos task failed: no org object.")
            raise Exception("Don't have {0} organization object yet.")

        # Get the repos and store them in Repository objects
        github_repo_objects = list(org_object.organization.get_repos())
        datastore_repos = []
        for repo in github_repo_objects:
            datastore_repo = models.Repository()
            datastore_repo.populate(name=encode_if_unicode(repo.name),
                                    repository=repo)
            datastore_repos.append(datastore_repo)
        ndb.put_multi(datastore_repos)

    def get(self):
        self._get_repos()

    def post(self):
        self._get_repos()


@ndb.transactional
def make_task_to_get_repo(repo_name):
    """Create a task that will try to get the given repository from github
    for the given organization.
    """
    logging.debug("Repo-get: Inserting task to retrieve repo {0}"
                  " for organization {1}".format(settings.ORG_NAME, repo_name))
    taskqueue.add(url=settings.urls['get_repo'],
                  method='POST',
                  params={'repo_name': repo_name})


class GetRepo(webapp2.RequestHandler):
    def _get_repo(self):
        repo_name = self.request.get('repo_name')

        # Make sure we have what we need
        org_object = models.Organization.query(
            models.Organization.name == settings.ORG_NAME).get()
        if not org_object:
            make_task_to_get_org(settings.ORG_NAME)
            logging.debug("GetRepo task failed: no org object.")
            raise Exception("Don't have {0} organization object yet.")

        # Get the repo and store it on the datastore
        github_repo_object = org_object.organization.get_repo(repo_name)
        repo = models.Repository()
        repo.populate(name=encode_if_unicode(github_repo_object.name),
                      repository=github_repo_object)
        repo.put()

    def get(self):
        self._get_repo()

    def post(self):
        self._get_repo()


@ndb.transactional
def make_task_to_get_forks(org_name, repo_name):
    """Create a task that will try to get the given repository from github
    for the given repository.
    """
    logging.debug("Forks-get: Inserting task to retrieve forks for {0}'s"
                  " repo {1}".format(settings.ORG_NAME, repo_name))
    taskqueue.add(url=settings.urls['get_forks'],
                  method='POST',
                  params={'repo_name'})


class GetForks(webapp2.RequestHandler):
    def _get_forks(self):
        repo_name = self.request.get('repo_name')

        # Make sure we have what we need
        repo_object = models.Repository.query(
            models.Repository.name == repo_name).get().repository
        if not repo_object:
            make_task_to_get_repo(settings.ORG_NAME, repo_name)
            logging.debug("GetRepo task failed: no github object.")
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

    def get(self):
        self._get_forks()

    def post(self):
        self._get_forks()
