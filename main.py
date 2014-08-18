# import os
# import sys

from google.appengine.ext import webapp
from console.pages import IndexPage
from console.pages import ReportPage
# import settings

app = webapp.WSGIApplication([
    ('/', IndexPage),
    ('/report', ReportPage)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
