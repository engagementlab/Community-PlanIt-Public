import datetime

from cache_utils.decorators import cached
from nani.utils import get_translation

from django.conf import settings
from django.http import Http404
from django.utils.translation import get_language
from django.contrib.sites.models import RequestSite

from web.instances.models import Instance
from web.missions.models import Mission
from web.accounts.models import UserProfilePerInstance, UserProfileVariantsForInstance

from .models import PlayerLeaderboard, AffiliationLeaderboard


import logging
log = logging.getLogger(__name__)

def _fake_latest(model, qs):
    if model and qs:
        _get_latest_by = model._meta.get_latest_by
        _latest_by = max(qs.values_list(_get_latest_by, flat=True))
        return model.objects.get(**{_get_latest_by:_latest_by})

def get_translation_with_fallback(obj, attr):
    if not get_language() in obj.get_available_languages():
        trans_model = obj.__class__.objects.translations_model()
        try:
            return getattr(get_translation(obj, settings.LANGUAGE_CODE), attr)
        except trans_model.DoesNotExist:
            return "---"
    return getattr(obj, attr)

#def instance_from_request(request):
    #user_profile = request.user.get_profile()
#    domain = RequestSite(request)
#    try:
#        return Instance.objects.get(for_city__domain=domain)
#    except Instance.DoesNotExist:
#        return

def missions_bar_context(request, mission=None):
    
    if not hasattr(request, 'current_game'):
        raise Http404("could not locate a valid game")

    try:
        prof_per_instance = UserProfilePerInstance.objects.get(
                    instance=request.current_game, 
                    user_profile=request.user.get_profile()
        )
    except UserProfilePerInstance.DoesNotExist:
        raise Http404("user for this game is not registered")

    context = {}

    if mission is None:
        mission = Mission.objects.default(request.current_game.pk)

    #my_points_for_mission, progress_percentage = \
    #    UserProfilePerInstance.objects.progress_data_for_mission(
    #                request.current_game, 
    #                mission, 
    #                prof_per_instance.user_profile
    #    )
    if mission is not None:
        my_points_for_mission, progress_percentage = \
                prof_per_instance.progress_percentage_by_mission(mission)

        context.update({
            'my_points_for_mission': my_points_for_mission,
            'progress_percentage': progress_percentage,
        })

    all_missions_for_game = Mission.objects.for_instance(instance=request.current_game)
    my_flags_count = prof_per_instance.flags
    my_badges_count = prof_per_instance.badges.count()
    my_flags_range = range(0, my_flags_count)

    #try:
    #    lb = PlayerLeaderboard.objects.get(player=prof_per_instance)
    #except PlayerLeaderboard.DoesNotExist:
    #    my_total_points = prof_per_instance.total_points,
    #else:
    #   my_total_points = lb.points
    my_total_points = prof_per_instance.total_points

    context.update({
        'mission': mission,
        'all_missions_for_game': all_missions_for_game,
        'my_flags_range': my_flags_range,
        'my_total_points': my_total_points,
        'my_badges_count': my_badges_count,
    })

    return context


def rebuild_player_leaderboard(profiles_for_game):

    for prof_per_instance in profiles_for_game:
        lb, created = PlayerLeaderboard.objects.get_or_create(player=prof_per_instance)
        #lb.points = UserProfilePerInstance.objects.total_points_for_profile(prof_per_instance.instance, prof_per_instance.user_profile)
        lb.points = prof_per_instance.total_points
        lb.screen_name = prof_per_instance.user_profile.screen_name
        lb.absolute_url = prof_per_instance.get_absolute_url()
        lb.date_last_built = datetime.datetime.now()
        lb.save()

def rebuild_affiliation_leaderboard(game, affiliations):

    for affiliation in affiliations:
        points = 0
        lb, created = AffiliationLeaderboard.objects.get_or_create(instance=game, affiliation=affiliation)
        for prof_per_instance in UserProfilePerInstance.objects.filter(instance=game, affils=affiliation).\
                exclude(user_profile__user__is_active=False):
            #points_for_player = UserProfilePerInstance.objects.total_points_for_profile(prof_per_instance.instance, prof_per_instance.user_profile)
            points_for_player = prof_per_instance.total_points
            if points_for_player == 0:
                continue
            points+=points_for_player
        lb.name = affiliation.name
        if affiliation.slug.strip() != '':
            lb.absolute_url = affiliation.get_absolute_url()
        lb.points = points
        lb.date_last_built = datetime.datetime.now()
        lb.save()


@cached(60*60*24)
def leaderboard_for_game(game_id):
    # rank
    # screen_name
    # url to profile
    game = Instance.objects.get(pk=int(game_id))
    profiles_for_game = UserProfilePerInstance.objects.filter(instance=game).\
                                        exclude(user_profile__user__is_active=False,
                                            user_profile__user__is_superuser=True,
                                            user_profile__user__is_staff=True,
                                        )
    rebuild_player_leaderboard(profiles_for_game)
    variants = UserProfileVariantsForInstance.objects.get(instance=game)
    affiliations = variants.affiliation_variants.all()
    rebuild_affiliation_leaderboard(game, affiliations)





