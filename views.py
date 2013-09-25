from django.template import RequestContext
from django.shortcuts import render_to_response
import django.views.generic as generic
import django.core.urlresolvers
from django.utils.encoding import smart_str

from datetime import datetime
import settings
import markdown2
from django.db import models
from django_tables2 import RequestConfig

from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
import SkeletalDisplay

def reverse(name, args=[], kwargs={}):
	for i, arg in enumerate(args):
		if isinstance(arg, str):
			args[i] = arg.replace('.','__')
	for key, value in kwargs.items():
		if isinstance(value, str):
			kwargs[key]=value.replace('.','__')
	return django.core.urlresolvers.reverse(name, args=args, kwargs=kwargs)

class TemplateBase(generic.TemplateView):
	def get(self, request, *args, **kw):
		self._request = request
		context = self.get_context_data(**kw)
		return self.render_to_response(context)
	
	def setup_context(self, **kw):
		self._apps = SkeletalDisplay.get_display_apps()
		if 'message' in self._request.session:
			self._content['info'] = self._request.session.pop('info')
		if 'success' in self._request.session:
			self._content['success'] = self._request.session.pop('success')
		if 'error' in self._request.session:
			self._content['error'] = self._request.session.pop('error')
		self._disp_model = None
		self._top_active = None
			
		self._app_name = kw.get('app', None)
		self._model_name = kw.get('model', None)
		if None not in (self._app_name, self._model_name):
			self._disp_model = self._find_model(self._app_name, self._model_name)
			self._plural_t = get_plural_name(self._disp_model)
			self._single_t = self._disp_model.model._meta.verbose_name.title()
		
		self._context = super(TemplateBase, self).get_context_data(**kw)
		
		self._context['base_template'] = 'sk_page_base.html'
		if hasattr(settings, 'PAGE_BASE'):
			self._context['base_template'] = settings.PAGE_BASE
	
	def generate_base(self, generate_side_menu=True):
		side_menu = default_side_menu(disp_model=self._disp_model, apps=self._apps)
		self._context.update(base_context(self.request, side_menu, top_active=self._top_active))
	
	def _find_model(self, app_name, model_name):
		try:
			return self._apps[app_name][model_name]
		except:
			raise Exception('ERROR: %s.%s not found' % (app_name, model_name))
	
	def _set_crums(self, set_to = None, add = None):
		if set_to is not None:
			self._request.session['crums'] = set_to
		if add is not None:
			if add[0] != self._request.session['crums'][-1]:
				self._request.session['crums'] += add
		return self._request.session['crums']

class Index(TemplateBase):
	template_name = 'sk_index.html'
	
	def get_context_data(self, **kw):
		self.setup_context(**kw)
		self._context['title'] = settings.SITE_TITLE
		self.generate_base()
		return self._context

class DisplayIndex(TemplateBase):
	template_name = 'sk_display_index.html'
	
	def get_context_data(self, **kw):
		self.setup_context(**kw)
		self._context['title'] = settings.SITE_TITLE
		self._top_active = 'display_index'
		self.generate_base()
		return self._context

class DisplayModel(TemplateBase):
	template_name = 'sk_model_display.html'
	
	def get_context_data(self, **kw):
		self.setup_context(**kw)
		links = [{'url': reverse('add_item', args=[self._app_name, self._model_name]), 'name': 'Add ' + self._single_t},
				{'url': reverse('hot_edit', kwargs={'app': self._app_name, 'model': self._model_name}), 'name': 'Mass Edit'}]
		crums = self._set_crums(set_to = [{'url': reverse('display_index'), 'name': 'Model Display'},
										{'url': reverse('display_model', args=(self._app_name, self._model_name)), 'name' : self._plural_t}])
		table = self._disp_model.DjangoTable(self._disp_model.model.objects.all())
		RequestConfig(self._request).configure(table)
		self._context.update({'page_menu': links, 'crums': crums, 'table': table, 'model_title': self._plural_t})
		
		self._context['title'] = self._plural_t
		self._top_active = 'display_index'
		self.generate_base()
		return self._context

