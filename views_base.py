from django.shortcuts import render, redirect
import django.views.generic as generic
import django.core.urlresolvers
import settings
import SkeletalDisplay
    
def reverse(name, args=[], kwargs={}):
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            args[i] = arg.replace('.','__')
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs[key]=value.replace('.','__')
    return django.core.urlresolvers.reverse(name, args=args, kwargs=kwargs)
    
class ViewBase():
    def dispatch(self, request, *args, **kwargs):
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated():
            return redirect(reverse('login'))
        return super(ViewBase, self).dispatch(request, *args, **kwargs)
    
    def setup_context(self, **kw):
        self._apps = SkeletalDisplay.get_display_apps()
        self._disp_model = None
        self._top_active = None
        self._app_name = kw.get('app', None)
        self._model_name = kw.get('model', None)
        self._item_id = kw.get('id', None)
        if None not in (self._app_name, self._model_name):
            self._disp_model = self._find_model(self._app_name, self._model_name)
            self._plural_t = get_plural_name(self._disp_model)
            self._single_t = self._disp_model.model._meta.verbose_name.title()
            if self._item_id is not None:
                self._item = self._disp_model.model.objects.get(id = int(self._item_id))
        
        if not hasattr(self, '_context'):
            self._context={}
        self._context['menu'] = self._side_menu()
        self._context.update(basic_context(self.request, self._top_active))

    
    def _find_model(self, app_name, model_name):
        try:
            return self._apps[app_name][model_name]
        except:
            raise Exception('ERROR: %s.%s not found' % (app_name, model_name))
    
    def _set_crums(self, set_to = None, add = None):
        if set_to is not None:
            self.request.session['crums'] = set_to
        if add is not None:
            if add[0] != self.request.session['crums'][-1]:
                self.request.session['crums'] += add
        return self.request.session['crums']
    
    def _side_menu(self):
        side_menu = []
        active = None
        if self._disp_model is not None: active = self._disp_model.__name__
        for app_name in self._apps:
            for model_name in self._apps[app_name]:
                model = self._apps[app_name][model_name]
                if model.display:
                    cls = ''
                    if model_name == active: cls = 'open'
                    side_menu.append({'url': reverse('display_model', args=[app_name, model_name]), 
                                    'name': get_plural_name(model), 'class': cls, 'index': model.index})
        side_menu = sorted(side_menu, key=lambda d: d['index'])
        return side_menu

class TemplateBase(generic.TemplateView, ViewBase):
    
    def setup_context(self, **kw):
        super(TemplateBase, self).setup_context(**kw)

def get_plural_name(dm):
    return  unicode(dm.model._meta.verbose_name_plural)

def basic_context(request, top_active = None):
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

    top_menu = []
    for item in settings.TOP_MENU:
        menu_item = {'url': reverse(item['url']), 'name': item['name']}
        if item['url'] == top_active:
            menu_item['class'] = 'active'
        top_menu.append(menu_item)
    if request.user.is_staff:
        top_menu.append({'url': reverse('admin:index'), 'name': 'Admin'})
    else:
        top_menu.append({'url': reverse('logout'), 'name': 'Logout'})
    context['site_title'] = settings.SITE_TITLE
    context['top_menu'] = top_menu
    return context














