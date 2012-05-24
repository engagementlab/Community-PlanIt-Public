import os
import xlwt
import time
from stream.models import Action
import StringIO
from random import randint
from datetime import datetime, date

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection

from web.accounts.models import UserProfilePerInstance, UserProfile
from web.answers.models import AnswerMultiChoice
from web.badges.models import BadgePerPlayer
from web.instances.models import Instance
from web.missions.models import Mission
from .models import Report, determine_path

import logging
log = logging.getLogger()


"""
BEHOLD! The Spec!

Reports:

-- activity report by user - this report should be organized by user name and include all demographic data, number of log-ins, flag placement, badges earned, number of challenges completed, number of challenges created, number of comments liked, number of comments replied to.

-- activity time by user - this report should include user name and demographic data and when they logged in.

-- record of challenge activity by user - this report should include user name and demographic data and their record of all challenge activity. This should include responses to challenges (if multiple choice) and comments.

-- mission report - organized by challenge; if multiple choice (summary of results); and all comments and replies.

all registration data, points, badges, and flag placements, should be included in all reports organized by user.
"""

#class ReportProxy(object):
#    def __init__(self, report):
#        self.__report = report
#    def __getattr__(self, name):
#        return getattr(self.__report, name)


def get_report_instance(report_label):
    """ find the report class for the named report """
    try:
        report_name = settings.CPI_REPORTS[report_label]
    except (KeyError, AttributeError):
        raise ImproperlyConfigured("settings.CPI_REPORTS is not configured correctly for %r" % report)

    # 'report_label' : ('app.module','ReportClass')
    # from app.module load ReportClass and instantiate
    report_module = __import__( report_name[0],{},{},[''])
    report_class = getattr(report_module,report_name[1] )
    return report_class()


class ReportData(object):

    def __init__(self, **kwargs):
        self.field_titles = kwargs.pop('field_titles')
        self.values_list = kwargs.pop('values_list')
        self.exec_time = kwargs.pop('exec_time')
        self.query_count = kwargs.pop('query_count')


class ReportHandler(object):

    def __init__(self, *args, **kwargs):
        self.game_id = kwargs.pop('game_id')

    def run_reports(self):

        for report_label in settings.CPI_REPORTS.keys():
            get_report_instance(report_label)

        if self.game_id is not None:
            games = Instance.objects.filter(pk=self.game_id)
        else:
            games = Instance.objects.current()

        for report_label in settings.CPI_REPORTS.keys():
            report_instance = get_report_instance(report_label)

            for game in games:
                data = report_instance.get_report_data(game)
                xls_report = XlsReport(data)
                output = xls_report.render_to_excel()

                title = "".join([game.slug, '-', report_label])
                report = Report.objects.create(
                        title=title,
                        instance=game,
                        db_queries=data.query_count,
                        exec_time=data.exec_time,
                )
                NOW = datetime.now()
                filename = "".join([NOW.strftime('%Y-%m-%d-%H-%M'), '-', title, '.xls'])
                location = os.path.join(settings.MEDIA_ROOT, determine_path(report, filename))
                new_dir = os.path.dirname(location)
                if not os.path.exists(new_dir):
                    os.mkdir(new_dir)

                report.file.save(filename, ContentFile(output.getvalue()), save=True)
                output.close()
                log.debug('done with report. %s, saved %s' % (filename, location))


class XlsReport(object):

    def __init__(self, data):
        #self.report_title = data.report_title
        self.values_list = data.values_list
        self.field_titles = data.field_titles

    def render_to_excel(self, save_to_file=True):

        wb = xlwt.Workbook(encoding='utf8')
        sheet = wb.add_sheet('untitled')

        default_style = xlwt.Style.default_style

        header_style =xlwt.XFStyle()
        header_background = xlwt.Pattern()
        header_background.pattern = xlwt.Pattern.SOLID_PATTERN
        header_background.pattern_fore_colour = 22

        header_font = xlwt.Font()
        header_font.name = 'Calibri'
        header_font.bold = True
        header_style.pattern = header_background


        datetime_style = xlwt.easyxf(num_format_str='dd/mm/yyyy hh:mm')
        date_style = xlwt.easyxf(num_format_str='dd/mm/yyyy')

        for col, val in enumerate(self.field_titles):
            sheet.write(0, col, val, style=header_style)

        for row, rowdata in enumerate(self.values_list, start=1):
            for col, val in enumerate(rowdata):
                if isinstance(val, datetime):
                    style = datetime_style
                elif isinstance(val, date):
                    style = date_style
                else:
                    style = default_style

                sheet.write(row, col, val, style=style)

        #if not save_to_file:
        #    return xls_to_response(wb, filename)

        output = StringIO.StringIO()
        wb.save(output)
        return output


