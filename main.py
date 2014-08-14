# import os
# import sys

from google.appengine.ext import webapp
from stats.pages import IndexPage
from stats.pages import ReportPage
# import settings

app = webapp.WSGIApplication([
    ('/', IndexPage),
    ('/report', ReportPage)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
