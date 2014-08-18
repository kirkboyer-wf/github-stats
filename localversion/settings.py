AUTH_TOKEN = 'fake_token!'
ORG_NAME = "yippy-dippy!"
SORT_BY = "who knows?"
SINCE = None

try:
    import settings_local
except ImportError:
    settings_local = None

if settings_local:
    for setting in dir(settings_local):
        globals()[setting.upper()] = getattr(settings_local, setting)
