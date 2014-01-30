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
import markdown2
import django.forms as forms
import HotDjango

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
	
class FilterForm(forms.Form):
	def __init__(self, *args, **kwargs):
		choices = kwargs.pop('choices', ())
		initial = kwargs.pop('initial', 0)
		super(FilterForm, self).__init__(*args, **kwargs)
		self.fields['filter'] = forms.ChoiceField(choices=choices, initial = initial)

class DisplayModel(viewb.TemplateBase):
	template_name = 'sk_model_display.html'
	_base_queryset = None
	
	def get_context_data(self, **kw):
		self._context['page_menu'] = self.set_links()
		extra_filter = None
		if hasattr(self, 'filter_options'):
			choices = [(i, choice[0]) for i, choice in enumerate(self.filter_options)]
			initial = 0
			if 'filter' in self.request._get_get():
				initial = int(self.request._get_get()['filter'])
				extra_filter = self.filter_options[initial][1]
			self._context['FilterForm'] = FilterForm(choices = choices, initial = initial)
		if self._base_queryset:
			qs = self._base_queryset()
		elif self._disp_model.queryset is not None:
			qs = self._disp_model.queryset()
		else:
			qs = self._disp_model.model.objects.all()
		if extra_filter:
			qs = extra_filter(qs)
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
	_hot_added = False
	
	def get_context_data(self, **kw):
		self._context['page_menu'] = self.set_links()
		status_groups=[{'title': None, 'fields': self._populate_fields(self._item, self._disp_model)}]
		
		for field_name, model_name in self._disp_model.extra_models.items():
			model = getattr(self._item, field_name)
			field =self._item._meta.get_field_by_name(field_name)[0]
			if model:
				status_groups.append({'title': field.verbose_name, 'fields': self._populate_fields(model, self._apps[self._app_name][model_name])})
		
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
		if hasattr(self._disp_model, 'related_tables'):
			field_names = self._disp_model.related_tables.keys()
			self._add_hot(field_names)
			for field_name in field_names:
				links.append({'onclick': "edit_related('%s')" % field_name,  
							'name': 'Edit Associated ' + HotDjango.get_verbose_name(self._disp_model, field_name)})
		if hasattr(self._disp_model, 'HotTable'):
			for field_name in self._disp_model.HotTable.Meta.fields:
				dj_field = self._disp_model.model._meta.get_field_by_name(field_name)[0]
				if isinstance(dj_field, models.ManyToManyField):
					links.append({'onclick': "edit_m2m('%s')" % field_name,  
								'name': 'Edit Associated ' + HotDjango.get_verbose_name(self._disp_model, field_name)})
					self._add_hot([field_name])
		return links
	
	def _add_hot(self, field_names):
		if self._hot_added:
			self._context['hot_fields'] += ',' + ','.join(field_names)
			return
		self._context['hot'] = True
		self._context['app_name'] = self._app_name
		self._context['model_name'] = self._model_name
		self._context['this_item_id'] = self._item_id
		self._context['hot_fields'] = ','.join(field_names)
		self._hot_added = True
		
	def _populate_fields(self, item, dm, exceptions=[]):
		item_fields=[]
		for field in dm.model._meta.fields:
			if field.name in exceptions or field.name in dm.exclude:
				continue
			name = field.verbose_name
			value = self._convert_to_string(getattr(item, field.name))
			item_fields.append({'name': name, 'state': value })
		for name, func in dm.extra_funcs:
			value = getattr(item, func)()
			value = self._convert_to_string(value)
			item_fields.append({'name': name, 'state': value})
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
			name = value.__class__.__name__
			if self._disp_model.models2link2 and name not in self._disp_model.models2link2.keys():
				return smart_str(value)
			if  not self._disp_model.models2link2:
				(app_name, disp_model) = self._find_model(value.__class__.__name__)
				return '<a href="%s">%s</a>' % (reverse(self.viewname, args=self.args_base(app_name, disp_model) + [value.id]), str(value))
			else:
				rev = self._disp_model.models2link2[name]
				return '<a href="%s">%s</a>' % (reverse(rev, args=[value.id]), str(value))
		elif isinstance(value, models.fields.files.ImageFieldFile):
			if value.name:
				return '<img src="%s" height="150" alt="image unavailable">' % value.url
			else: return ''
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

class TextDisplay(viewb.TemplateBase):
	template_name = 'sk_text_page.html'
	side_menu = False
	all_auth_permitted = True
	body = ''
	title = 'Empty'
	
	def page_setup(self):
		pass
	
	def get_context_data(self, **kw):
		self.page_setup()
		self._context['title'] = self.title
		self._context['page_content'] = markdown2.markdown(self.body)
		return self._context
		
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
		links = [{'url': reverse('password_reset_recover'), 'name': 'Change Password'}]
		links += super(UserDisplay, self).set_links()
		links.append({'url': reverse('logout'), 'name': 'Logout'})
		return links