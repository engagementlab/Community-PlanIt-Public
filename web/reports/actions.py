import urllib
import math
from django.utils import simplejson
from gmapsfield.fields import GoogleMaps
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, Http404
from web.reports.models import Activity
from web.instances.models import PointsAssignment 

class ActivityLogger:
    def log(self, user, request, action, data, url, type):
    	kwargs = dict(
                user=user, 
                instance=user.get_profile().instance, 
                action=action, 
                data=data, 
                location=None, 
                url=url, 
                type=type
        )
        a = Activity.objects.create(**kwargs)
        a.save()

        # Push to messages queue
        messages.success(request, 'You ' + str(data) +' '+ str(action))

class PointsAssigner:
    def fetch(self, action):
        p = PointsAssignment.objects.get(action=action)

        return p.points 
    
    def assignPoints(self, user, points):
        if points == None:
            up = user.get_profile()
            up.totalPoints += settings.DEFAULT_POINTS or 10
            up.coinPoints += settings.DEFAULT_POINTS or 10
            up.currentCoins += settings.DEFAULT_COINS or 0
            if up.coinPoints >= 100:
                up.currentCoins += up.coinPoints / 100
                up.coinPoints = up.coinPoints % 100
            up.save()
        else:
            up = user.get_profile()
            up.totalPoints += points
            up.coinPoints += points
            if up.coinPoints >= 100:
                up.currentCoins += up.coinPoints / 100
                up.coinPoints = up.coinPoints % 100
            up.save()
    
    def assign(self, user, action):
        try:
            p = PointsAssignment.objects.get(instance=user.get_profile().instance, action__action=action)
            self.assignPoints(user, p.points)
        except PointsAssignment.DoesNotExist:
            pass
    
    def assignAct(self, user, activity):
        self.assignPoints(user, activity.getPoints())
