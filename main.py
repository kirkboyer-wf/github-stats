import os
import sys
import jinja2
import webapp2
import logging

lib_path = os.path.join(os.getcwd(), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# project modules
import settings
import models

from api_interface import update_all_data
from api_interface import Get

from console.pages import IndexPage
from console.pages import ReportPage
from console.pages import DownloadPage

# google app engine stuff
# from google.appengine.ext import ndb
# from google.appengine.api import taskqueue

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Updater(webapp2.RequestHandler):
    def get(self):
        logging.info("Before this update: have {0} comments.".format(
            models.Comment.query().count()))
        update_all_data()


app = webapp2.WSGIApplication([
    ('/', IndexPage),
    (settings.URLS['download'], DownloadPage),
    (settings.URLS['report'], ReportPage),
    (settings.URLS['update'], Updater),
    (settings.URLS['get_comments'], Get),
    (settings.URLS['get_repos'], Get),
    (settings.URLS['get_forks'], Get),
    (settings.URLS['get_pulls'], Get)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
