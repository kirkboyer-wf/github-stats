#!/Users/kirkboyer/Envs/github-stats/bin/python

import settings
from github import Github

if __name__ == "__main__":
    import sys
    options_file = sys.argv[1]
    fname = sys.argv[2]

    # gather information
    GIT_OBJECT = Github(auth_token=settings.AUTH_TOKEN)
    ORG_OBJECT = GIT_OBJECT.get_organization(settings.ORG_NAME)


    # write to given filename
    with open(fname, 'w') as f:
        pass
