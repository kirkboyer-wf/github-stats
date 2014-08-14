# import os
# import sys

from google.appengine.ext import webapp
from pages import IndexPage
from pages import ReportPage
# import settings

app = webapp.WSGIApplication([
    ('/', IndexPage),
    ('/report', ReportPage)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
