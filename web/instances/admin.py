from django.contrib import admin

from nani.admin import TranslatableAdmin, TranslatableTabularInline

from web.instances.models import *

from web.accounts.models import UserProfileVariantsForInstance

class UserProfileVariantsForInstanceInline(admin.StackedInline):
    filter_horizontal = ('affiliation_variants', 'stake_variants',)
    model = UserProfileVariantsForInstance

class InstanceAdmin(TranslatableAdmin):
    list_display = ('title', 'start_date', 'city', 'is_disabled')
    list_filter = ('is_disabled',)
    filter_horizontal = ('curators', 'languages',)
    inlines = [
        UserProfileVariantsForInstanceInline,
    ]
class NotificationRequestAdmin(admin.ModelAdmin):
    list_display = ('email', 'instance')

class PointsAssignmentAdmin(admin.ModelAdmin):
    list_display = ('action', 'points', 'instance')

class AffiliationAdmin(admin.ModelAdmin):
	list_display = ('name',)

# Register to admin sites
admin.site.register(Instance, InstanceAdmin)
admin.site.register(Language)
admin.site.register(Affiliation, AffiliationAdmin)
admin.site.register(NotificationRequest, NotificationRequestAdmin)
#admin.site.register(PointsAssignmentAction)
admin.site.register(PointsAssignment, PointsAssignmentAdmin)
