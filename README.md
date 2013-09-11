django-skeletal-display
=======================

django app for simple display of models using bootstrap

App uses django-tables2 (https://github.com/bradleyayers/django-tables2) to provide a simple dispaly of defined apps.

To use:

install django-tables2 and markdown (used for displaying TextFields in certain situations:
	(sudo) pip install django-tables2 markdown2 django-bootstrap3

Add folder (named SkeletalDisplay) to project folded.

Edit settings.py

	# make sure TEMPLATE_CONTEXT_PROCESSORS is included and includes auth
	TEMPLATE_CONTEXT_PROCESSORS =(
		"django.contrib.auth.context_processors.auth",
		"django.core.context_processors.debug",
		"django.core.context_processors.i18n",
		"django.core.context_processors.media",
		"django.core.context_processors.static",
		"django.core.context_processors.tz",
		"django.contrib.messages.context_processors.messages",
		'django.core.context_processors.request')

	TEMPLATE_DIRS = (os.path.join(SITE_ROOT, 'templates'),
					os.path.join(SITE_ROOT, 'SkeletalDisplay/templates'))

	INSTALLED_APPS = [
		...
	    'SkeletalDisplay',
		'django_tables2',
		'bootstrap3',
		...
	]
	
	...

	#Skeletal Dispaly Settings
	
	CUSTOM_DATE_FORMAT = '%Y-%m-%d'
	CUSTOM_DT_FORMAT = '%Y-%m-%d %H:%M:%S %Z'
	CUSTOM_SHORT_DT_FORMAT = '%y-%m-%d_%H %M'
	DATETIME_FORMAT = 'Y-m-d H:i:s'
	SHORT_DATETIME_FORMAT = DATETIME_FORMAT
	
	DISPLAY_APPS = [<<apps to display>>]
	SITE_TITLE = '<<site name>>'
	EXTRA_TOP_RIGHT_MENU = [{'url': 'name to reverse', 'name': 'Name for Link'}]
	LOGIN_REDIRECT_URL = '/'
	INTERNAL_IPS = ('127.0.0.1',)

edit your projects urls.py to look something like this:

	from django.conf.urls import patterns, include, url
	import settings

	import SkeletalDisplay.urls

	# Uncomment the next two lines to enable the admin:
	from django.contrib import admin
	admin.autodiscover()

	urlpatterns = SkeletalDisplay.urls.urlpatterns

	urlpatterns += patterns('',
		url(r'^admin/', include(admin.site.urls), name='admin'),)

	urlpatterns += patterns('',
		(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
	)

lastly you need to add a display.py file to each app named in DISPLAY_APPS (see above) to define how the app is displayed.

	import django_tables2 as tables
	from django_tables2.utils import A
	import SkeletalDisplay
	import models as m
	
	# one class for each model, with name identical to model in models.py:
	
	class Component(SkeletalDisplay.ModelDisplay):
		#extra functions from the model to display in item_display, absent for none.
		extra_funcs={'Nominal Price': 'str_nominal_price'}
		#tables from other views add to each item_display, default table name is Table, 
		# to include other Table Names, add the 'table' item, absent for none.
		attached_tables = [{'name':'Assembly', 'populate':'assemblies', 'title':'Assemblies Using this Component'},
						{'name':'Material', 'populate':'materials', 'table':'Table2', 'title':'Materials used in this Component'}]
		# index for position of this item in the main menu
		index = 0
		
		#definition of the table used for the display of all items in this model, or called by other models, extra tables may have other names,
		# args for reverse are the name of the app then the component name, then it's id.
		class Table(tables.Table):
			name = tables.LinkColumn('display_item', args=['SalesEstimates', 'Component', A('pk')])
			str_nominal_price = tables.Column(verbose_name='Nominal Price')
			class Meta(SkeletalDisplay.ModelDisplayMeta):
				model = m.Component
				exclude = ('id', 'description', 'nominal_price', 'xl_id')
