# built-in mdules
import jinja2
import os
import webapp2

# third-party modules
from github import Github

# project modules
import models
import settings
from reporting import make_reports_available


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

GIT_OBJECT = Github(login_or_token=settings.AUTH_TOKEN)


def _start_download(handler, file_content, filename):
    handler.response.headers[
        'Content-Disposition'] = 'attachment; filename={0}'.format(
            filename)
    handler.response.out.write(file_content)


class Page(webapp2.RequestHandler):
    def _make_page(self, page_name, template_values):
        template = JINJA_ENVIRONMENT.get_template(
            'templates/{page}.html'.format(page=page_name))
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(template.render(template_values))


class DownloadPage(webapp2.RequestHandler):
    def get(self):
        _start_download(
            self,
            file_content=models.Report.get_or_insert(
                'report').text or 'Report not created yet.',
            filename='test_data.txt')


class PrepareReportPage(webapp2.RequestHandler):
    def post(self):
        make_reports_available()


class ReportPage(Page):
    def get(self):
        template_values = {}
        self._make_page('report', template_values)
        self.redirect(settings.URLS['download'])


class IndexPage(Page):
    def get(self):
        template_values = {}
        self._make_page('index', template_values)

    def post(self):
        pass
