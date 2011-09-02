import datetime
from django.template.defaultfilters import slugify
from django.db import models
from django.contrib import admin

from nani.admin import TranslatableAdmin
from nani.models import TranslatableModel, TranslatedFields
from nani.manager import TranslationManager

from instances.models import Instance

#class MissionQueryMixin(object):
#    def past(self):
#        return self.filter(end_date__lt=datetime.datetime.now()).order_by('-end_date')
#
#    def future(self):
#        return self.filter(start_date__gt=datetime.datetime.now()).order_by('start_date')
#
#    def active(self):
#        now = datetime.datetime.now()
#        return self.filter(start_date__lte=now, end_date__gte=now).order_by('start_date')

#class MissionQuerySet(TranslationQueryset, MissionQueryMixin):
#    pass

class MissionManager(TranslationManager):
    #def get_query_set(self):
    #    return MissionQuerySet(self.model, using=self._db)

    def past(self):
        return self.filter(end_date__lt=datetime.datetime.now()).order_by('-end_date')

    def future(self):
        return self.filter(start_date__gt=datetime.datetime.now()).order_by('start_date')

    def active(self):
        now = datetime.datetime.now()
        return self.filter(start_date__lte=now, end_date__gte=now).order_by('start_date')

class Mission(TranslatableModel):
    instance = models.ForeignKey(Instance, related_name='missions')
    slug = models.SlugField(editable=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    video = models.TextField(blank=True)

    translations = TranslatedFields(
        name = models.CharField(max_length=45),
        description = models.TextField(blank=True),
        #meta = {'get_latest_by': 'start_date'}
    )
    
    objects = MissionManager()

    class Meta:
        get_latest_by = 'start_date'
        
    def is_active(self):
        now = datetime.datetime.now()
        return self.start_date <= now and now <= self.end_date
        
    def is_expired(self):
        return datetime.datetime.now() > self.end_date
    
    def is_started(self):
        return datetime.datetime.now() >= self.start_date

    @classmethod 
    def latest_by_instance(self, instance):
        missions_for_instance = self.objects.filter(instance=instance)
        latest_by =  max(missions_for_instance.values_list('end_date'))
        return self.objects.get(**{'end_date': latest_by})

    def save(self):
        #TODO make this work with unicode
        self.slug = slugify(self.pk)
        super(Mission, self).save()

    def __unicode__(self):
        return self.safe_translation_getter('name', 'Mission: %s' % self.pk)

class MissionAdmin(TranslatableAdmin):
    list_display = ('start_date', 'end_date', 'instance') #could not be used with nani:, 'name', 
