DEBUG = True

MIDDLEWARE_CLASSES = tuple(list(MIDDLEWARE_CLASSES).insert(1,
                'debug_toolbar.middleware.DebugToolbarMiddleware'))
MIDDLEWARE_CLASSES += (
    'gridcalendar.middlewares.ProfileMiddleware', )
INSTALLED_APPS = ('debug_toolbar',) + INSTALLED_APPS
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    # 'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel', # shows passwords !!!
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)
# don't show the toolbar if the profiler
#   gridcalendar.middlewares.ProfileMiddleware
# is used, which happens when adding ?profile=1 to the request
def custom_show_toolbar(request):
    if request.REQUEST.get('profile', False):
        return False
    return True

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': True,
    #'TAG': 'div',
}

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
CACHES['default']['KEY_PREFIX'] = 'debug'
