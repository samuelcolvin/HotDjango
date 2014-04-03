__version__ = '0.2'
from django.core.urlresolvers import reverse as _reverse
from public import *

def _check_settings_attr(attr):
    if not hasattr(settings, attr):
        raise HotDjangoError('settings has no attribute "%s"' % attr)

try:
    import settings
except ImportError:
    raise HotDjangoError('settings module not found')
else:
    _check_settings_attr('DISPLAY_APPS')
    _check_settings_attr('SITE_TITLE')
    _check_settings_attr('TOP_MENU')
    _check_settings_attr('INDEX_URL_NAME')
    get_all_apps()
    try:
        _reverse(settings.INDEX_URL_NAME)
    except:
        raise HotDjangoError('url with name settings.INDEX_URL_NAME: "%s" not found.' % settings.INDEX_URL_NAME)
    