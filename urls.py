from django.conf.urls import patterns, include, url
import SkeletalDisplay.editor as editor
import SkeletalDisplay.views as views

urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'sk_login.html'}, name='login'),
)

urlpatterns += patterns('SkeletalDisplay.views',
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^disp/$', views.DisplayIndex.as_view(), name='display_index'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)$', views.DisplayModel.as_view(), name='display_model'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', views.DisplayItem.as_view(), name='display_item'),
    url(r'^logout/$', 'logout', name='logout'),
)

urlpatterns += patterns('SkeletalDisplay.editor',
    url(r'^add/(\w+)/(\w+)$', 'add_item', name='add_item'),
    url(r'^hot_edit/(?P<app>\w+)/(?P<model>\w+)$', editor.HotEdit.as_view(), name='hot_edit'),
    url(r'^edit/(\w+)/(\w+)/(\d+)$', 'edit_item', name='edit_item'),
    url(r'^delete/(\w+)/(\w+)/(\d+)$', 'delete_item', name='delete_item'),
)