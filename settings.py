AUTH_TOKEN = 'fake_token!'

try:
    import settings_local
except ImportError:
    settings_local = None

if settings_local:
    for setting in dir(settings_local):
        globals()[setting.upper()] = getattr(settings_local, setting)
