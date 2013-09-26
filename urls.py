from django.conf.urls import patterns, url
import SkeletalDisplay.editor as editor
import SkeletalDisplay.views as views

urlpatterns = patterns('SkeletalDisplay.views',
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^disp/$', views.DisplayIndex.as_view(), name='display_index'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)$', views.DisplayModel.as_view(), name='display_model'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', views.DisplayItem.as_view(), name='display_item'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
)

urlpatterns += patterns('SkeletalDisplay.editor',
    url(r'^add/(?P<app>\w+)/(?P<model>\w+)$', editor.AddItem.as_view(), name='add_item'),
    url(r'^hot_edit/(?P<app>\w+)/(?P<model>\w+)$', editor.HotEdit.as_view(), name='hot_edit'),
    url(r'^edit/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', editor.EditItem.as_view(), name='edit_item'),
    url(r'^delete/(\w+)/(\w+)/(\d+)$', 'delete_item', name='delete_item'),
)