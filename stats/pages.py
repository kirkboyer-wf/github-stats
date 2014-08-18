import os

import jinja2
import webapp2

# import settings

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Page(webapp2.RequestHandler):
    def _make_page(self, page_name, template_values):
        template = JINJA_ENVIRONMENT.get_template(
            'templates/{page}.html'.format(page=page_name))
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(template_values))


class IndexPage(Page):
    def get(self):
        template_values = {}
        self._make_page('index', template_values)

    def post(self):
        pass


class ReportPage(Page):
    def get(self):
        template_values = {}
        self._make_page('report', template_values)

    def post(self):
        pass

