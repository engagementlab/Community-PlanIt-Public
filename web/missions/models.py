import os.path
from datetime import datetime, timedelta
from decimal import Decimal
from operator import attrgetter

from cache_utils.decorators import cached
#from stream import utils as stream_utils

from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import SortedDict
from django.db import models
from django.conf import settings
#from django.db.models.signals import post_save

from web.instances.models import Instance, BaseTreeNode
from web.challenges.models import (
        Challenge, 
        BarrierChallenge, 
        FinalBarrierChallenge,
)

#from .managers import MissionManager

import logging
log = logging.getLogger(__name__)


class Mission(BaseTreeNode):

    description = models.TextField(blank=True)
    video = models.TextField(blank=True)
    challenge_coin_value = models.IntegerField(verbose_name="coin value for challenge", default=0)
    created_date = models.DateTimeField(auto_now_add=True)

    #objects = MissionManager()

    @property 
    def start_date(self):
        for dt, m in self.parent._missions_by_start_date.\
                iteritems():
            if m == self:
                return dt

    @property 
    def end_date(self):
        return self.start_date + \
            timedelta(days=self.parent.days_for_mission)

    @property
    def ends_in_days(self):
        delta =  self.end_date - datetime.now()
        return delta.days

    @property
    def starts_in_days(self):
        delta = self.start_date - datetime.now()
        return delta.days

    @property
    def is_active(self):
        return self == self.parent.active_mission

    @property
    def is_expired(self):
        return datetime.now() > self.end_date

    @property
    def is_future(self):
        return datetime.now() <= self.start_date

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('instances:missions:mission', (), {
            'game_slug': self.parent.slug,
            'mission_id': self.pk
        })

    def get_next_mission(self):
        return self.get_next_sibling()

    def get_previous_mission(self):
        return self.get_previous_sibling()


    def _validate_challenge_counts(self, d):
        """ make sure that the challenges count in the SortedDict is the same as in db"""

        dict_challenge_count = len(d.keys())
        for k in d.keys():
            dict_challenge_count += len(d.get(k))
        return Challenge.objects.filter(parent=self).count() == dict_challenge_count

    @property
    def challenges_as_sorteddict(self):
        d = SortedDict()
        this_block = []
        for challenge in Challenge.objects.filter(parent=self):
            if not challenge.challenge_type in \
                    (Challenge.BARRIER, Challenge.FINAL_BARRIER):
                this_block.append(challenge)
            else:
                d[challenge] = this_block
                this_block = []

        #TODO
        # move the validation checks to the admin

        msg = "Mission `%s` contains two consecutive Barrier Challenges"  %(self.__unicode__())
        for val in d.values():
            assert len(val) != 0, msg

        msg = "Mission `%s` contains an invalid number of barriers, need at least one Barrier Challenge and one Final Barrier Challenge" %(self.__unicode__())
        assert (Challenge.objects.filter(parent=self).\
                            instance_of(FinalBarrierChallenge) | 
                Challenge.objects.filter(parent=self).\
                            instance_of(BarrierChallenge)).count()  == len(d), msg

        msg = "Mission `%s` contains an invalid challenge/barrier order" %(self.__unicode__())
        assert self._validate_challenge_counts(d) is True, msg

        return d

#stream_utils.register_target(Mission)

#ALTER TABLE stream_action ADD COLUMN action_object_mission_id integer;
#stream_utils.register_action_object(Mission)

# invalidate cache for 'missions' group
def invalidate_mission(sender, **kwargs):
    activity = kwargs.pop('instance')
    if activity:
        mission_id = activity.mission.pk
        Mission.get_challenges_cached.invalidate(mission_id)
        Mission.get_player_submitted_activities_cached.invalidate(mission_id)

#post_save.connect(invalidate_mission, Mission)
#post_save.connect(invalidate_prof_per_instance, Mission)

#def invalidate_activities_for_mission(sender, **kwargs):
#    activity = kwargs.get('instance')
#    log.debug("on_delete. invaliding activities_for_mission %s" %  activity)
#    Mission.objects.activities_for_mission(slug=activity.mission.slug)

