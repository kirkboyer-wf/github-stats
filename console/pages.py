import os

from github import Github
import jinja2
import webapp2
import settings
from notifications import get_all_notifications_from_org
from notifications import NotificationEntry
from notifications import UserEntry
import datetime
import logging

# import settings

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

GIT_OBJECT = Github(login_or_token=settings.AUTH_TOKEN)


def fill_notifications_data():
    # TODO: check if we already have data.
    if NotificationEntry.all().filter('timestamp >', datetime.datetime.now() +
                                      datetime.timedelta(-1)):
        logging.info("Already have stuff from within 1 days!!!")
        # then we've already got data
        return

    notes = [NotificationEntry(user=note['user'],
                               repo=note['repo'],
                               timestamp=note['timestamp'],
                               language=note['language'])
             for note in get_all_notifications_from_org(
                 GIT_OBJECT.get_organization(settings.ORG_NAME))]
    # Store raw notifications information

    user_languages = {}
    for note in notes:
        note.put()
        # store by-user data
        if note.user in user_languages:
            user_languages[note.user][note.language] += 1
        else:
            user_languages[note.user] = {note.language: 1}

    for user, languages in user_languages.items():
        u = UserEntry(languages=languages,
                      user=user)
        u.put()


def find_best_user_for_language(language):
    users = UserEntry.all().fetch()


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
        fill_notifications_data()
        template_values = {}
        self._make_page('report', template_values)

    def post(self):
        pass

