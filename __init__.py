<<<<<<< HEAD
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
    index = 100
    models2link2 = None
    
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
        
        url_args = list(self.reverse_args_base)
        if self.use_model_arg:
            url_args.append('__mod_name__')
        url_args.append('1234567')
        self._url_base = reverse(self.viewname, args=url_args)
        
        if self.apps is None:
            self.apps, _ = get_display_apps()
        super(Table, self).__init__(*args, **kw)
    
class SelfLinkColumn(tables.Column):
    def render(self, value, **kw):
        record = kw['record']
        table = kw['table']
        if None in (table.viewname, table.reverse_args_base):
            return value
        else:
            model_name = find_model(table.apps, record.__class__.__name__)[1]
            url = table._url_base.replace('__mod_name__', model_name).replace('1234567', str(record.id))
#             args = table.reverse_args_base[:]
#             if table.use_model_arg:
#                 args.append(model_name)
#             args.append(record.id)
#             url = reverse(table.viewname, args=args)
            return mark_safe('<a href="%s">%s</a>' % (url, value))
    
class SterlingPriceColumn(tables.Column):
    def render(self, value):
        if value>1000:
            return '{:,}'.format(value)
        elif value>10:
            return '%0.2f' % value
        else:
            string = '%0.3f' % value
            if string.endswith('0'):
                return string[:-1]
            return string


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
=======
from rest_framework import serializers
import inspect, settings

__version__ = '0.1'

HOT_ID_IN_MODEL_STR = False
if hasattr(settings, 'HOT_ID_IN_MODEL_STR'):
    HOT_ID_IN_MODEL_STR = settings.HOT_ID_IN_MODEL_STR

class _MetaBaseDisplayModel(type):
    def __init__(cls, *args, **kw):
        type.__init__(cls, *args, **kw)
        if cls.__name__ in ('BaseDisplayModel', 'ModelDisplay'):
            return
        assert hasattr(cls, 'model'), '%s is missing a model, all display models must have a model attribute' % cls.__name__
        cls.model_name = cls.model.__name__
        if hasattr(cls, 'HotTable'):
            if hasattr(cls.HotTable, 'Meta'):
                cls.HotTable.Meta.model = cls.model
            else:
                cls.HotTable.Meta = type('Meta', (), {'model': cls.model})

class BaseDisplayModel:
    __metaclass__ = _MetaBaseDisplayModel
    verbose_names = {}

class IDNameSerialiser(serializers.RelatedField):
    read_only = False
    def __init__(self, model, *args, **kwargs):
        self._model = model
        super(IDNameSerialiser, self).__init__(*args, **kwargs)
        
    def to_native(self, item):
        if hasattr(item, 'hot_name'):
            name = item.hot_name()
        else:
            name = str(item)
        if HOT_ID_IN_MODEL_STR:
            return name
        else:
            return '%d: %s' % (item.id, name)
    
    def from_native(self, item):
        try:
            dj_id = int(item)
        except:
            dj_id = int(item[:item.index(':')])
        return self._model.objects.get(id = dj_id)

class ChoiceSerialiser(serializers.Serializer):
    read_only = False
    def __init__(self, choices, *args, **kwargs):
        self._choices = choices
        super(ChoiceSerialiser, self).__init__(*args, **kwargs)
        
    def to_native(self, item):
        return next(choice[1] for choice in self._choices if choice[0] == item)
    
    def from_native(self, item):
        return next(choice[0] for choice in self._choices if choice[1] == item)
    
class ModelSerialiser(serializers.ModelSerializer):
    def save(self, *args, **kwargs):
        if hasattr(self.object, 'hotsave_enabled') and self.object.hotsave_enabled:
            kwargs['hotsave'] = True
        super(ModelSerialiser, self).save(*args, **kwargs)


def get_verbose_name(dm, field_name):
    dj_field = dm.model._meta.get_field_by_name(field_name)[0]
    if hasattr(dj_field, 'verbose_name'):
        return dj_field.verbose_name
    elif field_name in dm.verbose_names:
        return dm.verbose_names[field_name]
    return field_name

def get_all_apps():
    importer = lambda m: __import__(m, globals(), locals(), ['display'], -1)
    display_modules = map(importer, settings.DISPLAY_APPS)
    apps={}
    extra_render = None
    for app in display_modules:
        app_name = app.display.app_name
        apps[app_name] = {}
        if extra_render == None:
            extra_render = getattr(app.display, 'extra_render', None)
        for ob_name in dir(app.display):
            ob = getattr(app.display, ob_name)
            if inherits_from(ob, 'BaseDisplayModel'):
                apps[app_name][ob_name] = ob
                apps[app_name][ob_name]._app_name = app_name
    return apps, extra_render

def get_rest_apps():
    display_apps, _ = get_all_apps()
    for disp_app in display_apps.values():
        for model_name in disp_app.keys():
            if not hasattr(disp_app[model_name], 'HotTable'):
                del disp_app[model_name]
        if len(disp_app) == 0:
            del disp_app
    return display_apps

def inherits_from(child, parent_name):
    if inspect.isclass(child):
        if parent_name in [c.__name__ for c in inspect.getmro(child)[1:]]:
            return True
    return False

def is_allowed_hot(user, permitted_groups=None):
    if user.is_staff:
        return True
    if permitted_groups is None:
        permitted_groups = settings.HOT_PERMITTED_GROUPS
        if permitted_groups is 'all':
            return True
    for group in user.groups.all().values_list('name', flat=True):
        if group in permitted_groups:
            return True
    return False
>>>>>>> handsontable-original
