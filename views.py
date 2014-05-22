from django.utils.encoding import smart_str
from datetime import datetime
import settings
from django.db import models
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
import views_base as viewb
import django.contrib.auth.views
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
import markdown2
import django.forms as forms
import public
import django.views.generic as generic
from django.core.context_processors import csrf
import django.utils.formats as django_format
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import settings
from django.contrib.auth.forms import AuthenticationForm

class AuthForm(AuthenticationForm):
	def __init__(self, request=None, *args, **kwargs):
		super(AuthForm, self).__init__(request, *args, **kwargs)
		self.fields['password'].widget = forms.PasswordInput(attrs={'placeholder': 'Password'})
		self.fields['username'].widget = forms.TextInput(attrs={'placeholder': 'Username'})

DEFAULT_LOGIN_TEMPLATE = 'hot/login.html'

def login_template():
	if hasattr(settings, 'LOGIN_TEMPLATE'):
		return settings.LOGIN_TEMPLATE
	return DEFAULT_LOGIN_TEMPLATE

def logout(request):
	auth_logout(request)
	return redirect(reverse(settings.INDEX_URL_NAME))

def login(request, *args):
	template = login_template()
	if hasattr(settings, 'LOGIN_TEMPLATE'):
		template = settings.LOGIN_TEMPLATE
	context = viewb.set_messages(request)
	context['is_mobile'] = viewb.is_mobile(request)
	kw = {'template_name': template, 
		  'extra_context': context,
		  'authentication_form': AuthForm,}
	return django.contrib.auth.views.login(request, *args, **kw)

class Index(viewb.TemplateBase):
	template_name = 'hot/index.html'
	side_menu = False
	all_permitted = True
	show_crums = False
	
	def setup_context(self, **kw):
		self.request.session['menu_active'] = None
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
	template_name = 'hot/model_display.html'
	filter_form = FilterForm
	
	def get_context_data(self, **kw):
		self._context['page_menu'] = self.set_links()
		qs = self.filter
		table = self.generate_table(self._disp_model.DjangoTable, qs)
# 		RequestConfig(self.request).configure(table)
		self._context['table'] = table
		
		self._context['title'] = self._plural_t
		return self._context
	
	@property
	def filter(self):
		qs = super(DisplayModel, self).filter
		if self._disp_model.filter_options is not None:
			filter_ops = self._disp_model.filter_options
			choices = [(i, choice[0]) for i, choice in enumerate(filter_ops)]
			initial = 0
			if 'filter' in self.request._get_get():
				initial = int(self.request._get_get()['filter'])
				extra_filter = filter_ops[initial][1]
				qs = extra_filter(qs)
			self._context['FilterForm'] = FilterForm(choices = choices, initial = initial)
		return qs
	
	def get_item_args(self):
		return [self._app_name, self._model_name]
	
	def set_links(self):
		links = super(DisplayModel, self).set_links()
		if self._disp_model.HotTable:
			links.append({'url': reverse('hot_edit', kwargs={'app': self._app_name, 'model': self._model_name}), 'name': 'Mass Edit'})
		return links

