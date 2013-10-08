from django.utils.encoding import smart_str
from datetime import datetime
import settings
from django.db import models
import SkeletalDisplay
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
import SkeletalDisplay.views_base as viewb
import django.contrib.auth.views
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet 

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect(settings.LOGIN_URL)

def login(*args):
	template = 'sk_login.html'
	if hasattr(settings, 'LOGIN_TEMPLATE'):
		template = settings.LOGIN_TEMPLATE
	kw = {'template_name': template}
	return django.contrib.auth.views.login(*args, **kw)

class Index(viewb.TemplateBase):
	template_name = 'sk_index.html'
	side_menu = False
	all_auth_permitted = True
	
	def setup_context(self, **kw):
		self.request.session['top_active'] = None
		super(Index, self).setup_context(**kw)
	
	def get_context_data(self, **kw):
		self._context['title'] = settings.SITE_TITLE
		return self._context

class DisplayIndex(viewb.TemplateBase):
	template_name = 'sk_display_index.html'
	
	def get_context_data(self, **kw):
		self._context['title'] = settings.SITE_TITLE
		return self._context

class DisplayModel(viewb.TemplateBase):
	template_name = 'sk_model_display.html'
	
	def get_context_data(self, **kw):
		self._context['page_menu'] = self.set_links()
		if self._disp_model.queryset is not None:
			qs = self._disp_model.queryset()
		else:
			qs = self._disp_model.model.objects.all()
		table = self.generate_table(self._disp_model.DjangoTable, qs)
# 		RequestConfig(self.request).configure(table)
		self._context['table'] = table
		
		self._context['title'] = self._plural_t
		return self._context
	
	def get_item_args(self):
		return [self._app_name, self._model_name]
	
	def set_links(self):
		links = super(DisplayModel, self).set_links()
		if hasattr(self._disp_model, 'HotTable'):
			links.append({'url': reverse('hot_edit', kwargs={'app': self._app_name, 'model': self._model_name}), 'name': 'Mass Edit'})
		return links

class DisplayItem(viewb.TemplateBase):
	template_name = 'sk_item_display.html'
	
	def get_context_data(self, **kw):
		self._context['page_menu'] = self.set_links()
		status_groups=[{'title': None, 'fields': self._populate_fields(self._item, self._disp_model)}]
		
		for field_name, model_name in self._disp_model.extra_models.items():
			field = getattr(self._item, field_name)
			if field:
				status_groups.append({'title': model_name, 'fields': self._populate_fields(field, self._apps[self._app_name][model_name])})
		
		self._context['status_groups'] = status_groups
		
		self._context['tables_below'] = self._populate_tables(self._item, self._disp_model)
		
		name = str(self._disp_model.model.objects.get(id=int(self._item_id)))
		self.set_crums(add = [{'url': 
		                    reverse(self.viewname, args=self.args_base(model = self._model_name) + [int(self._item_id)]), 'name': name}])
		
		title = '%s: %s' %  (self._single_t, str(self._item))
		self._context['title'] = title
		return self._context
	
	def set_links(self):
		links = super(DisplayItem, self).set_links()
		if self._disp_model.editable:
			links.append({'url': reverse('edit_item', args=[self._app_name, self._model_name, self._item.id]), 'name': 'Edit ' + self._single_t})
		if self._disp_model.deletable:
			links.append({'url': reverse('delete_item', args=[self._app_name, self._model_name, self._item.id]), 
					  'name': 'Delete ' + self._single_t, 'classes': 'confirm-follow', 
                      'msg': 'Are you sure you wish to delete this item?'})
		return links
		
	def _populate_fields(self, item, dm, exceptions=[]):
		item_fields=[]
		for name, func in dm.extra_funcs:
			value = getattr(item, func)()
			value = self._convert_to_string(value)
			item_fields.append({'name': name, 'state': value})
		for field in dm.model._meta.fields:
			if field.name in exceptions or field.name in dm.exclude:
				continue
			name = field.verbose_name
			value = self._convert_to_string(getattr(item, field.name))
			item_fields.append({'name': name, 'state': value })
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
			this_table['renderable'] = self.generate_table(table_def, popul)
# 			RequestConfig(self.request).configure(this_table['renderable'])
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
		elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, QuerySet):
			return ', '.join([self._convert_to_string(v) for v in value])
		elif isinstance(value, long) or isinstance(value, int) or isinstance(value, float):
			return self._find_base(value)
		elif isinstance(value, datetime):
			return value.strftime(settings.CUSTOM_DT_FORMAT)
		elif isinstance(value, models.Model):
			(app_name, disp_model) = self._find_model(value.__class__.__name__)
			return '<a href="%s">%s</a>' % (reverse(self.viewname, args=self.args_base(app_name, disp_model) + [value.id]), str(value))
		else:
			return smart_str(value)
				
	def _find_model(self, to_find):
		return SkeletalDisplay.find_model(self._apps, to_find, self._app_name)
	
	def _find_base(self, value):
		if value > 1e3:
			return '{:,}'.format(value)
		elif isinstance(value, float):
			return '%0.2f' % value
		else:
			return '%d' % value
		
class UserDisplay(DisplayItem):
	top_active = 'user_profile'
	all_auth_permitted = True
	side_menu = False
	
	def setup_context(self, **kw):
		kw['app'] = 'sk'
		kw ['model'] = 'User'
		kw['id'] = str(self.request.user.id)
		super(UserDisplay, self).setup_context(**kw)
	
	def set_links(self):
		links = super(UserDisplay, self).set_links()
		links.append({'url': 'logout', 'name': 'Logout'})
		return links