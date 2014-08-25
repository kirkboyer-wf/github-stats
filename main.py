import os
import sys

import jinja2
import webapp2

lib_path = os.path.join(os.getcwd(), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.appengine.ext import webapp

from console.pages import IndexPage
from console.pages import ReportPage
# import settings

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class DatObject(ndb.Model):
    value = ndb.IntegerProperty(indexed=False)


# TESTING TASK STUFF
class DatHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'values': DatObject.query()}
        test_template = JINJA_ENV.get_template('index.html')
        self.response.out.write(test_template.render(template_values))

    def post(self):
        key = self.request.get('key')
        taskqueue.add(url='/test_secret', params={'key': key})
        self.redirect('/')


class DatWorker(webapp2.RequestHandler):
    def post(self):
        key = self.request.get('key')

        def update_value():
            value = DatObject.get_or_insert(key, value=0)
            value.value += 1
            value.put()
        update_value()


app = webapp.WSGIApplication([
    ('/', IndexPage),
    ('/report', ReportPage),
    ('/test_tasks', DatHandler),
    ('/test_secret', DatWorker)
    # ('/url/that/was/hit/', HandlerClass),
    # list of these!
], debug=True)
