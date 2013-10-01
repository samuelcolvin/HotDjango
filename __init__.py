import settings
import inspect, json
import HotDjango
import django_tables2 as tables
from django_tables2.utils import A


class _MetaModelDisplay(HotDjango._MetaBaseDisplayModel):
    def __init__(cls, *args, **kw):
        if cls.__name__ == 'ModelDisplay':
            return
        assert hasattr(cls, 'model'), '%s is missing a model, all display models must have a model attribute.' % cls.__name__
        cls.model_name = cls.model.__name__
        if hasattr(cls, 'DjangoTable'):
            if hasattr(cls.DjangoTable, 'Meta'):
                cls.DjangoTable.Meta.model = cls.model
        HotDjango._MetaBaseDisplayModel.__init__(cls, *args, **kw)

class ModelDisplay(HotDjango.BaseDisplayModel):
    __metaclass__ = _MetaModelDisplay
    extra_funcs = []
    extra_fields = {}
    extra_models = {}
    attached_tables = []
    exclude = []
    show_crums = True
    display = True
    addable = True
    editable = True
    deletable = True
    form = None
    formset_model = None
    queryset= None
    
class ModelDisplayMeta:
    orderable = False
    attrs = {'class': 'table table-bordered table-condensed'}
    per_page = 100

def get_display_apps():
    return HotDjango.get_all_apps()

class _AppEncode(json.JSONEncoder):
    def default(self, obj):
        if inspect.isclass(obj):
            return dir(obj)
        return json.JSONEncoder.default(self, dir(obj))
    
class Logger:
    def __init__(self):
        self._log = []
        
    def addline(self, line):
        self._log.append(line)
        
    def get_log(self):
        return self._log