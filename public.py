from rest_framework import serializers
import inspect, json, imp, os
import settings
import django_tables2 as tables
import django_tables2.tables as tables2_tables
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django_tables2.utils import A
from django.core.urlresolvers import reverse
import importlib
from datetime import datetime as dtdt
from datetime import timedelta
import pytz

HOT_URL_NAME = 'hot'

class HotDjangoError(Exception):
    pass

HOT_ID_IN_MODEL_STR = False
if hasattr(settings, 'HOT_ID_IN_MODEL_STR'):
    HOT_ID_IN_MODEL_STR = settings.HOT_ID_IN_MODEL_STR

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

def get_display_apps():
    importer = lambda m: importlib.import_module('%s.display' % m)
    apps={}
    extra_render = None
    for app_name in settings.DISPLAY_APPS:
        disp_path = os.path.join(app_name, 'display.py')
        if not os.path.exists(os.path.join(settings.SITE_ROOT, disp_path)):
            raise HotDjangoError('%s does not exist' % disp_path)
        app_display = importer(app_name)
        if hasattr(app_display, 'AppName'):
            app_name = app_display.AppName
        apps[app_name] = {}
        if extra_render == None:
            extra_render = getattr(app_display, 'extra_render', None)
        for ob_name in dir(app_display):
            ob = getattr(app_display, ob_name)
            if inherits_from(ob, 'ModelDisplay'):
                apps[app_name][ob_name] = ob
                apps[app_name][ob_name]._app_name = app_name
    return apps, extra_render

def get_rest_apps():
    display_apps, _ = get_display_apps()
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
        if not hasattr(settings, 'HOT_PERMITTED_GROUPS'):
            return False
        permitted_groups = settings.HOT_PERMITTED_GROUPS
    if permitted_groups == 'all-anon':
        return True
    if permitted_groups == 'all-users':
        return not user.is_anonymous()
    for group in user_groups(user):
        if group in permitted_groups:
            return True
    return False

def user_groups(user):
    return user.groups.all().values_list('name', flat=True)
    
class SelfLinkColumn(tables.Column):
    def render(self, value, **kw):
        record = kw['record']
        table = kw['table']
        if None in (table.viewname, table.reverse_args_base):
            return value
        else:
            disp_model_name = table.Meta.display_model_name
            url = table._url_base.replace('__mod_name__', disp_model_name).replace('1234567', str(record.id))
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
    
class ModelDisplayMeta(object):
    orderable = False
    attrs = {'class': 'table table-bordered table-condensed'}
    per_page = 100
    
class _MetaTable(tables2_tables.DeclarativeColumnsMetaclass):
    def __new__(mcs, name, bases, attrs):
        if '__metaclass__' not in attrs and 'Meta' not in attrs:
            attrs['Meta'] = type('Meta', (ModelDisplayMeta,), {})
        return tables2_tables.DeclarativeColumnsMetaclass.__new__(mcs, name, bases, attrs)
    
class Table(tables.Table):   
    __metaclass__ = _MetaTable 
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

class _MetaModelDisplay(type):
    def __init__(cls, name, parents, extra, **kw):
        if cls.__name__ == 'ModelDisplay':
            type.__init__(cls, name, parents, extra, **kw)
            return
        if not hasattr(cls, 'model'):
            app_name = extra['__module__'].split('.')[0]
            app = __import__(app_name, globals(), locals(), ['models'], -1)
            c_name = cls.__name__
            if not hasattr(app.models, c_name):
                raise HotDjangoError('%s is missing a model, and no model in %s has that name' % (c_name, app_name))
            cls.model = getattr(app.models, c_name)
        cls.model_name = cls.model.__name__
        
        if not hasattr(cls, 'DjangoTable'):
            cls.DjangoTable = type('DjangoTable', (Table,), {})
        
        cls.DjangoTable.Meta.display_model_name = cls.__name__
        if len(cls.DjangoTable.base_columns) == 0:
            cls.DjangoTable.base_columns['__unicode__'] = SelfLinkColumn(verbose_name='Name')
            
        if hasattr(cls, 'HotTable'):
            dft_fields = ['id']
            name_missing_e = None
            if 'name' in cls.model._meta.get_all_field_names():
                dft_fields.append('name')
            else:
                name_missing_e = HotDjangoError('%s has no "name" field and fields is not defined in HotTable' % cls.model.__name__)
            if hasattr(cls.HotTable, 'Meta'):
                cls.HotTable.Meta.model = cls.model
                if not hasattr(cls.HotTable.Meta, 'fields'):
                    if name_missing_e: raise name_missing_e
                    cls.HotTable.Meta.fields =  dft_fields
        type.__init__(cls, name, parents, extra, **kw)

class ModelDisplay(object):
    verbose_names = {}
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
    get_queryset = None
    filter_options = None
    index = 100
    models2link2 = None

class _AppEncode(json.JSONEncoder):
    def default(self, obj):
        if inspect.isclass(obj):
            return dir(obj)
        return json.JSONEncoder.default(self, dir(obj))
    
def find_disp_model(apps, to_find, this_app_name = None):
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
    
class _base_time_filter(object):
    def __init__(self, field_name, suffix = '__gt'):
        self._key = field_name + suffix
        
    def _kw(self, filter_value):
        return {self._key: filter_value}

def _today():
    return dtdt.now().replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=pytz.utc)

class TimeFilters:
        
    @staticmethod
    class today(_base_time_filter):
        def __call__(self, qs):
            return qs.filter(**self._kw(_today()))
        
    @staticmethod
    class this_week(_base_time_filter):
        def __call__(self, qs):
            n = _today()
            mon = n - timedelta(days=n.weekday())
            return qs.filter(**self._kw(mon))
    
    @staticmethod
    class recent(_base_time_filter):
        def __init__(self, days, *args, **kw):
            self._days = days
            super(TimeFilters.recent, self).__init__(*args, **kw)
            
        def __call__(self, qs):
            recent = dtdt.today()-timedelta(days=self._days)
            recent = recent.replace(tzinfo=pytz.utc)
            return qs.filter(**self._kw(recent))
