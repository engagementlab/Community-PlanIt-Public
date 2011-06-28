import datetime

from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext, loader
from django.contrib import auth

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from web.instances.models import *
from web.attachments.models import Attachment
from web.accounts.models import *
from web.missions.models import *
from web.challenges.models import *
from web.accounts.forms import *
from web.reports.models import Activity 
from web.reports.actions import ActivityLogger
from web.processors import instance_processor as ip

#TODO: this does not fail nicely, it should 
def region(request, slug):
    instance = Instance.objects.get(slug=slug)
    userProfiles = UserProfile.objects.filter(instance=instance)
    users = []
    for userProfile in userProfiles:
        users.append(userProfile.user)
    leaderboard = []
    for userProfile in userProfiles.order_by("-totalPoints"):
        leaderboard.append(userProfile.user)
    log = Activity.objects.filter(instance=instance).order_by('-date')[:100]
    attachments = Attachment.objects.filter(instance=instance).exclude(file='')
    tmpl = loader.get_template('instances/base.html')
    return HttpResponse(tmpl.render(RequestContext(request, {
        'current_instance': instance,
        'users': users,
        'leaderboard': leaderboard,
        'log': log,
        'attachments': attachments,
    }, [ip])))

def all(request):
    instances = Instance.objects.all()
    now = datetime.datetime.now()
    
    # Get number of players in instance
    for instance in instances:
        instance.player_count = UserProfile.objects.filter(instance=instance).count()

    tmpl = loader.get_template('instances/all.html')
    return HttpResponse(tmpl.render(RequestContext(request, {
        'instances': instances,
        'now': now,
    }, [ip])))
