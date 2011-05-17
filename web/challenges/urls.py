from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

urlpatterns = patterns('',
    # Accept
    (r'^(?P<id>.*)/accept/$', 'challenges.views.accept'),
    # Decline
    (r'^(?P<id>.*)/decline/$', 'challenges.views.decline'),
    # Comment
    (r'^(?P<id>.*)/comment/$', 'challenges.views.comment'),
    (r'^(?P<id>.*)/complete/$', 'challenges.views.complete'),

    # Add
    (r'^add/$', 'challenges.views.add'),
    (r'^remove/$', 'challenges.views.delete'),
    # Fetch
    (r'^(?P<id>.*)/$', 'challenges.views.fetch'),
    # Show all
    (r'^$', 'challenges.views.all'),
)
