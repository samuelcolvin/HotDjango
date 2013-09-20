import settings
import inspect, json
import HotDjango


class _MetaModelDisplay(HotDjango._MetaBaseDisplayModel):
    def __init__(cls, *args, **kw):
        HotDjango._MetaBaseDisplayModel.__init__(cls, *args, **kw)
        if not (hasattr(cls,'HotTable') or hasattr(cls,'DjangoTable')):
            return
        assert hasattr(cls, 'model'), '%s is missing a model, all display models must have a model attribute at %s' % (cls.__name__, cls.__file__)
        cls.model_name = cls.model.__name__
        if hasattr(cls, 'DjangoTable'):
            if hasattr(cls.DjangoTable, 'Meta'):
                cls.DjangoTable.Meta.model = cls.model
            else:
                cls.DjangoTable.Meta = type('Meta', (), {'model': cls.model})

class ModelDisplay(HotDjango.BaseDisplayModel):
    __metaclass__ = _MetaModelDisplay
    extra_funcs = []
    tables = []
    display = True
    
class ModelDisplayMeta:
    orderable = False
    attrs = {'class': 'table table-bordered table-condensed'}
    per_page = 100


def get_display_apps():
    all_apps = HotDjango.get_all_apps()
    for app in all_apps.values():
        for model_name in app.keys():
            if not hasattr(app[model_name], 'DjangoTable'):
                del app[model_name]
        if len(app) == 0:
            del app
    return all_apps

class _AppEncode(json.JSONEncoder):
    def default(self, obj):
        if inspect.isclass(obj):
            return dir(obj)
        return json.JSONEncoder.default(self, dir(obj))
    
class Logger:
    def __init__(self):
        self._log = ''
        
    def addline(self, line):
        self._log +='<p>%s</p>\n' % line
        
    def get_log(self):
        return self._log