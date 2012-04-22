from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

urlpatterns = patterns('web.crowds.views',

    # View
    url(r'^(?P<id>\d+)/view/$', 'view_crowd', name='view'),
    # Join
    url(r'^(?P<id>\d+)/join/$', 'join_crowd', name='join'),
    # Leave
    url(r'^(?P<id>\d+)/leave/$', 'leave_crowd', name='leave'),
    # Comment
    url(r'^(?P<id>\d+)/comment/$', 'comment', name='comment'),
    
    # Add
    url(r'^create/$', 'rally', name='rally'),
    url(r'^remove/$', 'delete', name='delete'),
    #Submit Response
    #url(r'^(?P<id>\d+)/$', 'challenge', name='challenge'),

    # Show all
    url(r'^$', 'all', name='index'),
)