class DisplayItem(viewb.TemplateBase):
	template_name = 'hot/item_display.html'
	_hot_added = False
	custom_tables_below = False
	
	def get_context_data(self, **kw):
		self._context['page_menu'] = self.set_links()
		status_groups = [{'title': None, 'fields': self._populate_fields(self._item, self._disp_model)}]
		
		for extra in self._disp_model.extra_models:
			model_name = extra['model']
			if extra['field'] == 'self':
				model = self._item
				title = ''
			else:
				model = getattr(self._item, extra['field'])
				title =self._item._meta.get_field_by_name(extra['field'])[0].verbose_name
			title = extra.get('title', title)
			visible = extra.get('visible', False)
			if model:
				status_groups.append({'title': title, 
									'fields': self._populate_fields(model, self._apps[self._app_name][model_name]),
									'collapse': True,
									'visible': visible})
		
		self._context['status_groups'] = status_groups
		self._context['tables_below'] = self._populate_tables(self._item, self._disp_model)
		
		name = str(self._disp_model.model.objects.get(id=int(self._item_id)))
		self.set_crums(add = [{'url': reverse(self.viewname, args=self.args_base(model = self._model_name) + [int(self._item_id)]), 'name': name}])
		title = '%s: %s' %  (self._single_t, self._item.__unicode__())
		self._context['title'] = title
		return self._context
	
	def set_links(self):
		links = super(DisplayItem, self).set_links()
		if self._disp_model.editable:
			links.append({'url': reverse('edit_item', args=[self._app_name, self._model_name, self._item.id]), 'name': 'Edit ' + self._single_t})
		if self._disp_model.deletable:
			links.append({'url': reverse('delete_item', args=[self._app_name, self._model_name, self._item.id]), 
					  	  'name': 'Delete ' + self._single_t, 
					  	  'classes': 'confirm-follow', 
                          'msg': 'Are you sure you wish to delete this item?'})
		if self._disp_model.related_tables:
			field_names = self._disp_model.related_tables.keys()
			self._add_hot(field_names)
			for field_name in field_names:
				links.append({'onclick': "edit_related('%s')" % field_name,  
							'name': 'Edit Associated ' + public.get_verbose_name(self._disp_model, field_name)})
		if self._disp_model.HotTable:
			for field_name in self._disp_model.HotTable.Meta.fields:
				dj_field = self._disp_model.model._meta.get_field_by_name(field_name)[0]
				if isinstance(dj_field, models.ManyToManyField):
					links.append({'onclick': "edit_m2m('%s')" % field_name,  
								'name': 'Edit Associated ' + public.get_verbose_name(self._disp_model, field_name)})
					self._add_hot([field_name])
		if self._disp_model.extra_buttons:
			links.extend(self._disp_model.extra_buttons(self))
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
		if not dm.exclude_all:
			for field in dm.model._meta.fields:
				if field.name in exceptions or field.name in dm.exclude:
					continue
				name = field.verbose_name
				try:
					value = self._convert_to_string(getattr(item, field.name), field)
				except ObjectDoesNotExist:
					value = 'Not Found'
				item_fields.append({'name': name, 'state': value })
		for name, func in dm.extra_funcs:
			if hasattr(dm, func):
				value = getattr(dm, func)(item)
			else:
				value = getattr(item, func)
				if hasattr(value, '__call__'):
					value = value()
			value = self._convert_to_string(value)
			item_fields.append({'name': name, 'state': value})
		for name, field in dm.extra_fields.items():
			sub_item = item
			for part in field.split('__'):
				sub_item = getattr(sub_item, part)
			value = self._convert_to_string(sub_item, field)
			item_fields.append({'name': name, 'state': value})
		return item_fields
	
	def _populate_tables(self, item, model):
		generated_tables = []
		for tab in model.attached_tables:
			this_table={'title': tab['title'], 'id': tab['title'].lower()}
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
	
	def _convert_to_string(self, value, field = None):
		if value == None:
			return ''
		if field and len(field.choices) > 0:
			cdict = dict(field.choices)
			if value in cdict:
				return cdict[value]
		if isinstance(field, models.URLField):
			return '<a href="%s" target="blank">%s</a>' % (value, value)
		if isinstance(value, bool):
			if value:
				return '<span class="glyphicon glyphicon-ok"></span>'
			else:
				return '<span class="glyphicon glyphicon-remove"></span>'
		elif isinstance(value, (list, tuple, QuerySet)):
			return ', '.join(self._convert_to_string(v) for v in value)
		elif isinstance(value, (long, int, float)):
			return self._find_base(value)
		elif isinstance(value, datetime):
			return django_format.date_format(timezone.localtime(value), 'DATETIME_FORMAT')
		elif isinstance(value, models.Model):
			name = value.__class__.__name__
			if self._disp_model.models2link2 and name not in self._disp_model.models2link2.keys():
				return smart_str(value)
			if self._disp_model.models2link2 and name in self._disp_model.models2link2.keys():
				rev = self._disp_model.models2link2[name]
				return '<a href="%s">%s</a>' % (reverse(rev, args=[value.id]), str(value))
			else:
				app_mod = self._find_model(value.__class__.__name__)
				if app_mod:
					app_name, disp_model = app_mod
					return '<a href="%s">%s</a>' % (reverse(self.viewname, args=self.args_base(app_name, disp_model) + [value.id]), str(value))
		elif isinstance(value, models.fields.files.ImageFieldFile):
			if value.name:
				return '<a href="%s"><img src="%s" alt="image unavailable"></a>' % \
						(value.url, value.url)
			else: return ''
		return smart_str(value)
				
	def _find_model(self, to_find):
		return public.find_disp_model(self._apps, to_find, self._app_name)
	
	def _find_base(self, value):
		if value > 1e3:
			return '{:,}'.format(value)
		elif isinstance(value, float):
			return '%0.2f' % value
		else:
			return '%d' % value

class TextDisplay(viewb.TemplateBase):
	template_name = 'hot/text_page.html'
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
	menu_active = 'user_profile'
	all_auth_permitted = True
	side_menu = False
	
	def setup_context(self, **kw):
		referrer = self.request.META.get('HTTP_REFERER')
		if referrer and referrer.endswith('change_password'):
			self.request.session['success'] = 'Password changed successfully'
		kw ['model'] = 'User'
		kw['id'] = str(self.request.user.id)
		super(UserDisplay, self).setup_context(**kw)
	
	def set_links(self):
		links = [{'url': reverse('change_password'), 'name': 'Change Password'}]
		links += super(UserDisplay, self).set_links()
		links.append({'url': reverse('logout'), 'name': 'Logout'})
		return links

#hands-on-table:

class AllView(generic.TemplateView):

	template_name = 'all_hot.html'
	
	def get_context_data(self, **kwargs):
		context = super(AllView, self).get_context_data(**kwargs)
		context.update(base_context(self.request))
		return context

class TableView(generic.TemplateView):
	template_name = 'simple_hot.html'
	
	def get_context_data(self, **kwargs):
		context = super(TableView, self).get_context_data(**kwargs)
		self._app_name = kwargs['app']
		context['app_name'] = self._app_name
		context['model_name'] = kwargs['model']
		context.update(base_context(self.request))
		return context

def base_context(request):
	context = {}
	apps = public.get_rest_apps()
	context['menu'] = []
	for app_name, app in apps.iteritems():
		for model_name in app.keys():
			context['menu'].append({'name': model_name,
	                     'url': reverse('hot-table', kwargs={'app': app_name, 'model': model_name})})
	context['menu'].append({'name': 'Restful API',
	             'url': reverse('all-hot-table') + 'restful'})
	context.update(csrf(request))
	return context