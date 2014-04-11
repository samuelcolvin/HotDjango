from public import *
import traceback

__version__ = '0.2'

def validate():
    """
    Try to check everything looks ok right at the beginning.
    """
    from django.core.urlresolvers import reverse as _reverse
    def _check_settings_attr(attr):
        if not hasattr(settings, attr):
            raise HotDjangoError('settings has no attribute "%s", this is required.' % attr)
    
    try:
        import settings
    except ImportError:
        raise HotDjangoError('settings module not found')
    else:
        _check_settings_attr('DISPLAY_APPS')
        _check_settings_attr('SITE_TITLE')
        _check_settings_attr('SITE_ROOT')
        get_display_apps()

"""
Only run validate if import is during the initial validate.
Will need changing for future version of Django.
"""
if any('validation.py' in line for line in traceback.format_stack()):
    validate()