import settings
import inspect, json
import HotDjango
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django_tables2.utils import A
from django.core.urlresolvers import reverse


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
    
class Table(tables.Table):
    def __init__(self, *args, **kw):
        self.viewname= kw.pop('viewname', None)
        self.reverse_args_base = kw.pop('reverse_args', None)
        self.apps = kw.pop('apps', None)
        self.use_model_arg = kw.pop('use_model_arg', True)
        if self.apps is None:
            self.apps = get_display_apps()
        super(Table, self).__init__(*args, **kw)
    
class SelfLinkColumn(tables.Column):
    def render(self, value, **kw):
        record = kw['record']
        table = kw['table']
        if None in (table.viewname, table.reverse_args_base):
            return value
        else:
            model_name = find_model(table.apps, record.__class__.__name__)[1]
            args = table.reverse_args_base[:]
            if table.use_model_arg:
                args.append(model_name)
            args.append(record.id)
            url = reverse(table.viewname, args=args)
            return mark_safe('<a href="%s">%s</a>' % (url, value))

def get_display_apps():
    return HotDjango.get_all_apps()

class _AppEncode(json.JSONEncoder):
    def default(self, obj):
        if inspect.isclass(obj):
            return dir(obj)
        return json.JSONEncoder.default(self, dir(obj))
    
def find_model(apps, to_find, this_app_name = None):
    if this_app_name is not None:
        for model_name in apps[this_app_name].keys():
            if model_name == to_find:
                return (this_app_name, model_name)
    for app_name, app in apps.items():
        if this_app_name is not None and this_app_name == app_name:
            continue
        for model_name in app.keys():
            if model_name == to_find:
                return (app_name, model_name)
    return None

class Logger:
    def __init__(self):
        self._log = []
        
    def addline(self, line):
        self._log.append(line)
        
    def get_log(self):
        return self._log