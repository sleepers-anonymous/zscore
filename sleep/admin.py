from django.contrib import admin
from sleep.models import *

class AllnighterAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'comments')
    list_filter = ('user', 'date')
    ordering = ('user',)
    search_fields = ['user__username']

class PartialSleepAdmin(admin.ModelAdmin):
    list_display = ('user','start_local_time')
    search_fields = ('user__username',)
    list_filter = ('user', 'start_time')

class SleepAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user']}),
        ('Date/Time info', {'fields' : ['date', 'start_time', 'end_time','timezone']}),
        ('Other', {'fields' : ['comments','quality','sleepcycles']})
         ]
    list_display = ('user', 'start_local_time', 'end_local_time','comments')
    list_filter = ('user','end_time')
    ordering = ('user','end_time',)
    search_fields = ['user__username','comments']

class SleeperProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields' : ['user','timezone','metrics']}),
        ('Friends', {'fields' : ['friends','follows']}),
        ('Privacy Settings', {'fields' : [ 'privacy', 'privacyLoggedIn', 'privacyFriends', 'autoAcceptGroups']}),
        ('Customizations', {'fields' : ['punchInDelay','useGravatar','moreMetrics', 'use12HourTime', 'mobile']}),
        ('Ideal Settings', {'fields' : ['idealSleep','idealSleepTimeWeekday', 'idealSleepTimeWeekend','idealWakeupWeekday','idealWakeupWeekend']}),
        ('Email Settings', {'fields' : ['emailreminders','emailTime','emailActivated']})
        ]
    list_display = ['user']
    ordering = ('user',)
    filter_horizontal = ('friends','follows','metrics')
    search_fields = ['user__username']
                               

class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('requestor', 'requestee', 'accepted')
    search_fields = ['requestor__user__username','requestee__username']
    list_filter = ('requestor__user','requestee')

class MembershipInline(admin.TabularInline):
    model = Membership

class SleeperGroupAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'privacy', 'defunctMembers']
    list_display = ('name', 'description','privacy')
    inlines = [MembershipInline]
    search_fields = ['name','description']
    ordering = ('name',)

class GroupInviteAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'accepted')
    ordering = ('accepted','group','user')
    search_fields = ['user__username','group__name']

class MembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'role')
    ordering = ('group','user','role')
    search_fields = ['group__name', 'user__username']
    list_filter = ('group', 'user')

class GroupRequestAdmin(admin.ModelAdmin):
    list_display = ('user','group', 'accepted')
    search_fields = ('user__username','group__name')

class MetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_style', 'priority', 'show_by_default')
    ordering = ('-priority',)
    search_fields = ('name',)

admin.site.register(Allnighter, AllnighterAdmin)
admin.site.register(PartialSleep, PartialSleepAdmin)
admin.site.register(Sleep, SleepAdmin)
admin.site.register(SleeperProfile, SleeperProfileAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)
admin.site.register(SleeperGroup, SleeperGroupAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(GroupInvite, GroupInviteAdmin)
admin.site.register(GroupRequest, GroupRequestAdmin)
admin.site.register(Metric,MetricAdmin)