class DemographicReport(object):
    """ -- activity report by user - 
        this report should be organized by user name and 
        - include 
            all demographic data, 
            number of log-ins, 
            flag placement, 
            badges earned, 
            number of challenges completed, 
            number of challenges created, 
            number of comments liked, 
            number of comments replied to.  """

    def __init__(self, *args, **kwargs):
        self.debug = settings.DEBUG

    def get_demographic_field_titles(self):
        return (
                'ID', 
                'first name',
                'last name',
                'email',
                'stake', 
                'affiliations', 
                'preferred language', 
                'picture', 
                'race', 
                'gender', 
                'education', 
                'income', 
                'rent/own', 
                'city/neighborhood', 
                'zip code', 
        )

    def get_demographic_details(self, prof_per_instance, profile, user):

        def get_stakes(profile):
            return profile.format_stakes

        def get_affiliations(profile):
            return ", ".join(profile.affils.values_list('name', flat=True))

        return (
            prof_per_instance.pk,
            user.first_name,
            user.last_name,
            profile.email,
            get_stakes(prof_per_instance),
            get_affiliations(prof_per_instance),
            prof_per_instance.preferred_language.name,
            "Yes" if profile.avatar else "No",
            profile.race.race if hasattr(profile, 'race') and profile.race is not None else "",
            profile.gender.gender if hasattr(profile, 'gender') and profile.gender is not None else "",
            profile.education.education if hasattr(profile, 'education') and profile.education is not None else "",
            profile.income.income if hasattr(profile, 'income') and profile.income is not None else "",
            profile.living.situation if hasattr(profile, 'living') and profile.living is not None else "",
            profile.city or "",
            profile.zip_code or "",
        )

    def user_profiles_per_instance_qs(self, game):
        qs = UserProfilePerInstance.objects.filter(
                                        instance=game).\
                                    exclude(
                                        user_profile__user__is_superuser=True,
                                        user_profile__user__is_staff=True,
        )
        if self.debug:
            qs = qs.filter(user_profile__user__pk=877)
        return qs

    def get_report_data(self, game):

        field_titles = self.get_demographic_field_titles() + (
                'number of log-ins',
                'total flags spent for game', 
                'total points for game', 
                'badges earned', 
                'challenge completed count',
                'challenges created count',
                'comments liked count',
                'comments replied to count',
        )

        t1 = time.time()
        values_list = []
        for prof_per_instance in self.user_profiles_per_instance_qs(game):

            profile =  prof_per_instance.user_profile
            user =  prof_per_instance.user_profile.user
            all_details = self.get_demographic_details(prof_per_instance, profile, user) + (
                    Action.objects.get_for_actor(user).filter(
                                                        verb='user_logged_in',
                                                        target_instance=game,
                        ).count(),
                    prof_per_instance.flags,
                    prof_per_instance.total_points,
                    ", ".join(BadgePerPlayer.objects.filter(user=user).values_list('badge__title', flat=True)),
                    Action.objects.get_for_actor(user).filter(
                                                        verb='activity_completed', 
                                                        target_instance=game
                        ).count(),
                    Action.objects.get_for_actor(user).filter(
                                                        verb='activity_player_submitted', 
                                                        target_instance=game
                        ).count(),
                    Action.objects.get_for_actor(user).filter(
                                                        verb='liked', 
                                                        target_comment__instance=game
                        ).count(),
                    Action.objects.get_for_actor(user).filter(
                                                        verb='commented', 
                                                        target_comment__instance=game
                        ).count(),
            )
            values_list.append(all_details)

        return ReportData(
                field_titles = field_titles,
                values_list = values_list,
                exec_time = time.time()-t1,
                query_count = len(connection.queries),
        )


