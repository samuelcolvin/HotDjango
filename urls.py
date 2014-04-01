from django.conf.urls import patterns, url, include
import HotDisplay.editor as editor
import HotDisplay.views as views
import HotDisplay.views_base as viewb

urlpatterns = patterns('HotDisplay.views',
#    url(r'^$', views.AllView.as_view(), name='all-hot-table'),
    url(r'^restful/', include('HotDisplay.rest_urls')),
#    url(r'^(?P<app>\w+)/(?P<model>\w+)$', views.TableView.as_view(), name='hot-table'),
    url(r'^disp/$', views.DisplayModel.as_view(), name='sk'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)$', views.DisplayModel.as_view(), name='sk'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', views.DisplayItem.as_view(), name='sk'),
    url(r'^permden$', viewb.PermissionDenied.as_view(), name='permission_denied'),
    url(r'^user$', views.UserDisplay.as_view(), name='user_profile'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^', include('password_reset.urls')),
)

urlpatterns += patterns('HotDisplay.editor',
    url(r'^add/(?P<app>\w+)/(?P<model>\w+)$', editor.AddEditItem.as_view(), name='add_item'),
    url(r'^edit/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', editor.AddEditItem.as_view(), name='edit_item'),
    url(r'^hot_edit/(?P<app>\w+)/(?P<model>\w+)$', editor.HotEdit.as_view(), name='hot_edit'),
    url(r'^delete/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', editor.DeleteItem.as_view(), name='delete_item'),
)