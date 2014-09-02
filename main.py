import os
import sys
import jinja2
import webapp2

lib_path = os.path.join(os.getcwd(), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# project modules
import settings

from api_interface import update_data
from api_interface import Get

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
        # get_forks_task('bigsky')
        # get_pulls_task('wf-grafana')
        update_data()


app = webapp2.WSGIApplication([
    ('/', IndexPage),
    ('/report', ReportPage),
    ('/test_tasks', Tester),
    (settings.URLS['get_comments'], Get),
    (settings.URLS['get_repos'], Get),
    (settings.URLS['get_forks'], Get),
    (settings.URLS['get_pulls'], Get)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