class DisplayItem(TemplateBase):
	template_name = 'sk_item_display.html'
	
	def get_context_data(self, **kw):
		self.setup_context(**kw)
		self._item_id = kw.get('id', None)
		self._item = self._disp_model.model.objects.get(id = int(self._item_id))
		
		
		links = [{'url': reverse('add_item', args=[self._app_name, self._model_name]), 'name': 'Add ' + self._single_t},
				{'url': reverse('edit_item', args=[self._app_name, self._model_name, self._item.id]), 'name': 'Edit Item'},
				{'url': reverse('delete_item', args=[self._app_name, self._model_name, self._item.id]), 'name': 'Delete Item'}]
		
		status_groups=[]
		title = '%s: %s' %  (self._single_t, str(self._item))
		status_groups.append({'title': title, 'fields': self._populate_fields(self._item, self._disp_model)})
		tbelow = self._populate_tables(self._item, self._disp_model)
		name = str(self._disp_model.model.objects.get(id=int(self._item_id)))
		crums = self._set_crums(add = [{'url': reverse('display_item', args=(self._app_name, self._model_name, int(self._item_id))), 'name': name}])
		
		self._context.update({'page_menu': links, 'status_groups': status_groups, 'crums': crums, 'tables_below': tbelow})

		self._context['title'] = self._single_t
		self._top_active = 'display_index'
		self.generate_base()
		return self._context
	
	def _populate_fields(self, item, dm, exceptions=[]):
		item_fields=[]
		for field in dm.model._meta.fields:
			if field.name in exceptions:
				continue
			name = field.verbose_name
			value = self._convert_to_string(getattr(item, field.name), field.name)
			item_fields.append({'name': name, 'state': value })
		for func in dm.extra_funcs:
			value = self._convert_to_string(getattr(item, dm.extra_funcs[func])(), func)
			item_fields.append({'name': func, 'state': value})
		return item_fields
	
	def _populate_tables(self, item, model):
		generated_tables = []
		if hasattr(model, 'attached_tables'):
			for tab in model.attached_tables:
				this_table={'title': tab['title']}
				if 'populate' in tab:
					popul = getattr(item, tab['populate']).all()
				else:
					popul = getattr(item,  tab['populate_func'])()
				if 'table' in tab:
					table_def = getattr(self._apps[self._disp_model.app_parent][tab['name']], tab['table'])
				else:
					table_def = self._apps[self._disp_model.app_parent][tab['name']].DjangoTable
				this_table['renderable'] = table_def(popul)
				RequestConfig(self._request).configure(this_table['renderable'])
				generated_tables.append(this_table)

		return generated_tables
	
	def _convert_to_string(self, value, name):
		if value == None:
			return ''
		if isinstance(value, bool):
			if value:
				return u'\u2713'
			else:
				return u'\u2718'
		elif isinstance(value, long) or isinstance(value, int) or isinstance(value, float):
			return self._find_base(value)
		elif isinstance(value, datetime):
			return value.strftime(settings.CUSTOM_DT_FORMAT)
		elif isinstance(value, models.Model):
			model_name = value.__class__.__name__
			app_name = value.__module__.replace('.models', '')
			return '<a href="%s">%s</a>' % (reverse('display_item', args=[app_name, model_name, value.id]), str(value))
		else:
			if name == 'index':
				if value.startswith('    '):
					value = value[2:]
					value = value.replace('\n    ', '\n  ')
				value = markdown2.markdown(value)
			elif name in ['raw', 'log']:
				value = '<textarea>%s</textarea>' % value
			return smart_str(value)
	
	def _find_base(self, value):
		if value > 1e3:
			return '{:,}'.format(value)
		elif isinstance(value, float):
			return '%0.2f' % value
		else:
			return '%d' % value

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect(reverse('index'))

		
def default_side_menu(disp_model=None, apps=None):
	side_menu = []
	active = None
	if disp_model is not None: active = disp_model.__name__
	if apps is None: apps = SkeletalDisplay.get_display_apps()
	for app_name in apps:
		for model_name in apps[app_name]:
			model = apps[app_name][model_name]
			if model.display:
				cls = ''
				if model_name == active: cls = 'open'
				side_menu.append({'url': reverse('display_model', args=[app_name, model_name]), 
								'name': get_plural_name(model), 'class': cls, 'index': model.index})
	side_menu = sorted(side_menu, key=lambda d: d['index'])
	return side_menu
	
def base_context(request, side_menu, top_active=None):
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
	site_title = settings.SITE_TITLE
	return {'top_menu': top_menu, 'site_title': site_title, 'menu': side_menu}

def base(request, title, content, template, apps=None, disp_model=None, top_active=None):
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
	main_menu=[]
	active = None
	if disp_model is not None: active = disp_model.__name__
	if apps is None: apps = SkeletalDisplay.get_display_apps()
	for app_name in apps:
		for model_name in apps[app_name]:
			model = apps[app_name][model_name]
			if model.display:
				cls = ''
				if model_name == active: cls = 'open'
				main_menu.append({'url': reverse('display_model', args=[app_name, model_name]), 
								'name': get_plural_name(model), 'class': cls, 'index': model.index})
	main_menu = sorted(main_menu, key=lambda d: d['index'])
	site_title = settings.SITE_TITLE
	content.update({'top_menu': top_menu, 'site_title': site_title, 'title': title, 'menu': main_menu})
	return render_to_response(template, content, context_instance=RequestContext(request))

def get_plural_name(dm):
	return  unicode(dm.model._meta.verbose_name_plural)