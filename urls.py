from django.conf.urls import patterns, url, include
import editor
import views
import views_base as viewb
import public

urlpatterns = patterns('HotDjango.views',
#    url(r'^$', views.AllView.as_view(), name='all-hot-table'),
    url(r'^restful/', include('HotDjango.rest_urls')),
#    url(r'^(?P<app>\w+)/(?P<model>\w+)$', views.TableView.as_view(), name='hot-table'),
    url(r'^$', views.DisplayModel.as_view(), name= public.HOT_URL_NAME),
    url(r'^(?P<app>\w+)/(?P<model>\w+)$', views.DisplayModel.as_view(), name= public.HOT_URL_NAME),
    url(r'^(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', views.DisplayItem.as_view(), name= public.HOT_URL_NAME),
    url(r'^permden$', viewb.PermissionDenied.as_view(), name='permission_denied'),
    url(r'^user$', views.UserDisplay.as_view(), name='user_profile'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^', include('password_reset.urls')),
)

urlpatterns += patterns('',
    url(r'^(?P<app>\w+)/(?P<model>\w+)/add$', editor.AddEditItem.as_view(), name='add_item'),
    url(r'^(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)/edit$', editor.AddEditItem.as_view(), name='edit_item'),
    url(r'^(?P<app>\w+)/(?P<model>\w+)/hot_edit$', editor.HotEdit.as_view(), name='hot_edit'),
    url(r'^(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)/delete$', editor.DeleteItem.as_view(), name='delete_item'),
)