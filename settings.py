AUTH_TOKEN = 'fake_token!'
ORG_NAME = "yippy-dippy!"


URLS = {
    'download': '',
    'report': '',
    'update': '',
    'get_github': '',
    'get_org': '',
    'get_orgs': '',
    'get_repos': '',
    'get_forks': '',
    'get_pulls': '',
    'get_comments': '',
}


try:
    import settings_local
except ImportError:
    settings_local = None

if settings_local:
    for setting in dir(settings_local):
        globals()[setting.upper()] = getattr(settings_local, setting)
