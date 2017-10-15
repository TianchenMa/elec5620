from django.contrib import admin

from .models import *


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    fields = [
        'username',
        'password',
        'identity',
        'doctor'
    ]

    list_display = ['username', 'password', 'doctor', 'identity']


class RegisterCodeAdmin(admin.ModelAdmin):
    fields = [
        'code',
        'creator',
        'used',
    ]

    list_display = ['code', 'creator', 'used']


class HealthDataAdmin(admin.ModelAdmin):
    fields = [
        'creator',
        'sub_date'
    ]

    list_display = ['creator', 'sub_date']


class MessageAdmin(admin.ModelAdmin):
    fields = [
        'from_user',
        'to_user',
        'content',
        'viewed',
        'send_date'
    ]

    list_display = ['from_user', 'to_user', 'content', 'viewed', 'send_date']


class AnnouncementAdmin(admin.ModelAdmin):
    fields = [
        'publisher',
        'content',
        'send_date'
    ]

    list_display = ['publisher', 'content', 'send_date']


class AnnouncementReceiveAdmin(admin.ModelAdmin):
    fields = [
        'announcement',
        'enduser',
        'viewed'
    ]

    list_display = ['announcement', 'enduser', 'viewed']


class TaskAdmin(admin.ModelAdmin):
    fields = [
        'doctor',
        'user',
        'content',
        'send_date'
    ]

    list_display = ['doctor', 'user', 'content', 'send_date']


class ActivityAdmin(admin.ModelAdmin):
    fields = [
        'user',
        'title',
        'content',
        'activity_time'
    ]

    list_display = ['user', 'title', 'content', 'activity_time']


admin.site.register(User, UserAdmin)
admin.site.register(RegisterCode, RegisterCodeAdmin)
admin.site.register(HealthData, HealthDataAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(AnnouncementReceive, AnnouncementReceiveAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Activity, ActivityAdmin)
