import datetime

from django.db import models
from django.db.models import Q

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

from gmapsfield.fields import GoogleMapsField

from attachments.models import Attachment
from comments.models import Comment
from instances.models import Instance
from responses.comment.models import CommentResponse

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^gmapsfield\.fields\.GoogleMapsField"])

class ChallengeQueryMixin(object):
    def active(self):
        now = datetime.datetime.now()
        return self.filter(Q(start_date__isnull=True)|Q(start_date__lte=now)).filter(Q(end_date__isnull=True)|Q(end_date__gte=now)).order_by('start_date')

    def available(self, user):
        return self.active().exclude(player_challenges__player=user).order_by('start_date')

    def past(self):
        now = datetime.datetime.now()
        return self.filter(end_date__lt=now).order_by('start_date')

class ChallengeQuerySet(models.query.QuerySet, ChallengeQueryMixin):
    pass

class ChallengeManager(models.Manager, ChallengeQueryMixin):
    def get_query_set(self):
        return ChallengeQuerySet(self.model, using=self._db)

class Challenge(models.Model):
    map = GoogleMapsField()
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    flagged = models.BooleanField(default=0, editable=False)

    instance = models.ForeignKey(Instance, related_name='challenges')
    user = models.ForeignKey(User, editable=False)
    attachments = models.ManyToManyField(Attachment, blank=True)
    comments = generic.GenericRelation(Comment)
    game_type = models.CharField(max_length=45, editable=False)

    objects = ChallengeManager()

    class Meta:
        ordering = ['start_date']
    
    @models.permalink
    def get_absolute_url(self):
        return ('challenges:challenge', [str(self.id)])
    
    def is_active(self):
        if not self.start_date:
            return True

        now = datetime.datetime.now()
        return self.start_date <= now and now <= self.end_date
        
    def is_expired(self):
        return self.end_date is not None and datetime.datetime.now() > self.end_date
    
    def is_started(self):
        return self.start_date is None or datetime.datetime.now() >= self.start_date
    
    def save(self):
        self.game_type = "challenge"
        #TODO: Make sure this is correct, the None map I am not sure about - BMH
        if self.map == "None":
            self.map = self.instance.location
        super(Challenge, self).save()

    def __unicode__(self):
        label = self.name or 'None'
        return label

class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'screen_name')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'attachments' and getattr(self, 'obj', None):
            kwargs['queryset'] = Challenge.objects.get(id=self.obj.id).attachments.all()
        elif db_field.name == 'attachments':
            kwargs['queryset'] = Challenge.objects.filter(id=-2)

        if db_field.name == 'comments' and getattr(self, 'obj', None):
            kwargs['queryset'] = Challenge.objects.get(id=self.obj.id).comments.all()
        elif db_field.name == 'comments':
            kwargs['queryset'] = Challenge.objects.filter(id=-2)
        return super(ChallengeAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        self.obj = obj 
        return super(ChallengeAdmin, self).get_form(request, obj, **kwargs)

    def screen_name(self, obj):
        return obj.user.get_profile() and obj.user.get_profile().screen_name or obj.user.username

class PlayerChallengeQueryMixin(object):
    def accepted(self):
        return self.filter(accepted=True, completed=False)

    def available(self):
        now = datetime.datetime.now()
        result = self.filter(accepted=False, completed=False)
        result = result.filter(Q(challenge__start_date__isnull=True)|Q(challenge__start_date__lte=now), Q(challenge__end_date__isnull=True)|Q(challenge__end_date__gte=now))
        return result

    def completed(self):
        return self.filter(completed=True)

    def declined(self):
        return self.filter(declined=True)

    def current(self):
        return self.filter(accepted=True, completed=False)

class PlayerChallengeQuerySet(models.query.QuerySet, PlayerChallengeQueryMixin):
    pass

class PlayerChallengeManager(models.Manager, PlayerChallengeQueryMixin):
    def get_query_set(self):
        return PlayerChallengeQuerySet(self.model, using=self._db)

class PlayerChallenge(models.Model):
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    response_type = models.CharField(max_length=30, blank=True, null=True)

    attachments = models.ManyToManyField(Attachment, blank=True, null=True)
    response = models.OneToOneField(CommentResponse, null=True, blank=True, related_name='player_challenge')
    challenge = models.ForeignKey(Challenge, related_name='player_challenges')
    player = models.ForeignKey(User, related_name='player_challenges')

    objects = PlayerChallengeManager()
    
    def __unicode__(self):
        pc = None
        return (self.player.get_profile() and self.player.get_profile().screen_name or self.player.username) + ": " + self.challenge.name
