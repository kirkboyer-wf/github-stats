# built-in modules
import os
import sys

lib_path = os.path.join(os.getcwd(), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# third-party modules
import jinja2
import logging
import webapp2

# project modules
import models
import settings

from api_interface import Get
from api_interface import update_all_data

from console.pages import DownloadPage
from console.pages import IndexPage
from console.pages import ReportPage


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
