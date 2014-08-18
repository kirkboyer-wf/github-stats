#!/Users/kirkboyer/Envs/github-stats/bin/python

import settings
from github import Github
import re


def _users_tagged_in_comment(comment):
    """Given a comment, returns the set of @somebody-wf tags that
    appear in its body.
    """
    print("Looking for tags in:\n{0}\n".format(comment.body))
    pattern = r'[@][a-zA-Z]{3,}[-]wf'
    return set(re.findall(pattern, comment.body))


def _get_notes_from_repo(repo):
    notes = []
    print("comments to search:{0}".format(
        list(comment.body for comment in repo.get_pulls_comments())))
    for comment in repo.get_pulls_comments():
        notes.extend([{'user': user,
                       'repo': repo,
                       'timestamp': comment.updated_at,
                       'language': repo.language}
                      for user in _users_tagged_in_comment(comment)])
    return notes


# yay pretty displays
def __fill_with_spaces(string, length=15):
    return string + (length - len(string))*" "


if __name__ == "__main__":
    # import sys
    # fname = sys.argv[1]

    # gather information
    GIT_OBJECT = Github(login_or_token=settings.AUTH_TOKEN)
    ORG_OBJECT = GIT_OBJECT.get_organization(settings.ORG_NAME)

    notes = []
    for repo in ORG_OBJECT.get_repos():
        notes.extend(_get_notes_from_repo(repo))

    print("Repos searched: {0}\n".format(list(
        repo.name for repo in ORG_OBJECT.get_repos())))
    # testing that I found notes!
    print("Notes found:")
    print("{user}{repo}{timestamp}{language}".format(
        user=__fill_with_spaces("User"),
        repo=__fill_with_spaces("Repo"),
        timestamp=__fill_with_spaces("Timestamp"),
        language=__fill_with_spaces("Language")))
    for note in notes:
        print("{user}{repo}{timestamp}{language}".format(
            user=__fill_with_spaces(note['user']),
            repo=__fill_with_spaces(note['repo']),
            timestamp=__fill_with_spaces(note['timestamp']),
            language=__fill_with_spaces(note['language'])))

    # write to given filename
    # with open(fname, 'w') as f:
    #     pass
