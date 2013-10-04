from django.conf.urls import patterns, url
import SkeletalDisplay.editor as editor
import SkeletalDisplay.views as views
import SkeletalDisplay.views_base as viewb

urlpatterns = patterns('SkeletalDisplay.views',
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^disp/$', views.DisplayIndex.as_view(), name='sk'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)$', views.DisplayModel.as_view(), name='sk'),
    url(r'^disp/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', views.DisplayItem.as_view(), name='sk'),
    url(r'^permden$', viewb.PermissionDenied.as_view(), name='permission_denied'),
    url(r'^user$', views.UserDisplay.as_view(), name='user_profile'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
)

urlpatterns += patterns('SkeletalDisplay.editor',
    url(r'^add/(?P<app>\w+)/(?P<model>\w+)$', editor.AddEditItem.as_view(), name='add_item'),
    url(r'^edit/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', editor.AddEditItem.as_view(), name='edit_item'),
    url(r'^hot_edit/(?P<app>\w+)/(?P<model>\w+)$', editor.HotEdit.as_view(), name='hot_edit'),
    url(r'^delete/(?P<app>\w+)/(?P<model>\w+)/(?P<id>\d+)$', editor.DeleteItem.as_view(), name='delete_item'),
)