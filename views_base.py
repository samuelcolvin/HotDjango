from django.shortcuts import redirect
import django.views.generic as generic
import settings
import public
from django.core.urlresolvers import reverse
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.template.response import TemplateResponse

HOT_VIEW_SETTINGS = {'viewname': public.HOT_URL_NAME, 
                    'args2include': [True, True], 
                    'base_name': 'Model Display', 
                    'menu_active': public.HOT_URL_NAME}
    
class ViewBase(object):
    side_menu = True
    all_auth_permitted = False
    all_permitted = False
    menu_active = None
    show_crums = True
    _apps, _extra_render = public.get_display_apps()
    
    def get(self, request, *args, **kw):
        try:
            self.setup_context(**kw)
        except ObjectDoesNotExist:
            print 'ObjectDoesNotExist'
            return redirect(reverse('permission_denied'))
        if not self.allowed:
            return redirect(reverse('permission_denied'))
        return super(ViewBase, self).get(request, *args, **kw)
    
    @property
    def allowed(self):
        return self.all_permitted or \
            (self.all_auth_permitted and self.request.user.is_active) or \
            public.is_allowed_hot(self.request.user, self._disp_model.permitted_groups)
    
    def setup_context(self, **kw):
        if not hasattr(self, 'view_settings'):
            self.view_settings = HOT_VIEW_SETTINGS.copy()
            if hasattr(settings, 'HOT_VIEW_SETTINGS'):
                self.view_settings.update(settings.HOT_VIEW_SETTINGS)
        self.viewname = self.view_settings['viewname']
        self._disp_model = None
        self._app_name = kw.get('app', None)
        self._model_name = kw.get('model', None)
        self._item_id = kw.get('id', None)
        self._disp_model = self._get_model()
        self._plural_t = get_plural_name(self._disp_model)
        self._single_t = get_single_name(self._disp_model)
        if self._item_id not in [None, 'None']:
            sfilter = self.filter
            if sfilter is None:
                raise ObjectDoesNotExist('filter is None')
            else:
                self._item = sfilter.get(id = int(self._item_id))
        if not hasattr(self, '_context'):
            self._context={}
        if self._extra_render:
            self._context.update(self._extra_render(self.request))
        self.generate_side_menu()
        self.create_crums()
        menu_active = self.view_settings['menu_active']
        if self.menu_active:
            menu_active = self.menu_active
            
        self.request.session['view_settings'] = {'viewname': self.viewname, 'menu_active': menu_active}
        self._context.update(basic_context(self.request, menu_active))
        
    @property
    def filter(self):
        if self._disp_model.get_queryset is not None:
            return self._disp_model.get_queryset(self.request)
        else:
            return self.default_queryset
    
    @property
    def default_queryset(self):
        return self._disp_model.model.objects.all()
    
    def _get_default_app_model(self):
        for app_name in self._apps:
            models =[(model_name, self._apps[app_name][model_name].index)\
                      for model_name in self._apps[app_name]]
            models = sorted(models, key = lambda x: x[1])
            for model_name, _ in models:
                model = self._apps[app_name][model_name]
                if model.display and public.is_allowed_hot(self.request.user, model.permitted_groups):
                    self._app_name = app_name
                    self._model_name = model_name
                    return
        self._app_name = settings.DISPLAY_APPS[0]
        self._model_name = self._apps[self._app_name].keys()[0]
                                
    def _get_model(self):
        if self._app_name is None and self._model_name is None:
            self._get_default_app_model()
        if self._app_name is None:
            for app_name, app in self._apps.items():
                if self._model_name in app:
                    self._app_name = app_name
                    break
        try:
            return self._apps[self._app_name][self._model_name]
        except KeyError:
            raise Http404('ERROR: %s.%s not found' % (self._app_name, self._model_name))
    
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
        if not self.side_menu:
            return
        side_menu = []
        active = None
        if self._disp_model is not None: active = self._disp_model.__name__
        for app_name in self._apps:
            for model_name in self._apps[app_name]:
                if hasattr(self, 'side_menu_items') and model_name not in self.side_menu_items:
                    continue
                model = self._apps[app_name][model_name]
                if model.display and public.is_allowed_hot(self.request.user, model.permitted_groups):
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
        return table(queryset, 
                     viewname=self.viewname, 
                     reverse_args=self.args_base(), 
                     apps=self._apps, 
                     use_model_arg = use_model_arg,
                     request = self.request)

class TemplateBase(ViewBase, generic.TemplateView):
    pass

class TemplateResponseForbidden(TemplateResponse):
    status_code = 403

