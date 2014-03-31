from django.shortcuts import redirect
import django.views.generic as generic
import settings
import SkeletalDisplay, HotDjango
from django.core.urlresolvers import reverse

SK_VIEW_SETTINGS = {'viewname': 'sk', 'args2include': [True, True], 'base_name': 'Model Display', 'top_active': 'sk'}
    
class ViewBase(object):
    side_menu = True
    all_auth_permitted = False
    extra_permission_check = None
    top_active = None
    show_crums = True
    
    def get(self, request, *args, **kw):
        self.setup_context(**kw)
        if not self.check_permissions():
            return redirect(reverse('permission_denied'))
        return super(ViewBase, self).get(request, *args, **kw)
    
    def check_permissions(self):
        if self.extra_permission_check:
            extra = self.extra_permission_check()
            if extra is True:
                return True
            elif extra is False:
                return False
        if self.all_auth_permitted or self.is_allowed():
            return True
        return False
    
    def setup_context(self, **kw):
        if not hasattr(self, 'view_settings'):
            self.view_settings = SK_VIEW_SETTINGS.copy()
            if hasattr(settings, 'SK_VIEW_SETTINGS'):
                self.view_settings.update(settings.SK_VIEW_SETTINGS)
        self.viewname = self.view_settings['viewname']
        self._apps, self._extra_render = SkeletalDisplay.get_display_apps()
        self._disp_model = None
        self._app_name = kw.get('app', None)
        self._model_name = kw.get('model', None)
        self._item_id = kw.get('id', None)
        if self._app_name is None and self._model_name is None:
            self._get_default_names()
        self._disp_model = self._get_model(self._app_name, self._model_name)
        self._plural_t = get_plural_name(self._disp_model)
        self._single_t = get_single_name(self._disp_model)
        if self._item_id is not None:
            self._item = self._disp_model.model.objects.get(id = int(self._item_id))
        if not hasattr(self, '_context'):
            self._context={}
        if self._extra_render:
            self._context.update(self._extra_render(self.request))
        self.create_crums()
        if self.side_menu:
            self.generate_side_menu()
        top_active = self.view_settings['top_active']
        if self.top_active:
            top_active = self.top_active
            
        self.request.session['view_settings'] = {'viewname': self.viewname, 'top_active': top_active}
        self._context.update(basic_context(self.request, top_active))
        
    def is_allowed(self):
        return HotDjango.is_allowed_hot(self.request.user)
    
    def _get_default_names(self):
        self._app_name = [app_name for app_name in self._apps.keys() if app_name != 'sk'][0]
        self._model_name = sorted(self._apps[self._app_name].values(), key=lambda model: model.index)[0].__name__
    
    def _get_model(self, app_name, model_name):
        try:
            return self._apps[app_name][model_name]
        except:
            raise Exception('ERROR: %s.%s not found' % (app_name, model_name))
    
    def set_links(self):
        links =[]
        if self._disp_model.addable:
            links.append({'url': reverse('add_item', args=[self._app_name, self._model_name]), 'name': 'Add ' + self._single_t})
        return links
    
    def set_crums(self, set_to = None, add = None):
        if not self.show_crums:
            return
        if not self._disp_model.show_crums:
            if 'crums' in self.request.session:
                del self.request.session['crums']
            return
        if set_to is not None:
            self.request.session['crums'] = set_to
        if add is not None:
            if 'crums' not in self.request.session or len(self.request.session['crums']) == 0:
                self.request.session['crums'] = add
            elif add[0] != self.request.session['crums'][-1]:
                self.request.session['crums'] += add
        self._context['crums'] = self.request.session['crums']
        
    def create_crums(self):
        if self._disp_model is not None and self._disp_model.display:
            crums=[{'url': reverse(self.viewname), 'name': self.view_settings['base_name']}]
            crums.append({'url': reverse(self.viewname, args=self.args_base(model=self._model_name)), 'name' : self._plural_t})
            self.set_crums(set_to = crums)

    def generate_side_menu(self):
        side_menu = []
        active = None
        if self._disp_model is not None: active = self._disp_model.__name__
        for app_name in self._apps:
            for model_name in self._apps[app_name]:
                if hasattr(self, 'side_menu_items') and model_name not in self.side_menu_items:
                    continue
                model = self._apps[app_name][model_name]
                if model.display:
                    cls = ''
                    if model_name == active: cls = 'open'
                    side_menu.append({'url': reverse(self.viewname, args=self.args_base(app_name, model_name)), 
                                    'name': get_plural_name(model), 'class': cls, 'index': model.index})
        side_menu = sorted(side_menu, key=lambda d: d['index'])
        self._context['side_menu'] = side_menu
    
    def args_base(self, app=None, model=None):
        if app is None:
            app = self._app_name
        args = []
        if self.view_settings['args2include'][0]:
            args = [app]
        if model is not None and self.view_settings['args2include'][1]:
            args.append(model)
        return args
    
    def generate_table(self, table, queryset):
        use_model_arg = True
        if not self.view_settings['args2include'][1]:
            use_model_arg = False
        return table(queryset, viewname=self.viewname, reverse_args=self.args_base(), apps=self._apps, use_model_arg = use_model_arg)

class TemplateBase(ViewBase, generic.TemplateView):
    pass

class PermissionDenied(ViewBase, generic.TemplateView):
    template_name = 'sk_simple_message.html'
    side_menu = False
    all_auth_permitted = True
    show_crums = False
    
    def get(self, request, *args, **kw):
        self.setup_context(**kw)
        return super(PermissionDenied, self).get(request, *args, **kw)

    def get_context_data(self, **kw):
        self._context['main_message'] = 'You do not have Permission to view this page.'
        return self._context
    
    def setup_context(self, **kw):
        if 'view_settings' in self.request.session:
            self.view_settings = SK_VIEW_SETTINGS.copy()
            self.view_settings.update(self.request.session['view_settings'])
        super(PermissionDenied, self).setup_context(**kw)
        del self._context['crums']

def get_plural_name(dm):
    return  unicode(dm.model._meta.verbose_name_plural)

def get_single_name(dm):
    return  unicode(dm.model._meta.verbose_name)

def basic_context(request, top_active = None):
    if top_active is not None:
        request.session['top_active'] = top_active
    elif 'top_active' in request.session:
        top_active = request.session['top_active']
    context = {}
    if 'message' in request.session:
        context['info'] = request.session.pop('info')
    if 'success' in request.session:
        context['success'] = request.session.pop('success')
    if 'errors' in request.session:
        context['errors'] = request.session.pop('errors')
    context['base_template'] = 'sk_page_base.html'
    if hasattr(settings, 'PAGE_BASE'):
        context['base_template'] = settings.PAGE_BASE
    raw_menu = []
    for item in settings.TOP_MENU:
        if 'groups' in item:
            if HotDjango.is_allowed_hot(request.user, permitted_groups=item['groups']):
                raw_menu.append(item)
        else:
            raw_menu.append(item)
    if request.user.is_staff:
        raw_menu.append({'url': 'admin:index', 'name': 'Staff Admin', 'glyph':'wrench'})
    top_menu = []
    for item in raw_menu:
        menu_item = {'url': reverse(item['url']), 'name': item['name']}
        if 'glyph' in item:
            menu_item['glyph'] = item['glyph']
        if item['url'] == top_active:
            menu_item['class'] = 'active'
        top_menu.append(menu_item)
    
    context['top_menu'] = top_menu
    context['site_title'] = settings.SITE_TITLE
    return context