class LoginActivityReport(DemographicReport):
    """
        -- activity time by user - 
        this report should include user name and demographic data and when they logged in.  """


    def get_report_data(self, game):

        field_titles = self.get_demographic_field_titles() + (
                #'number of log-ins',
                'login dates/times',
        )
        t1 = time.time()
        values_list = []
        for prof_per_instance in self.user_profiles_per_instance_qs(game):

            profile =  prof_per_instance.user_profile
            user =  prof_per_instance.user_profile.user

            demographic_details = self.get_demographic_details(prof_per_instance, profile, user)
            login_actions = Action.objects.get_for_actor(user).filter(
                                        verb='user_logged_in',
                                        target_instance=game,
                            )
            datetimes = login_actions.values_list('datetime', flat=True)

            for dt in datetimes:
                all_details =  demographic_details+ (
                        #login_actions.count(),
                        dt.strftime('%Y-%m-%d-%H-%M'),
                )
                values_list.append(all_details)

        return ReportData(
                field_titles = field_titles,
                values_list = values_list,
                exec_time = time.time()-t1,
                query_count = len(connection.queries),
        )

def fetch_replies(demographic_details, answer, comment):
    replies = []
    if comment.comments.all().count():
        for res in comment.comments.select_related().all():
            replies.append(
                demographic_details + (
                        res.pk,
                        answer.mission.title,
                        answer.name,
                        answer.type.type,
                        '-',
                        res.posted_date.strftime('%Y-%m-%d %H:%M'),
                        res.user.pk,
                        "response to %s" %(comment.pk),
                        res.message,
                        res.likes.all().count(),
                )
            )
            #fetch_replies(a, res)
    return replies

def _fetch_multichoice_replies(demographic_details, answer, comment, mission_title):
    replies = []
    for res in comment.comments.all():
        replies.append(
                demographic_details + (
                    res.pk,
                    mission_title,
                    "---",
                    'multichoice',
                    '-',
                    res.posted_date.strftime('%Y-%m-%d %H:%M'),
                    "response to %s" %(comment.pk),
                    res.message,
                    res.likes.all().count(),
                )
        )
        #_fetch_multichoice_replies(a, res, mission_title=mission_title)
    return replies

def update_list(values_list, demographic_details=(), user=None, activity=None, answers=None):

    if answers is None:
        return
    answers = answers.select_related('comments')
    if user is not None:
        answers = answers.filter(answerUser=user)
    for answ in answers:
        for c in answ.comments.select_related('user', 'selected', 'likes').all():
            if activity.type.type == 'single_response':
                answer_value = answ.selected.value
            elif activity.type.type == 'map':
                if hasattr(answ, 'map'):
                    answer_value = ", ".join(map(lambda c: str(c), answ.map.coordinates))
            else:
                answer_value = ''

            values_list.append(
                    demographic_details +
                    (
                        c.pk, 
                        activity.mission.title,
                        activity.name, 
                        activity.type.type, 
                        activity.question,
                        c.posted_date.strftime('%Y-%m-%d %H:%M'),
                        answer_value,
                        c.message, 
                        c.likes.all().count(),
                    )
            )
            if c.comments.all().count():
                values_list.extend(fetch_replies(demographic_details, activity, c))