class PermissionDenied(TemplateBase):
    template_name = 'hot/simple_message.html'
    response_class = TemplateResponseForbidden
    side_menu = False
    all_permitted = True
    show_crums = False
    
    def get(self, request, *args, **kw):
        self.setup_context(**kw)
        return super(PermissionDenied, self).get(request, *args, **kw)

    def get_context_data(self, **kw):
        self._context['main_message'] = 'You do not have Permission to view this page.'
        return self._context
    
    def create_crums(self):
        pass
    
    def setup_context(self, **kw):
        if 'view_settings' in self.request.session:
            self.view_settings = HOT_VIEW_SETTINGS.copy()
            self.view_settings.update(self.request.session['view_settings'])
        super(PermissionDenied, self).setup_context(**kw)
        if 'crums' in self._context:
            del self._context['crums']
            
class ModelEditView(ViewBase, 
                    generic.edit.TemplateResponseMixin, 
                    generic.edit.ModelFormMixin, 
                    generic.edit.ProcessFormView):
    app = None
    model = None
    object = None
    alert_all_errors = False
    template_name = 'hot/add_edit.html'
    
    def post(self, request, *args, **kw):
        self.setup_context(**kw)
        return super(ModelEditView, self).post(request, *args, **kw)
    
    def setup_context(self, **kw):
        kw['app'] = self.app
        kw ['model'] = self.model
        super(ModelEditView, self).setup_context(**kw)
        if self._item_id is not None:
            self.object = self._item

    def form_invalid(self, form):
        self.error_log('Form not Valid')
        general_errors = form.non_field_errors()
        if len(general_errors) > 0:
            self.error_log(', '.join(general_errors))
        if self.alert_all_errors:
            for name, errors in form.errors.items():
                if name != '__all__':
                    self.error_log('%s: %s' % (name, ', '.join(errors)))
        self._context.update(set_messages(self.request))
        return self.render_to_response(self.get_context_data(form=form))
    
    def success_log(self, line):
        if not 'success' in self.request.session:
            self.request.session['success'] = []
        self.request.session['success'].append(line)
     
    def error_log(self, line):
        if not 'errors' in self.request.session:
            self.request.session['errors'] = []
        self.request.session['errors'].append(line)
    
    def get_context_data(self, **kw):
        self._context.update(super(ModelEditView, self).get_context_data(**kw))
        return self._context
    
    def form_valid(self, form):
        form.request = self.request
        self.object = form.save()
        self.success_log('%s saved' % self._disp_model.model_name)
        return self.success_url
    
    @property
    def success_url(self):
        raise NotImplementedError('You need to add a success_url property')

def get_plural_name(dm):
    return  unicode(dm.model._meta.verbose_name_plural)

def get_single_name(dm):
    return  unicode(dm.model._meta.verbose_name)

def is_mobile(request):
    ua = request.META['HTTP_USER_AGENT'].lower()
    return any(phone_os in ua for phone_os in ('iphone', 'android', 'bb10'))

def basic_context(request, menu_active = None):
    if menu_active is not None:
        request.session['menu_active'] = menu_active
    elif 'menu_active' in request.session:
        menu_active = request.session['menu_active']
    context = set_messages(request)
    context['base_template'] = 'hot/page_base.html'
    if hasattr(settings, 'PAGE_BASE'):
        context['base_template'] = settings.PAGE_BASE
    if hasattr(settings, 'INDEX_URL_NAME'):
        context['index'] = settings.INDEX_URL_NAME
    raw_menu = []
    if hasattr(settings, 'MAIN_MENU'):
        for item in settings.MAIN_MENU:
            if 'groups' in item:
                if public.is_allowed_hot(request.user, permitted_groups=item['groups']):
                    raw_menu.append(item)
            else:
                raw_menu.append(item)
    if request.user.is_staff:
        raw_menu.append({'url': 'admin:index', 'name': 'Staff Admin', 'glyph':'wrench'})
    top_menu = []
    for item in raw_menu:
        menu_item = {'url': reverse(item['url']), 'name': item['name']}
        menu_item['glyph'] = item.get('glyph')
        menu_item['title'] = item.get('title')
        if item['url'] == menu_active:
            menu_item['class'] = 'active'
        top_menu.append(menu_item)
    context['top_menu'] = top_menu
        
    context['site_title'] = settings.SITE_TITLE
    if hasattr(settings, 'SITE_LOGO'):
        context['site_logo'] = settings.SITE_LOGO
    return context

def set_messages(request):
    context = {}
    if 'info' in request.session:
        info = request.session.pop('info')
        context['info'] = (info, [info])[isinstance(info, basestring)]
    if 'success' in request.session:
        success = request.session.pop('success')
        context['success'] = (success, [success])[isinstance(success, basestring)]
    if 'errors' in request.session:
        errors = request.session.pop('errors')
        context['errors'] = (errors, [errors])[isinstance(errors, basestring)]
    return context
