#!/Users/kirkboyer/Envs/github-stats/bin/python

# For now, do things locally. We'll set up an appspot later, once the stuff for
# pulling from Github actually works.

from github import Github

import settings

GIT_OBJECT = Github(login_or_token=settings.AUTH_TOKEN)
ORG_OBJECT = GIT_OBJECT.get_organization(settings.ORG_NAME)

ORG_LISTS = {
    'members': ORG_OBJECT.get_members,
    'repos': ORG_OBJECT.get_repos
}
