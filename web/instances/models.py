import datetime

from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from django.contrib import admin
from django.contrib.auth.models import User

from gmapsfield.fields import GoogleMapsField

from nani.admin import TranslatableAdmin
from nani.models import TranslatableModel, TranslatedFields
from nani.manager import TranslationManager

from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^gmapsfield\.fields\.GoogleMapsField"])


#class InstanceQueryMixin(object):
#    def past(self):
#        return self.filter(end_date__lt=datetime.datetime.now()).order_by('start_date')
#
#    def future(self):
#        return self.filter(start_date__gt=datetime.datetime.now()).order_by('start_date')
#
#    def active(self):
#        now = datetime.datetime.now()
#        return self.filter(start_date__lte=now).filter(Q(end_date__isnull=True)|Q(end_date__gte=now)).order_by('start_date')

#class InstanceQuerySet(models.query.QuerySet, InstanceQueryMixin):
#    pass

#class InstanceManager(TranslationManager, InstanceQueryMixin):
#    def get_query_set(self):
#        return InstanceQuerySet(self.model, using=self._db)

class InstanceManager(TranslationManager):
    def past(self):
        return self.filter(end_date__lt=datetime.datetime.now()).order_by('start_date')

    def future(self):
        return self.filter(start_date__gt=datetime.datetime.now()).order_by('start_date')

    def active(self):
        now = datetime.datetime.now()
        return self.filter(start_date__lte=now).filter(Q(end_date__isnull=True)|Q(end_date__gte=now)).order_by('start_date')


class Instance(TranslatableModel):
    state = models.CharField(max_length=2)
    slug = models.SlugField(unique=True, editable=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True, default=None)
    location = GoogleMapsField()
    curators = models.ManyToManyField(User)

    translations = TranslatedFields(
        name = models.CharField(max_length=45),
        city = models.CharField(max_length=255),
        content = models.TextField(null=True, blank=True),
        process_name = models.CharField(max_length=255, null=True, blank=True),
        process_description = models.TextField(null=True, blank=True),
        #meta = {'get_latest_by': 'start_date'}
    )
    objects = InstanceManager()

    class Meta:
        get_latest_by = 'start_date'
        
    def is_active(self):
        now = datetime.datetime.now()
        if now >= self.start_date and (self.end_date is None or now <= self.end_date):
            return True;
        else:
            return False;
        
    def is_expired(self):
        if self.end_date and datetime.datetime.now() >= self.end_date:
            return True
        else:
            return False
    
    def is_started(self):
        if datetime.datetime.now() >= self.start_date:
            return True
        else:
            return False
        
    def save(self, *args, **kwargs):
        #TODO make this work with unicode
        self.slug = slugify(self.pk)
        super(Instance,self).save()
        
    def __unicode__(self):
        return self.safe_translation_getter('name', 'Instance: %s' % self.pk)

    def coin_count(self):
        return self.user_profiles.aggregate(models.Sum('currentCoins')).get('currentCoins', 0)

#TODO: Perhaps this should be in it's own project
class PointsAssignment(models.Model):
    action = models.CharField(max_length=260)
    points = models.IntegerField(default=0)
    coins = models.IntegerField(default=0)

    instance = models.ForeignKey(Instance, editable=False)

class InstanceAdmin(TranslatableAdmin):
    list_display = ('start_date', 'end_date',) #could not be used with nani:, 'name', 

class NotificationRequest(models.Model):
    instance = models.ForeignKey(Instance, related_name='notification_requests')
    email = models.EmailField()

    class Meta:
        unique_together = ['instance', 'email']

    def __unicode__(self):
        return '{0}: {1}'.format(self.instance, self.email)
