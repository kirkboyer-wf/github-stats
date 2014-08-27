import os
import sys
import jinja2
import webapp2

lib_path = os.path.join(os.getcwd(), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# project modules
import settings
from api_interface import get_github
from api_interface import get_org

from api_interface import GetGithub
from api_interface import GetOrg
from api_interface import GetRepos
from api_interface import GetRepo
from api_interface import GetForks
from api_interface import GetPulls

from console.pages import IndexPage
from console.pages import ReportPage

# google app engine stuff
# from google.appengine.ext import ndb
# from google.appengine.api import taskqueue

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Tester(webapp2.RequestHandler):
    def get(self):
        # Make each kind of task
        get_github()
        get_org()
        # make_task_to_get_org()

app = webapp2.WSGIApplication([
    ('/', IndexPage),
    ('/report', ReportPage),
    ('/test_tasks', Tester),
    (settings.URLS['get_github'], GetGithub),
    (settings.URLS['get_org'], GetOrg),
    (settings.URLS['get_repos'], GetRepos),
    (settings.URLS['get_repo'], GetRepo),
    (settings.URLS['get_forks'], GetForks),
    (settings.URLS['get_pulls'], GetPulls)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