class ChallengeActivityReport(DemographicReport):
    """
        -- record of challenge activity by user 
        - this report should include user name and demographic data and their record of all challenge activity. 
        This should include responses to challenges (if multiple choice) and comments. """

    def get_report_data(self, game):

        field_titles = self.get_demographic_field_titles() + (
                            'comment id', 
                            'mission', 
                            'activity title', 
                            'challenge type', 
                            'original question',
                            'timestamp',
                            'response code',
                            'comment', 
                            'likes'
        )
        #all_actions = [Action.objects.get_for_actor(
        #                            p.prof_per_instance.user_profile.user).\
        #                                filter(
        #                                    verb='activity_completed'
        #                                    target_instance=game, 
        #                                ) for p in qs]
        #for prof_per_instance, actions in \
        #        zip(qs, all_actions):

        values_list = []
        t1 = time.time()
        for prof_per_instance in self.user_profiles_per_instance_qs(game):
            profile =  prof_per_instance.user_profile
            user =  prof_per_instance.user_profile.user
            demographic_details = self.get_demographic_details(prof_per_instance, profile, user)
            values_list.append(demographic_details)

            actions = Action.objects.get_for_actor(user).filter(target_instance=game, verb='activity_completed')
            for action in actions:
                obj = action.action_object
                if obj.__class__.__name__ ==  'PlayerEmpathyActivity':
                    update_list(values_list, demographic_details, user, obj, getattr(obj, 'empathy_answers'))
                if obj.__class__.__name__ ==  'PlayerActivity':
                    if obj.type.type == 'open_ended':
                        update_list(values_list, demographic_details, user, obj, getattr(obj, 'openended_answers'))
                    if obj.type.type == 'single_response':
                        update_list(values_list, demographic_details, user, obj, getattr(obj, 'singleresponse_answers'))
                    if obj.type.type == 'multi_response':
                        answers = AnswerMultiChoice.objects.select_related().filter(option__activity=obj)
                        for answer in answers:
                            for c in answer.comments.filter(user=user):
                                mission_title = answer.option.mission.title
                                values_list.append(
                                        demographic_details  + (
                                            c.pk, 
                                            mission_title,
                                            obj.name,
                                            'multichoice',
                                            obj.question,
                                            c.posted_date.strftime('%Y-%m-%d %H:%M'),
                                            answer.option.value,
                                            c.message, 
                                            c.likes.all().count(),
                                        )
                                )
                                if c.comments.all().count():
                                    values_list.extend(_fetch_multichoice_replies(demographic_details, answer, c, mission_title))
                if obj.__class__.__name__ == 'PlayerMapActivity':
                    update_list(values_list, demographic_details, user, obj, getattr(obj, 'map_answers'))

        return ReportData(
                field_titles = field_titles,
                values_list = values_list,
                exec_time = time.time()-t1,
                query_count = len(connection.queries),
        )



class MissionReport():

    """-- mission report - 
        organized by challenge; 
        if multiple choice (summary of results); 
        and all comments and replies."""

    def __init__(self, *args, **kwargs):
        self.debug = settings.DEBUG

    def get_report_data(self, game):
        field_titles = (
                            'mission', 
                            'comment id', 
                            'activity title', 
                            'activity type', 
                            'original question',
                            'timestamp',
                            'user',
                            'response code',
                            'comment', 
                            'likes'
        )
        t1 = time.time()
        values_list = []
        if self.debug:
            qs = Mission.objects.filter(slug='share-your-detroit')
        else:
            qs = Mission.objects.filter(instance=game)
        for mission in qs:
            challenges = mission.get_activities(include_player_submitted=True)
            print "mission: %s, %s challenges" %(mission.slug, len(challenges))
            for obj in challenges:
                if obj.__class__.__name__ ==  'PlayerEmpathyActivity':
                    update_list(values_list, user=None, activity=obj, answers=getattr(obj, 'empathy_answers'))
                if obj.__class__.__name__ ==  'PlayerActivity':
                    if obj.type.type == 'open_ended':
                        update_list(values_list, user=None, activity=obj, answers=getattr(obj, 'openended_answers'))
                    if obj.type.type == 'single_response':
                        update_list(values_list, user=None, activity=obj, answers=getattr(obj, 'singleresponse_answers'))
                    if obj.type.type == 'multi_response':
                        answers = AnswerMultiChoice.objects.select_related().filter(option__activity=obj)
                        for answer in answers:
                            for c in answer.comments.all():
                                #mission_title = answer.option.mission.title
                                mission_title = mission.title
                                values_list.append(
                                        (
                                            mission_title,
                                            c.pk, 
                                            obj.name,
                                            'multichoice',
                                            obj.question,
                                            c.posted_date.strftime('%Y-%m-%d %H:%M'),
                                            c.user.get_profile().screen_name,
                                            answer.option.value,
                                            c.message, 
                                            c.likes.all().count(),
                                        )
                                )
                                if c.comments.all().count():
                                    values_list.extend(_fetch_multichoice_replies(answer, c, mission_title))
                if obj.__class__.__name__ == 'PlayerMapActivity':
                    update_list(obj, getattr(obj, 'map_answers'))

        return ReportData(
                field_titles = field_titles,
                values_list = values_list,
                exec_time = time.time()-t1,
                query_count = len(connection.queries),
        )
