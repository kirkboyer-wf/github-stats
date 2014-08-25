#!/Users/kirkboyer/Envs/github-stats/bin/python

import time
import datetime
import settings
from github import Github
# from github.GithubException import RateLimitExceededException
import re
import os


def _handle_rate_limit(function, *args, **kwargs):
    """Will only wait and try again ONCE per attempted call, if the first
    attempt leads to a rate limit exceeded response.
    """
    try:
        return function(*args, **kwargs)
    except Exception, e:
        wait_until = datetime.datetime.fromtimestamp(int(e.message)+5)
        print(80*"*")
        print("Wait until {0} to hit API again".format(wait_until))
        print(80*"*")
        # time.sleep((wait_until-datetime.datetime.now()).seconds)
        return function(*args, **kwargs)


def _users_tagged_in_comment(comment):
    """Given a comment, returns the set of @somebody-wf tags that
    appear in its body.
    """
    pattern = r'[@][a-zA-Z]{3,}[-]wf'
    return set(re.findall(pattern, comment))


def _primary_language(repo):
    """Given a repo, determine its primary language (based on number of lines
    of code).
    """
    # languages = repo.get_languages()
    languages = _handle_rate_limit(repo.get_languages)
    if list(languages.iterkeys()):
        return max(languages.iterkeys(), key=(lambda key: languages[key]))
    return "None"


def _get_notes_from_repo(repo):
    """pyGithub's handling of this is dumb and doesn't let you get anything
    from closed pull requests. This function circumvents that issue.
    """
    notes = []

    total_data_path = os.path.dirname(os.path.join(os.path.realpath(__file__)))
    total_data_path = os.path.join(total_data_path, 'repo-data')
    data_path = os.path.join(total_data_path, repo.name)

    # skip the repo if we have a .data file for it already
    if ((os.path.join(total_data_path, repo.name+'.data')
         in os.listdir(total_data_path))):
        return

    print("Getting notes from repo: {0}".format(repo.name))
    # get comments from pull requests
    language = _primary_language(repo)

    pulls = _handle_rate_limit(repo.get_pulls, state="all")

    for pr in pulls:
        # skip this pull request if there is already a data file for it
        if os.path.isdir(data_path):
            if (str(pr.id)+'.data') in os.listdir(data_path):
                print("Skipping pull request {0}:{1}".format(
                    pr.id,
                    pr.title.encode('utf-8')))
                continue
        else:
            # TODO: remove this artificial slowdown once you have baseline data
            os.makedirs(data_path)
        # the first comment is recorded as the "pull request body"
        new_notes = [{'user': user,
                      'body': True,
                      'repo': repo.name,
                      'timestamp': pr.created_at,
                      'language': language}
                     for user in _users_tagged_in_comment(pr.body)]

        comments = _handle_rate_limit(pr.get_comments)

        # all other comments are regular comments
        for comment in comments:
            new_notes.extend([{'user': user,
                               'body': False,
                               'repo': repo.name,
                               'timestamp': comment.created_at,
                               'language': language}
                              for user in _users_tagged_in_comment(
                                  comment.body)])

        issue_comments = _handle_rate_limit(pr.get_issue_comments)

        for comment in issue_comments:
            new_notes.extend([{'user': user,
                               'body': False,
                               'repo': repo.name,
                               'language': language}
                              for user in _users_tagged_in_comment(
                                  comment.body)])
        time.sleep(1)
        # Track this pull request individually
        with open(os.path.join(data_path,
                               str(pr.id)+'.data'), 'wb') as f:
            pickle.dump(new_notes, f, pickle.HIGHEST_PROTOCOL)
            print("Storing notes from pull request {0}:{1}".format(
                pr.id,
                pr.title.encode('utf-8')))

    # if you have by-pull-request stored information, put it together and store
    if os.path.isdir(data_path):
        notes = []
        for prfile in os.listdir(data_path):
            with open(os.path.join(data_path, prfile), 'rb') as f:
                notes.extend(pickle.load(f))
        with open(os.path.join(total_data_path, repo.name+'.data'), 'wb') as f:
            pickle.dump(notes, f, pickle.HIGHEST_PROTOCOL)

    # Old way of doin' it
    # with open(os.path.join(data_path, repo.name+'.data'), 'wb') as f:
    #     pickle.dump(notes, f, pickle.HIGHEST_PROTOCOL)
    # This was the previous try. It couldn't handle closed Pull Requests:
    print("Got {0} notes!\n".format(len(notes)))
    # return notes


# yay pretty displays
def __fill_with_spaces(string, length=15):
    return string + (length - len(string))*" "


if __name__ == "__main__":
    # import sys
    import pickle
    # fname = sys.argv[1]

    # gather information
    # GIT_OBJECT = Github(login_or_token=settings.AUTH_TOKEN)
    # ORG_OBJECT = GIT_OBJECT.get_organization(settings.ORG_NAME)

    GIT_OBJECT = _handle_rate_limit(Github,
                                    login_or_token=settings.AUTH_TOKEN,
                                    per_page=100)
    ORG_OBJECT = _handle_rate_limit(GIT_OBJECT.get_organization,
                                    settings.ORG_NAME)
    repos = list(_handle_rate_limit(ORG_OBJECT.get_repos))

    print("Repos searched: {0}\n".format(list(
        repo.name for repo in repos)))
    notes = []
    start_at = u''

    if start_at:
        i = [True if repo.name == start_at else False
             for repo in repos].index(True)
        repos = repos[i:]

    # for repo in ORG_OBJECT.get_repos():
    for repo in repos:
        # if repo.name != u'housekeeper':
        #     continue
        _get_notes_from_repo(repo)
        # new_notes = _get_notes_from_repo(repo)
        # notes.extend(new_notes)

    # with open(fname, 'wb') as f:
        # put all the data into the given filename
        # pickle.dump(notes, f, pickle.HIGHEST_PROTOCOL)

    # testing that I found notes!
    # print("Notes found:")
    # print("{user}{repo}{timestamp}{language}".format(
    #     user=__fill_with_spaces("User"),
    #     repo=__fill_with_spaces("Repo"),
    #     timestamp=__fill_with_spaces("Timestamp", 20),
    #     language=__fill_with_spaces("Language")))
    # for note in notes:
    #     print("{user}{repo}{timestamp}{language}".format(
    #         user=__fill_with_spaces(note['user']),
    #         repo=__fill_with_spaces(note['repo'].name),
    #         timestamp=__fill_with_spaces(str(note['timestamp']), 20),
    #         language=__fill_with_spaces(note['language'])))
