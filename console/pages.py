# built-in mdules
import jinja2
import os
import webapp2
import heapq
import logging

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


def _prepare_report(n_largest=10, pr_body=True):
    # for each language, find top user by mentions
    logging.info("getting comments...")
    comments = models.Comment.query().fetch()

    languages = set([comment.language for comment in comments])
    num_mentions = {language: {} for language in languages}

    logging.info("counting mentions.")
    # count mentions of a user by language
    for comment in comments:
        # if comment.github_id == comment.pull_request_id and not pr_body:
        #     continue
        for user in comment.users:
            if user in num_mentions[comment.language]:
                num_mentions[comment.language][user] += 1
            else:
                num_mentions[comment.language][user] = 1

    logging.info("getting top users.")
    # get top users by language
    top_users = {}
    for language in languages:
        top_users[language] = heapq.nlargest(
            n_largest,
            num_mentions[language].iterkeys(),
            key=(lambda k:
                 num_mentions[language][k]))

    logging.info("building output file")
    # build output file
    output_text = "Top users by mentions in comments:\n"
    for language in languages:
        if language == 'None':
            continue

        output_text += "Top users for {0}\n".format(language)

        for rank, user in enumerate(top_users[language]):
            output_text += ("\t#{rank}: {user},"
                            " mentioned {mentions} times\n".format(
                                rank=rank+1,
                                user=user,
                                mentions=num_mentions[language][user]))

    report = models.Report.get_or_insert('report')
    report.text = output_text
    report.put()
    return top_users, num_mentions, languages


def _start_download(handler, file_content, filename):
    logging.info("Starting download...")
    handler.response.headers[
        'Content-Disposition'] = 'attachment; filename={0}'.format(
            filename)
    handler.response.out.write(file_content)


class DownloadPage(webapp2.RequestHandler):
    def get(self):
        _start_download(self,
                        file_content=models.Report.get_or_insert(
                            'report').text or 'Report not created yet.',
                        filename='test_data.txt')


class PrepareReportPage(webapp2.RequestHandler):
    def post(self):
        _prepare_report()


class ReportPage(Page):
    def get(self):
        template_values = {}
        _prepare_report()
        self._make_page('report', template_values)
        self.redirect(settings.URLS['download'])
