from django.utils.encoding import smart_str
from datetime import datetime
import settings
from django.db import models
from django_tables2 import RequestConfig

from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
import SkeletalDisplay.views_base as viewb
import django.contrib.auth.views

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect(viewb.reverse('index'))

def login(*args):
	template = 'sk_login.html'
	if hasattr(settings, 'LOGIN_TEMPLATE'):
		template = settings.LOGIN_TEMPLATE
	kw = {'template_name': template}
	return django.contrib.auth.views.login(*args, **kw)

class Index(viewb.TemplateBase):
	template_name = 'sk_index.html'
	
	def get_context_data(self, **kw):
		self._context['title'] = settings.SITE_TITLE
		return self._context

class DisplayIndex(viewb.TemplateBase):
	template_name = 'sk_display_index.html'
	top_active = 'display_index'
	
	def get_context_data(self, **kw):
		self._context['title'] = settings.SITE_TITLE
		return self._context

class DisplayModel(viewb.TemplateBase):
	template_name = 'sk_model_display.html'
	top_active = 'display_index'
	
	def get_context_data(self, **kw):
		links =[]
		if self._disp_model.addable:
			links.append({'url': viewb.reverse('add_item', args=[self._app_name, self._model_name]), 'name': 'Add ' + self._single_t})
		if hasattr(self._disp_model, 'HotTable'):
			links.append({'url': viewb.reverse('hot_edit', kwargs={'app': self._app_name, 'model': self._model_name}), 'name': 'Mass Edit'})
		if self._disp_model.show_crums:
			self._context['crums'] = self._set_crums(set_to = [{'url': viewb.reverse('display_index'), 'name': 'Model Display'},
										{'url': viewb.reverse('display_model', args=(self._app_name, self._model_name)), 'name' : self._plural_t}])
		table = self._disp_model.DjangoTable(self._disp_model.model.objects.all())
		RequestConfig(self.request).configure(table)
		self._context.update({'page_menu': links, 'table': table, 'model_title': self._plural_t})
		
		self._context['title'] = self._plural_t
		return self._context

class DisplayItem(viewb.TemplateBase):
	template_name = 'sk_item_display.html'
	top_active = 'display_index'
	
	def get_context_data(self, **kw):		
		links = []
		if self._disp_model.addable:
			links.append({'url': viewb.reverse('add_item', args=[self._app_name, self._model_name]), 'name': 'Add ' + self._single_t})
		if self._disp_model.editable:
			links.append({'url': viewb.reverse('edit_item', args=[self._app_name, self._model_name, self._item.id]), 'name': 'Edit ' + self._single_t})
		if self._disp_model.deletable:
			links.append({'url': viewb.reverse('delete_item', args=[self._app_name, self._model_name, self._item.id]), 'name': 'Delete ' + self._single_t})
		
		status_groups=[{'title': None, 'fields': self._populate_fields(self._item, self._disp_model)}]
		
		for field_name, model_name in self._disp_model.extra_models.items():
			status_groups.append({'title': model_name, 
								'fields': self._populate_fields(getattr(self._item, field_name), self._apps[self._app_name][model_name])})
			
		tbelow = self._populate_tables(self._item, self._disp_model)
		name = str(self._disp_model.model.objects.get(id=int(self._item_id)))
		if self._disp_model.show_crums:
			self._context['crums'] = self._set_crums(add = [{'url': viewb.reverse('display_item', args=(self._app_name, self._model_name, int(self._item_id))), 'name': name}])
		
		self._context.update({'page_menu': links, 'status_groups': status_groups, 'tables_below': tbelow})

		title = '%s: %s' %  (self._single_t, str(self._item))
		self._context['title'] = title
		return self._context
	
	def _populate_fields(self, item, dm, exceptions=[]):
		item_fields=[]
		for field in dm.model._meta.fields:
			if field.name in exceptions or field.name in dm.exclude:
				continue
			name = field.verbose_name
			value = self._convert_to_string(getattr(item, field.name))
			item_fields.append({'name': name, 'state': value })
		for func in dm.extra_funcs:
			value = self._convert_to_string(getattr(item, dm.extra_funcs[func])())
			item_fields.append({'name': func, 'state': value})
		for name, field in dm.extra_fields.items():
			sub_item = item
			for part in field.split('__'):
				sub_item = getattr(sub_item, part)
			value = self._convert_to_string(sub_item)
			item_fields.append({'name': name, 'state': value})
		return item_fields
	
	def _populate_tables(self, item, model):
		generated_tables = []
		for tab in model.attached_tables:
			this_table={'title': tab['title']}
			if 'populate' in tab:
				popul = getattr(item, tab['populate']).all()
			else:
				popul = getattr(item,  tab['populate_func'])()
			if 'table' in tab:
				table_def = getattr(self._apps[self._disp_model._app_name][tab['name']], tab['table'])
			else:
				table_def = self._apps[self._disp_model._app_name][tab['name']].DjangoTable
			this_table['renderable'] = table_def(popul)
			RequestConfig(self.request).configure(this_table['renderable'])
			generated_tables.append(this_table)

		return generated_tables
	
	def _convert_to_string(self, value):
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
			(app_name, disp_model) = self._find_model(value.__class__.__name__)
			return '<a href="%s">%s</a>' % (viewb.reverse('display_item', args=[app_name, disp_model, value.id]), str(value))
		else:
			return smart_str(value)
				
	def _find_model(self, to_find):
		for model_name in self._apps[self._app_name].keys():
			if model_name == to_find:
				return (self._app_name, model_name)
		for app_name, app in self._apps.items():
			if app_name == self._app_name:
				continue
			for model_name in app.keys():
				if model_name == to_find:
					return (app_name, model_name)
		return None
	
	def _find_base(self, value):
		if value > 1e3:
			return '{:,}'.format(value)
		elif isinstance(value, float):
			return '%0.2f' % value
		else:
			return '%d' % value
		
class UserDisplay(DisplayItem):
	top_active = 'user_profile'
	
	def setup_context(self, **kw):
		kw['app'] = 'sk'
		kw ['model'] = 'User'
		kw['id'] = str(self.request.user.id)
		super(UserDisplay, self).setup_context(**kw)
	