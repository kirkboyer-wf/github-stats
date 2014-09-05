# built-in mdules
import jinja2
import os
import webapp2
import heapq

# third-party modules
from github import Github

# project modules
import models
import settings


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

GIT_OBJECT = Github(login_or_token=settings.AUTH_TOKEN)


def _mention_count_by_language(comments, languages):
    num_mentions = {language: {} for language in languages}

    for comment in comments:
        for user in comment.users:
            if user in num_mentions[comment.language]:
                num_mentions[comment.language][user] += 1
            else:
                num_mentions[comment.language][user] = 1

    return num_mentions


def _top_users_by_language(num_mentions, languages, n_largest):
    top_users = {}
    for language in languages:
        top_users[language] = heapq.nlargest(
            n_largest,
            num_mentions[language].iterkeys(),
            key=(lambda user:
                 num_mentions[language][user]))

    return top_users


def _language_stats_text(user, rank, mentions):
    return "\t#{rank}: {user}, mentioned {mentions} times\n".format(
        rank=rank, user=user, mentions=mentions)


def _language_report_text(languages, num_mentions, n_largest):
    report = "Top users by language, using # mentions in comments:\n"
    top_users = _top_users_by_language(num_mentions, languages, n_largest)
    for language in languages:
        if language == 'None':  # for this report, only repos with languages.
            continue

        report += "Top users for {0}\n".format(language)

        for rank, user in enumerate(top_users[language]):
            report += _language_stats_text(
                user, rank+1, num_mentions[language][user])
    return report


def _make_language_report_available(comments, languages, n_largest):
    languages = set([comment.language for comment in comments])
    num_mentions = _mention_count_by_language(comments, languages)
    language_report = models.Report.get_or_insert('language_report')
    language_report.text = _language_report_text(languages,
                                                 num_mentions,
                                                 n_largest)
    language_report.put()


def _make_connectivity_report_available(comments, languages, n_largest):
    pass  # TODO: make this do something


def _make_reports_available(n_largest=10, pr_body=True):
    comments = models.Comment.query().fetch()

    _make_language_report_available(comments, n_largest)
    _make_connectivity_report_available(comments, n_largest)


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
        _make_reports_available()


class ReportPage(Page):
    def get(self):
        template_values = {}
        _make_reports_available()
        self._make_page('report', template_values)
        self.redirect(settings.URLS['download'])


class IndexPage(Page):
    def get(self):
        template_values = {}
        self._make_page('index', template_values)

    def post(self):
        pass
