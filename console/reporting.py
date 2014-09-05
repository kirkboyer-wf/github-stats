# built-in modules
import heapq

# third party modules
from google.appengine.ext import deferred

# project modules
import models


def _mentions_by_language(comments, languages):
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


def _language_report_text(comments, n_largest):
    languages = set([comment.language for comment in comments])
    num_mentions = _mentions_by_language(comments, languages)
    top_users = _top_users_by_language(num_mentions, languages, n_largest)
    report = "Top users by language, using # mentions in comments:\n"
    for language in languages:
        if language == 'None':  # for this report, only repos with languages.
            continue
        report += "Top users for {0}\n".format(languages)
        for rank, user in enumerate(top_users[language]):
            report += _language_stats_text(
                user, rank+1, num_mentions[language][user])
    return report


def _make_language_report_available(comments, n_largest):
    language_report = models.Report.get_or_insert('language_report')
    language_report.text = _language_report_text(n_largest)
    language_report.put()


def make_reports_available(n_largest=10, pr_body=True):
    comments = models.Comment.query().fetch()
    deferred.defer(_make_language_report_available, comments, n_largest)


def _make_connectivity_report_available(comments, n_largest):
    pass
